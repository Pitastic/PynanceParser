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
        parses = self._load_parsers()

        for d in input_data:
            for name, regex in parses.items():
                re_match = regex.search(d['text_tx'])
                if re_match:
                    d['parsed'][name] = re_match.group(1)

        return input_data

    def tag(self, iban,
            rule_name: str = None, rule_category: str = 'None', rule_subcategory: str = None,
            rule_tags: list[str] = None, rule_regex: str = None, rule_parsed_keys: list = (),
            rule_parsed_vals: list = (), prio: int = 1, prio_set: int = None,
            dry_run: bool = False) -> dict:
        """
        Kategorisiert die Kontoumsätze und aktualisiert die Daten in der Instanz.

        Args:
            data (dict): Dictionary mit den Parametern für das Tagging:
                iban            Name der Collection
                rule_name:      UUID der anzuwendenden Taggingregel.
                                Reserviertes Keyword 'ai' führt nur das AI Tagging aus.
                                Default: Es werden alle Regeln des Benutzers ohne das
                                AI Tagging angewendet.
                rule_category:  Name der zu setzenden Primärkategory.
                                Default: sonstiges
                rule_subcategory: Name der zu setzenden Sekundärkategorie.
                                Default: keine Sekundärkategorie
                rule_tags:      Name der zu setzenden Sekundärkategory.
                                Default: kein Tag
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
        prio_set = prio if prio_set is None else prio_set

        # RegEx Tagging (specific rule or all)
        if rule_regex is not None or rule_parsed_keys:

            # Custom Rule
            rule = {
                'category': rule_category,
                'subcategory': rule_subcategory,
                'tags': rule_tags,
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
            return self.tag_ai(dry_run=dry_run)

        # Benutzer Regeln laden
        rules = self._load_ruleset(rule_name)
        logging.debug(f"Regeln geladen: {rules}")
        if not rules:
            if rule_name:
                raise KeyError((f'Eine Regel mit dem Namen {rule_name} '
                                'konnte für den User nicht gefunden werden.'))

            raise ValueError('Es existieren noch keine Regeln für den Benutzer')

        # Benutzer Regeln ignoriert alle autpomatischen Tags,
        # setzt aber wieder nur seine eigene Prio.
        if rule_name is not None:
            prio_set = rules[rule_name].get('prioriry', prio)
            prio = 99

        # Benutzer Regeln anwenden (Tag Loop + Category + AI)
        # (kein Loop bei dry_run, da keine DB Updates gemacht werden)
        r = {'tagged': True, 'entries': [True] }  # Dummy Start
        result_rx = {'tagged': 0, 'entries': []}
        while r.get('tagged') and not dry_run:
            # Loop RegEx Tagging (Tags-only)
            r = self.tag_regex(rules, iban, prio=prio, prio_set=prio_set,
                                       dry_run=dry_run, tag_only=True)
            result_rx['tagged'] += r.get('tagged')
            result_rx['entries'] += r.get('entries')

        # Final RegEx Tagging (Categories)
        r = self.tag_regex(rules, iban, prio=prio, prio_set=prio_set,
                           dry_run=dry_run, tag_only=False)
        result_rx['tagged'] += r.get('tagged')
        result_rx['entries'] += r.get('entries')
        result_rx['entries'] = list(set(result_rx['entries']))

        # Guess empty TX
        result_ai = self.tag_ai(iban, dry_run=dry_run)

        return {**result_rx, **result_ai}

    def tag_regex(self, ruleset: dict, collection: str=None, prio: int=1,
                  prio_set: int=1, dry_run: bool=False, tag_only: bool=False) -> dict:
        """
        Automatische Kategorisierung anhand von hinterlegten RegExes je Kategorie.

        Args:
            ruleset:         Named rules to be applied on users transactions
            collection:      Name der Collection, in der gefiltert werden soll.
                             Default: IBAN aus der Config.
            prio:            Value of priority for this tagging run
                             in comparison with already tagged transactions (higher = important)
                             This value will be set as the new priority in DB
            prio_set:        Compare with 'prio' but set this value instead.
                             Default: prio.
            dry_run:         Switch to show, which TX would be updated. Do not update.
            tag_only:        Add to only the tags to the transactions.
        Returns:
            dict:
            - tagged (int): Summe aller erfolgreichen Taggings (0 bei dry_run)
            - entries (list): UUIDs die selektiert wurden (auch bei dry_run)
        """
        result = { 'tagged': 0, 'entries': [] }

        # Allgemeine Startfilter für die Condition
        query_args = self._form_tag_query(prio, collection)

        for rule_name, rule in ruleset.items():
            logging.info(f"RegEx Tagging mit Rule {rule_name}...")

            # Updated Category
            new_category = {
                'tags': rule.get('tags')
            }
            if not tag_only:
                new_category['category'] = rule.get('category')
                new_category['subcategory'] = rule.get('subcategory')
                new_category['prio'] = prio_set

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
            multi = 'AND'
            if rule.get('parsed') is not None:
                parsed_condition = rule.get('parsed')
                multi = parsed_condition.get('multi', 'AND')

                for key, val in parsed_condition.get('query', {}).items():
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
                multi=multi
            )

            # Nothing to update
            if not matched:
                logging.info(f"Rule '{rule_name}' trifft nichts.")
                continue

            # Create updated Data and get UUIDs
            for row in matched:

                # UUIDs
                uuid = row.get('uuid')
                if uuid is None:
                    raise ValueError(f'The following data in the DB has no UUID ! - {row}')

                result['entries'].append(uuid)

                # Update Request / Dry run
                if dry_run:
                    continue

                # Do not duplicate Tags
                existing_tags = row.get('tags', [])
                new_tags = [t for t in new_category.get('tags', []) if t not in existing_tags]
                new_category['tags'] = new_tags

                if not new_category.get('tags'):
                    if tag_only:
                        # Skip this loop
                        logging.info((f"Rule '{rule_name}' hat keine neuen Tags "
                                        f"für {uuid} - skipping (tag only)..."))
                        continue

                    # Do not update tags (but everything else)
                    del new_category['tags']
                    logging.info((f"Rule '{rule_name}' hat keine neuen Tags "
                                    f"für {uuid} - do not update tags..."))

                query = {'key': 'uuid', 'value': uuid}
                updated = self.db_handler.update(data=new_category, condition=query)

                # soft Exception Handling
                if not updated:
                    logging.error((f"Bei Rule '{rule_name}' konnte der Eintrag "
                                    f"'{uuid}' nicht geupdated werden - skipping..."))
                    continue

                result['tagged'] += updated.get('updated')

        return result

    def tag_ai(self, collection: str=None, dry_run: bool=False) -> dict:
        """
        Automatisches Tagging mit AI.

        Args:
            collection:     Name der Collection, in die Werte eingefügt werden sollen.
                            Default: IBAN aus der Config.
            dry_run         Switch to show, which TX would be updated. Do not update.
        Returns:
            dict:
            - guessed (int): Summe aller erfolgreichen Taggings (0 bei dry_run)
            - ai (dict):
                - entries (list): UUIDs die selektiert wurden (auch bei dry_run)
        """
        logging.info("Tagging with AI....")

        # Allgemeine Startfilter für die Condition
        query_args = self._form_tag_query(collection=collection, ai=True)
        matched = self.db_handler.select(**query_args)

        tagged = 0
        count = 0
        entries = []

        # Untersuche zeilenweise mit AI
        for row in matched:
            c, entry = self._ai_tagging(row)
            count += c
            entries.append(entry)

        # Update Request
        if count and not dry_run:

            for entry in entries:

                uuid = entry.get('uuid')
                query = {'key': 'uuid', 'value': uuid}

                # Updated Category
                new_category = {
                    'guess': entry.get('guess')
                }
                updated = self.db_handler.update(data=new_category, condition=query)
                updated = updated.get('updated')

                # soft Exception Handling
                if not updated:
                    logging.error(("Beim AI Tagging konnte der Eintrag "
                                   f"'{uuid}' nicht geupdated werden - skipping..."))
                    continue

                tagged += updated

        result = {
            'guessed': tagged,
            'ai': {
                'entries': [e.get('uuid') for e in entries],
            }
        }

        logging.info("Tagging with AI....DONE")
        return result

    def _form_tag_query(self, prio: int=1, collection: str=None, ai=False) -> dict:
        """
        Erstellt die Standardabfrage-Filter für den Ausgangsdatensatz eines Taggings.

        Args:
            prio, int: Filter more important tags
            collection, str: Collection to select from
            ai, bool: True if AI Tagging
        Return:
            dict: Query Dict for db_handler.select()
        """
        if not ai:
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
        else:
            # Startfilter für unkategoriesierte Transaktionen
            query_args = {
                'condition': [
                    {
                        'key': 'category',
                        'value': None,
                        'compare': '=='
                    }, {
                        'key': 'tags',
                        'value': None,
                        'compare': '=='
                    }
                ],
                'multi': 'OR',
                'collection': collection
            }

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
        primary_categories = [
            'AI_Pri_1', 'AI_Pri_2', 'AI_Pri_3', 'AI_Pri_4',
            'AI_Pri_5', 'AI_Pri_6', None, None, None, None,
            None, None, None, None, None, None, None
        ]
        possible_tags = [
            'AI_Sec_1', 'AI_Sec_2', 'AI_Sec_3', 'AI_Sec_4',
            'AI_Sec_5', 'AI_Sec_6', None, None, None, None,
            None, None, None, None, None, None, None
        ]

        c = 0
        guess = {}
        category = transaction.get('category')
        if category is None:
            # Guess Primary Tag
            found_category = random.choice(primary_categories)
            if found_category is not None:
                category = found_category
                guess['category'] = category
                c += 1


        if category is not None and transaction.get('tags') is None:
            # Guess Secondary Tag
            found_category = random.choice(possible_tags)
            if found_category is not None:
                guess['tags'] = found_category
                c += 1

        # Store result and return
        transaction['guess'] = guess
        return c, transaction

    def _load_parsers(self) -> dict:
        """
        Parser ermöglichen das Extrahieren von Kerninformationen aus dem Buchungstext.
        Die Ergebnisse können für Entscheidung beim Tagging genutzt werden.
        Der Key wird als Bezeichner für das Ergebnis verwendet.
        Jeder RegEx muss genau eine Gruppe matchen.
        """
        raw_parser = self.db_handler.filter_metadata(
            {"key": "metatype", "value": "parser"}
        )
        parsers = {}
        for p in raw_parser:
            parsers[p['name']] = re.compile(p.get('regex'))

        return parsers

    def _load_ruleset(self, rule_name=None) -> dict:
        """
        Load Rules from the Settings of for the requesting User.

        Args:
            rule_name (str, optional): Lädt die Regel mit diesem Namen.
                                       Default: Es werden alle Regeln geladen.
        Returns:
            dict: Verzeichnis nach Namen der Filterregeln
        """
        if rule_name:
            # Bestimmte Regel laden
            raw_rule = self.db_handler.filter_metadata(
                [
                    {"key": "metatype", "value": "rule"},
                    {"key": "name", "value": rule_name}
                ],
                multi='AND'
            )

            if not raw_rule:
                raise KeyError(f'Eine Regel mit dem Namen {rule_name} '
                               'konnte für den User nicht gefunden werden.')

            rule = raw_rule[0]
            regex = rule.get('regex')
            if regex:
                rule['regex'] = re.compile(regex)

            return {rule_name: rule}

        # Alle Regeln laden
        raw_rules = self.db_handler.filter_metadata(
            {"key": "metatype", "value": "rule"}
        )
        rules = {}
        for r in raw_rules:
            regex = r.get('regex')

            if regex:
                r['regex'] = re.compile(regex)

            rules[r.get('name')] = r

        return rules
