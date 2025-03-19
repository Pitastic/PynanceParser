#!/usr/bin/python3 # pylint: disable=invalid-name
"""Ausgelagerter Handler für die Umsatzuntersuchung."""

import copy
import random
import re
import logging


class Tagger():
    """Handler für die Untersuchung und Markierung von Umsätzen."""

    def __init__(self, db_handler):
        self.db_handler = db_handler

    def parse(self, input_data):
        """
        Untersucht die Daten eines Standard-Objekts (hauptsächlich den Text)
        und identifiziert spezielle Angaben anhand von Mustern.
        Alle Treffer werden unter dem Schlüssel 'parsed' jedem Eintrag hinzugefügt.

        Args:
            input_data, list(dict): Liste mit Transaktionen,
                                    auf die das Parsing angewendet werden soll.

        Returns:
            list(dict): Updated input_data
        """
        # RegExes
        # Der Key wird als Bezeichner für das Ergebnis verwendet.
        # Jeder RegEx muss genau eine Gruppe matchen.
        parse_regexes = {
            'Mandatsreferenz': re.compile(r"Mandatsref\:\s?([A-z0-9]*)"),
            'Gläubiger-ID': re.compile(r"([A-Z]{2}[0-9]{2}[0-9A-Z]{3}[0-9]{11})"),
            'Gläubiger-ID-2': re.compile(r"([A-Z]{2}[0-9]{2}[0-9A-Z]{3}[0-9]{19})"),
        }

        for d in input_data:
            for name, regex in parse_regexes.items():
                re_match = regex.search(d['text_tx'])
                if re_match:
                    d['parsed'][name] = re_match.group(1)

        return input_data

    def tag(self,
            rule_name: str = None, rule_primary: str = None, rule_secondary: str = None,
            rule_regex: str = None, rule_parsed_keys: list = (), rule_parsed_vals: list = (),
            prio: int = 1, prio_set: int = None, dry_run: bool = False) -> dict:
        """
        Kategorisiert die Kontoumsätze und aktualisiert die Daten in der Instanz.

        Args:
            data (dict): Dictionary mit den Parametern für das Tagging:
                rule_name:      Name der anzuwendenden Taggingregel.
                                Reserviertes Keyword 'ai' führt nur das AI Tagging aus.
                                Default: Es werden alle Regeln des Benutzers ohne das
                                AI Tagging angewendet.
                rule_primary:   Name der zu setzenden Primärkategory.
                                Default: Standardname
                rule_secondary  Name der zu setzenden Sekundärkategory.
                                Default: Standardname
                rule_regex:     Regulärer Ausdrück für die Suche im Transaktionstext.
                                Default: Wildcard
                rule_parsed_keys:   Liste mit Keys zur Prüfung in geparsten Daten.
                rule_parsed_vals:   Liste mit Values zur Prüfung in geparsten Daten.
                prio:           Value of priority for this tagging run
                                in comparison with already tagged transactions (higher = important)
                                This value will be set as the new priority in DB.
                                Default: 1
                prio_set:       Compare with 'prio' but set this value instead.
                                Default: prio.
                dry_run:        Switch to show, which TX would be updated. Do not update.
                                Default: False
        Returns:
            - tagged (int): Summe aller erfolgreichen Taggings (0 bei dry_run)
            - Regelname (dict):
                - tagged (int): Anzahl der getaggten Datensätze (0 bei dry_run)
                - entries (list): UUIDs die selektiert wurden (auch bei dry_run)
        """
        # RegEx Tagging (specific rule or all)
        if rule_regex is not None or rule_parsed_keys:

            # Custom Rule
            rule = {
                'primary': rule_primary,
                'secondary': rule_secondary,
                'regex': rule_regex
            }

            if len(rule_parsed_keys) != len(rule_parsed_vals):
                msg = 'Parse-Keys and -Vals were submitted in unequal length !'
                logging.error(msg)
                return {'error': msg}, 400

            for i, parse_key in enumerate(rule_parsed_keys):
                rule['parsed'][parse_key] = rule_parsed_vals[i]

            if rule_name is None:
                rule_name = 'Custom Rule'

            rules = {rule_name: rule}

            return self.tag_regex(rules, prio=prio,
                                  prio_set=prio_set, dry_run=dry_run)

        if rule_name == 'ai':
            # AI only
            return self.tag_ai(rules, prio=prio,
                               prio_set=prio_set, dry_run=dry_run)

        # Benutzer Regeln laden
        rules = self._load_ruleset(rule_name)
        logging.debug(f"Regeln geladen: {rules}")
        if not rules:
            if rule_name:
                raise KeyError((f'Eine Regel mit dem Namen {rule_name} '
                                'konnte für den User nicht gefunden werden.'))

            raise ValueError('Es existieren noch keine Regeln für den Benutzer')

        # Benutzer Regeln anwenden
        return self.tag_regex(rules, prio=prio, prio_set=prio_set, dry_run=dry_run)


    def tag_regex(self, ruleset: dict, collection: str=None, prio: int=1,
                  prio_set: int=None, dry_run: bool=False) -> dict:
        """
        Automatische Kategorisierung anhand von hinterlegten RegExes je Kategorie.

        Args:
            ruleset:         Named rules to be applied on users transactions
            collection:      Name der Collection, in die Werte eingefügt werden sollen.
                             Default: IBAN aus der Config.
            prio:            Value of priority for this tagging run
                             in comparison with already tagged transactions (higher = important)
                             This value will be set as the new priority in DB
            prio_set:        Compare with 'prio' but set this value instead.
                             Default: prio.
            dry_run:         Switch to show, which TX would be updated. Do not update.
        Returns:
            dict:
            - tagged (int): Summe aller erfolgreichen Taggings (0 bei dry_run)
            - Regelname (dict):
                - tagged (int): Anzahl der getaggten Datensätze (0 bei dry_run)
                - entries (list): UUIDs die selektiert wurden (auch bei dry_run)
        """
        result = { 'tagged': 0 }
        prio_set = prio if prio_set is None else prio_set

        # Allgemeine Startfilter für die Condition
        query_args = self._form_tag_query(prio, collection)

        for rule_name, rule in ruleset.items():
            logging.info(f"RegEx Tagging mit Rule {rule_name}...")

            # Updated Category
            new_category = {
                'prio': prio_set,
                'primary_tag': rule.get('primary', 'sonstiges'),
                'secondary_tag': rule.get('secondary', 'sonstiges'),
            }

            # Ergebnisspeicher
            rule_result = {
                'tagged': 0,
                'entries': []
            }

            # Spezielle Conditions einer Rule
            rule_args = copy.deepcopy(query_args)

            # -- Add Text RegExes
            if rule.get('regex') is not None:
                rule_args['condition'].append({
                    'key': 'text_tx',
                    'value': rule.get('regex'),
                    'compare': 'regex'
                })

            # -- Add Parsed Values
            if rule.get('parsed') is not None:
                parsed_condition = rule.get('parsed')
                for key, val in parsed_condition.items():
                    rule_args['condition'].append({
                        'key': {'parsed': key},
                        'value': val,
                        'compare': 'regex'
                    })

            # Dry Run first (store results)
            logging.debug(f"Query Args: {rule_args.get('condition')}")
            matched = self.db_handler.select(
                collection=rule_args.get('collection'),
                condition=rule_args.get('condition'),
                multi=rule_args.get('multi')
            )

            # Nothing to update
            if not matched:
                logging.info(f"Rule '{rule_name}' trifft nichts.")
                result[rule_name] = rule_result
                continue

            # Create updated Data and get UUIDs
            for row in matched:

                # UUIDs
                uuid = row.get('uuid')
                if uuid is None:
                    raise ValueError(f'The following data in the DB has no UUID ! - {row}')
                rule_result['entries'].append(uuid)

                # Update Request
                if dry_run is False:

                    query = {'key': 'uuid', 'value': uuid}
                    updated = self.db_handler.update(data=new_category, condition=query)

                    # soft Exception Handling
                    if not updated:
                        logging.error((f"Bei Rule '{rule_name}' konnte der Eintrag "
                                       f"'{uuid}' nicht geupdated werden - skipping..."))
                        continue
                    rule_result['tagged'] += updated.get('updated')

            # Store Result for this Rule
            result['tagged'] += rule_result.get('tagged')
            result[rule_name] = rule_result
        return result


    def tag_ai(self, collection: str=None, prio: int=1, prio_set: int=None,
               dry_run: bool=False) -> dict:
        """
        Automatisches Tagging mit AI.

        Args:
            collection:     Name der Collection, in die Werte eingefügt werden sollen.
                            Default: IBAN aus der Config.
            prio:           Value of priority for this tagging run
                            in comparison with already tagged transactions (higher = important)
                            This value will be set as the new priority in DB
            prio_set        Compare with priority but set this value instead.
                            Default: prio.
            dry_run         Switch to show, which TX would be updated. Do not update.
        Returns:
            dict:
            - tagged (int): Summe aller erfolgreichen Taggings (0 bei dry_run)
            - ai (dict):
                - tagged (int): Anzahl der getaggten Datensätze (0 bei dry_run)
                - entries (list): UUIDs die selektiert wurden (auch bei dry_run)
        """
        logging.info("Tagging with AI....")

        # Allgemeine Startfilter für die Condition
        query_args = self._form_tag_query(prio, collection=collection)
        matched = self.db_handler.select(**query_args)

        tagged = 0
        count = 0
        entries = []

        # Untersuche zeilenweise mit AI
        for row in matched:
            c, entry = self._ai_tagging(row)
            count += c
            entries += entry.get('uuid')

        # Update Request
        if count and not dry_run:

            for entry in entries:

                if entry.get('primmary') is None:
                    continue

                uuid = entry.get('uuid')
                query = {'key': 'uuid', 'value': uuid}
                new_prio = prio if prio_set is None else prio_set

                # Updated Category
                new_category = {
                    'prio': new_prio,
                    'primary_tag': entry.get('primary'),
                    'secondary_tag': entry.get('secondary', 'sonstiges'),
                }
                updated = self.db_handler.update(data=new_category, condition=query)

                # soft Exception Handling
                if not updated:
                    logging.error(("Beim AI Tagging konnte der Eintrag "
                                   f"'{uuid}' nicht geupdated werden - skipping..."))
                    continue

                tagged += updated

        result = {
            'tagged': tagged,
            'ai': {
                'tagged': tagged,
                'entries': entries
            }
        }

        logging.info("Tagging with AI....DONE")
        return result

    def _form_tag_query(self, prio: int, collection: str=None) -> dict:
        """
        Erstellt die Standardabfrage-Filter für den Ausgangsdatensatz eines Taggings.

        Args:
            prio, int: Filter more important tags
            collection, str: Collection to select from
        Return:
            dict: Query Dict for db_handler.select()
        """
        # Allgemeine Startfilter für die Condition
        query_args = {
            'condition': [{
                'key': 'prio',
                'value': prio,
                'compare': '<'
            }],
            'multi': 'AND',
            'collection': collection
        }
        if collection is not None:
            query_args['collection'] = collection

        return query_args

    def _ai_tagging(self, transaction):
        """
        Automatische Kategorisierung anhand eines Neuronalen Netzes.
        Trainingsdaten sind die zum Zeitpunkt des taggings bereits
        getaggten Datensätze aus der Datenbank.

        Args:
            transaction, dict: Transaktion, die untersucht werden soll.
        Returns:
            tuple(int, dict): Trefferanzahl (0|1), Aktualisierte Transaktion
        """
        #TODO: Fake Methode
        list_of_categories = [
            'Vergnügen', 'Versicherung', 'KFZ', 'Kredite',
            'Haushalt und Lebensmittel', 'Anschaffung',
        ]
        list_of_categories += 20 * None

        found_category = random.choice(list_of_categories)
        c = 0

        if found_category is not None:
            transaction['primary_tag'] = found_category
            transaction['secondary_tag'] = None
            c = 1

        return c, transaction

    def _load_ruleset(self, rule_name=None, namespace='both'):
        """
        Load Rules from the Settings of for the requesting User.

        Args:
            rule_name (str, optional): Lädt die Regel mit diesem Namen.
                                       Default: Es werden alle Regeln geladen.
            namespace (str, system|user|both): Unterscheidung aus weclhem Set Regeln
                                               geladen oder gesucht werden soll.
                                               - system: nur allgemeine Regeln
                                               - user: nur private Regeln
                                               - both (default): alle Regeln
        Returns:
            list(dict): Liste von Filterregeln
        """
        #TODO: Fake Funktion
        system_rules = {
            'Supermarkets': {
                'primary': 'Lebenserhaltungskosten',
                'secondary': 'Lebensmittel',
                'regex': r"(EDEKA|Wucherpfennig|Penny|Aldi|Kaufland|netto)",
            },
        }
        user_rules = {
            'City Tax': {
                'primary': 'Haus und Grund',
                'secondary': 'Stadtabgaben',
                'parsed': {
                    'Gläubiger-ID': r'DE7000100000077777'
                },
            }
        }

        if rule_name:

            # Bestimmte Regel laden
            if namespace in ['system', 'both']:
                # Allgemein
                rule = system_rules.get(rule_name)
            if namespace == 'both':
                # oder speziell (falls vorhanden)
                rule = user_rules.get(rule_name, rule)
            if namespace == 'user':
                # Nur User
                rule = user_rules.get(rule_name)

            return {rule_name: rule}

        # Alle Regeln einzelner namespaces
        if namespace == 'system':
            return system_rules
        if namespace == 'user':
            return user_rules

        # Alle Regeln aller namespaces
        system_rules.update(user_rules)
        return system_rules
