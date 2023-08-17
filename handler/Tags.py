#!/usr/bin/python3 # pylint: disable=invalid-name
"""Ausgelagerter Handler für die Umsatzuntersuchung."""

import copy
import random
import re
import cherrypy


class Tagger():
    """Handler für die Untersuchung und Markierung von Umsätzen."""

    def __init__(self):
        pass

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

    def tag_regex(self, db_handler, ruleset, collection=None, prio=1, dry_run=False, prio_set=None):
        """
        Automatische Kategorisierung anhand von hinterlegten RegExes je Kategorie.

        Args:
            db_handler, object: Instance for DB interaction (read/write)
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                        Default: IBAN aus der Config.
            ruleset, dict(dict): Named rules to be applied on users transactions
            prio, int(1): Value of priority for this tagging run
                          in comparison with already tagged transactions
                          This value will be set as the new priority in DB
            prio_set, int(None): Compare with priority but set this value instead.
                                 Default: prio.
            dry_run, bool(False): Switch to show, which TX would be updated. Do not update.
        Returns:
            dict:
            - tagged: int, Summe aller erfolgreichen Taggings (0 bei dry_run)
            - name: dict(Regelname)
                - tagged: int, Anzahl der getaggten Datensätze (0 bei dry_run)
                - entries: list, UUIDs die selektiert wurden (auch bei dry_run)
        """
        result = { 'tagged': 0 }
        prio = prio if prio_set is None else prio_set

        # Allgemeine Startfilter für die Condition
        query_args = {
            'condition': [{
                'key': 'priority',
                'value': prio,
                'compare': '<'
            }],
            'multi': 'AND'
        }
        if collection is not None:
            query_args['collection'] = collection


        for rule_name, rule in ruleset.items():
            cherrypy.log(f"RegEx Tagging mit Rule {rule_name}...")

            # Updated Category
            new_category = {
                'priority': prio,
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
                    'key': 'tx_text',
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
            matched = db_handler.select(collection=rule_args.get('collection'),
                                        condition=rule_args.get('condition'),
                                        multi=rule_args.get('multi'))

            # Nothing to update
            if not matched:
                cherrypy.log(f"Rule '{rule_name}' trifft nichts.")
                continue

            # Create updated Data and get UUIDs
            for row in matched:

                # UUIDs
                uuid = row.get('uuid')
                if uuid is None:
                    raise ValueError(f'The following data in the DB has no UUID ! - {row}')
                rule_result['entries'].append(uuid)

                # Update Request
                if not dry_run:

                    query = {'key': 'uuid', 'value': uuid}
                    updated = db_handler.update(data=new_category, condition=query)

                    # soft Exception Handling
                    if not updated:
                        cherrypy.log.error((f"Bei Rule '{rule_name}' konnte der Eintrag " +
                                            f"'{uuid}' nicht geupdated werden - skipping..."))
                        continue

                    rule_result['tagged'] += updated

            # Store Result for this Rule
            result['tagged'] += rule_result.get('tagged')
            result[rule_name] = rule_result

        return result


    def tag_ai(self, data, take_all=False):
        """
        Automatische Kategorisierung anhand eines Neuronalen Netzes.
        Trainingsdaten sind die zum Zeitpunkt des taggings bereits
        getaggten Datensätze aus der Datenbank. Für neue Tags werden die
        ungetaggten (default) oder alle Datensätze des aktuellen Imports berücksichtigt.

        Args:
            take_all, bool(False): Switch um nur ungetaggte oder alle Datensätze zu untersuchen.
        Returns:
            Anzahl der getaggten Datensätze
        """
        #TODO: Fake Funktion
        cherrypy.log("Tagging with AI....")
        list_of_categories = [
            'Vergnügen', 'Versicherung', 'KFZ', 'Kredite',
            'Haushalt und Lebensmittel', 'Anschaffung'
        ]
        count = 0
        for transaction in data:
            if transaction.get('primary_tag') is None or take_all:
                # Komplette Untersuchung
                # Setzt 'primary' und 'secondary' (ggf. None) soweit erkannt
                transaction['primary_tag'] = random.choice(list_of_categories)
                transaction['secondary_tag'] = None
                count = count + 1
        cherrypy.log("Tagging with AI....DONE")
        return random.randint(0, count)
