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

    def categorize(self, rules, iban: str = None,
                   prio: int = 1, prio_set: int = None, dry_run: bool = False) -> dict:
        """
        Kategorisiert die Kontoumsätze anhand von hinterlegten Regeln je Kategorie.

        Args:
            rules:         Named rules to be applied on users transactions (with category)
            iban:          Name der Collection, in der gefiltert werden soll.
                           Default: IBAN aus der Config.
            prio:          Override ruleset value of priority for this categorization run
                           in comparison with already cat. transactions (higher = important)
            prio_set:      Override: Compare with 'prio' but set this value instead.
            dry_run:       Switch to show, which TX would be updated. Do not update.
        Returns:
            dict:
            - categorized (int): Summe aller erfolgreichen Kategorisierungen (0 bei dry_run)
            - entries (list): UUIDs die selektiert wurden (auch bei dry_run)
        """
        result = { 'categorized': 0, 'entries': [] }

        for rule_name, rule in rules.items():
            logging.info(f"Kategorisierung mit Rule {rule_name}...")

            # Updated Category Object
            new_categories = {}

            if rule.get('category') is not None:
                new_categories['category'] = rule.get('category')

            if rule.get('subcategory') is not None:
                new_categories['subcategory'] = rule.get('subcategory')

            if not new_categories:
                logging.warning(f"Rule '{rule_name}' hat keine Kategorie - skipping...")
                continue

            if prio_set is not None:
                new_categories['prio'] = prio_set
            else:
                new_categories['prio'] = rule.get('prio', prio)

            # Allgemeiner Startfilter und spezielle Conditions einer Rule
            if prio > 1:
                # prio values override
                query_args = self._form_tag_query(prio, iban)

            else:
                # use rule prio or default
                query_args = self._form_tag_query(rule.get('prio', prio))

            # -- Add Text RegExes
            if rule.get('regex') is not None:
                query_args['condition'].append({
                    'key': 'text_tx',
                    'value': rule.get('regex'),
                    'compare': 'regex'
                })

            # -- Add Tags (as criteria)
            if rule.get('tags') is not None:
                query_args['condition'].append({
                    'key': 'tags',
                    'value': rule.get('tags'),
                    'compare': 'in'
                })

            # -- Add Parsed Values
            multi = 'AND'
            if rule.get('parsed') is not None:
                parsed_condition = rule.get('parsed')
                multi = parsed_condition.get('multi', 'AND')

                for key, val in parsed_condition.get('query', {}).items():
                    query_args['condition'].append({
                        'key': {'parsed': key},
                        'value': val,
                        'compare': 'regex'
                    })

            # Dry Run first (store results)
            logging.debug(f"Query Args: {query_args.get('condition')}")
            matched = self.db_handler.select(
                collection=query_args.get('collection'),
                condition=query_args.get('condition'),
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

                query = {'key': 'uuid', 'value': uuid}
                updated = self.db_handler.update(data=new_categories, condition=query)

                # soft Exception Handling
                if not updated:
                    logging.error((f"Bei Rule '{rule_name}' konnte der Eintrag "
                                    f"'{uuid}' nicht geupdated werden - skipping..."))
                    continue

                result['categorized'] += updated.get('updated')

            return result

    def tag(self, ruleset: dict, collection: str=None, dry_run: bool=False) -> dict:
        """
        Tagged Transaktionen anhand von Regeln in der Datenbank.

        Args:
            ruleset:         Named rules to be applied on users transactions
            collection:      Name der Collection, in der gefiltert werden soll.
                             Default: IBAN aus der Config.
            dry_run:         Switch to show, which TX would be updated. Do not update.
        Returns:
            dict:
            - tagged (int): Summe aller erfolgreichen Taggings (0 bei dry_run)
            - entries (list): UUIDs die selektiert wurden (auch bei dry_run)
        """
        #raise NotImplementedError("Function not finished yet !")
        result = { 'tagged': 0, 'entries': [] }

        # Allgemeine Startfilter für die Condition (ignore Prio bei Tagging)
        query_args = self._form_tag_query(99, collection)

        for rule_name, rule in ruleset.items():
            logging.info(f"RegEx Tagging mit Rule {rule_name}...")

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

            # Tags to set when matched
            new_tags = rule.get('tags', [])

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
                tags_to_set = [t for t in new_tags if t not in existing_tags]

                if not tags_to_set:
                    # Skip this loop
                    logging.info((f"Rule '{rule_name}' hat keine neuen Tags "
                                    f"für {uuid} - skipping (tag only)..."))
                    continue

                query = {'key': 'uuid', 'value': uuid}
                updated = self.db_handler.update(data={'tags': tags_to_set}, condition=query)

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
            'entries': [e.get('uuid') for e in entries],
        }

        logging.info("Tagging with AI....DONE")
        return result

    def tag_and_cat(self, iban: str, rule_name: str = None, category_name: str = None,
                    dry_run: bool = False) -> dict:
        """
        Tagged und kategorisiert die Kontoumsätze, indem Unterfunktionen aufgerufen werden.

        Args:
            iban            Name der Collection
            rule_name:      UUID der anzuwendenden Taggingregel.
                            Reserviertes Keyword 'ai' führt nur das AI Tagging aus.
                            Default: Es werden alle Regeln des Benutzers ohne das
                            AI Tagging angewendet.
            category_name:  UUID der anzuwendenden Kategorisierungsregel.
                            Default: Es werden alle Regeln des Benutzers angewendet.
            dry_run:        Switch to show, which TX would be updated. Do not update.
                            Default: False
        Returns dict:
            - tagged (int): Summe aller erfolgreichen Taggings (0 bei dry_run)
            - categorized (int): Summe aller erfolgreichen Kategorisierungen (0 bei dry_run)
            - entries (list): Betroffene UUIDs dieser Operation (auch bei dry_run)
        """
        result = { 'tagged': 0, 'categorized': 0, 'entries': [] }

        # Tagging Rules (specific rule or all - but not ai)
        if rule_name != 'ai':

            # Load specific tagging rule or all
            tagging_rules = self._load_ruleset(rule_name=rule_name, categories=False)

            # Log and Pre-Flightchecks
            logging.debug(f"Regeln geladen: {tagging_rules}")
            if not tagging_rules:
                if rule_name:
                    raise KeyError((f'Eine Regel mit dem Namen {rule_name} '
                                    'konnte für den User nicht gefunden werden.'))

                raise ValueError('Es existieren noch keine Regeln für den Benutzer')

            # Start Tagging (loop until none found)
            result['tagged'], result['entries'] =  self.tag(tagging_rules, iban, dry_run=dry_run)

        else:
            # AI only
            result['tagged'], result['entries'] = self.tag_ai(iban, dry_run=dry_run)

        # Categorize Rules (specific or all)
        cat_rules = self._load_ruleset(rule_name=category_name, categories=True)

        # Log and Pre-Flightchecks
        logging.debug(f"Cat-Regeln geladen: {cat_rules}")
        if not cat_rules:
            if category_name:
                raise KeyError((f'Eine Cat-Regel mit dem Namen {category_name} '
                                'konnte für den User nicht gefunden werden.'))

            raise ValueError('Es existieren noch keine Cat-Regeln für den Benutzer')

        # Benutzer Regeln ignoriert alle automatischen Regeln,
        # setzt aber wieder nur seine eigene Prio.
        prio = prio_set = None
        if category_name is not None:
            prio_set = cat_rules[category_name].get('prioriry')
            prio = 99

        # Kategorisierung wird einmal und nicht rekursiv durchgeführt
        result['categorized'], more_entries = self.categorize(cat_rules, iban,
                                                              prio, prio_set, dry_run)
        result['entries'].append (more_entries)

        return result

    def tag_or_cat_custom(self, iban: str, category: str = None, subcategory: str = None,
                          tags: list[str] = None, regex: str = None,
                          parsed_keys: list = None, parsed_vals: list = None, multi: str ='AND',
                          prio: int = 1, prio_set: int = None, dry_run: bool = False) -> dict:
        """Kategorisierung oder Tagging mit einer Custom Rule.
        Args:
            iban            Name der Collection
            category:       Name der zu setzenden Primärkategory.
            subcategory:    Name der zu setzenden Sekundärkategorie.
            tags:           Liste der zu setzenden Tags.
            tags_multi:     Logische Verknüpfung der Tags (AND|OR).
                            Default: AND
            regex:          Regulärer Ausdrück für die Suche im Transaktionstext.
            parsed_keys:    Liste mit Keys zur Prüfung in geparsten Daten.
            parsed_vals:    Liste mit Values zur Prüfung in geparsten Daten.
            multi:          Logische Verknüpfung der Kriterien (AND|OR).
                            Default: AND
            prio:           Value of priority for this tagging run
                            in comparison with already tagged transactions (higher = important)
                            This value will be set as the new priority in DB.
                            Default: 1
            prio_set:       Compare with 'prio' but set this value instead.
                            Default: prio.
            dry_run:        Switch to show, which TX would be updated. Do not update.
                            Default: False
        Returns dict:
            - tagged (int): Summe aller erfolgreichen Taggings (0 bei dry_run)
            - categorized (int): Summe aller erfolgreichen Kategorisierungen (0 bei dry_run)
            - entries (list): Betroffene UUIDs dieser Operation (auch bei dry_run)
        """
        if parsed_keys and parsed_vals and len(parsed_keys) != len(parsed_vals):
            msg = 'Parse-Keys and -Vals were submitted in unequal length !'
            logging.error(msg)
            return {'error': msg}, 400

        result = { 'tagged': 0, 'categorized': 0, 'entries': [] }
        prio_set = prio if prio_set is None else prio_set
        update_data = {}

        if subcategory is not None or category is not None:
            # Set Category: Tags are filter arguments; Prio matters
            update_data['prio'] = prio_set
            query_args = self._form_tag_query(prio, iban)
            query_args['condition'].append({
                'key': 'tags',
                'value': tags,
                'compare': 'in'
            })
            if category is not None:
                update_data['category'] = category

            if subcategory is not None:
                update_data['subcategory'] = subcategory

        else:
            # Set Tags: Prio does not matter (tags to set will be uniqued later)
            query_args = self._form_tag_query(99, iban)


        # Add RegEx
        if regex is not None:
            query_args['condition'].append({
                'key': 'text_tx',
                'value': regex,
                'compare': 'regex'
            })

        # Add Parsed Filters
        for i, parse_key in enumerate(parsed_keys):
            query_args['condition'].append({
                'key': {'parsed': parse_key},
                'value': parsed_vals[i],
                'compare': 'regex'
            })

        # Dry Run first (store results)
        logging.debug(f"Query Args: {query_args.get('condition')}")
        matched = self.db_handler.select(
            collection=query_args.get('collection'),
            condition=query_args.get('condition'),
            multi=multi
        )

        # Nothing to update
        if not matched:
            logging.info("Die Custom Rule trifft nichts.")
            return result

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

            query = {'key': 'uuid', 'value': uuid}

            if subcategory is None and category is None:
                # This is a tagging -> do not duplicate Tags
                existing_tags = row.get('tags', [])
                update_data['tags'] = [t for t in tags if t not in existing_tags]

            updated = self.db_handler.update(data=update_data, condition=query)

            # soft Exception Handling
            if not updated:
                logging.error(("Bei einer Custom Rule konnte der Eintrag "
                              f"'{uuid}' nicht geupdated werden - skipping..."))
                return result

            result['entries'].append(uuid)

            if subcategory is None and category is None:
                # This was a tagging
                result['tagged'] += updated.get('updated')

            else:
                # This was a categorization
                result['categorized'] += updated.get('updated')

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

    def _load_ruleset(self, rule_name=None, categories=False) -> dict:
        """
        Load Rules from the Settings of for the requesting User.

        Args:
            rule_name (str, optional): Lädt die Regel mit diesem Namen.
                                       Default: Es werden alle Regeln geladen.
            categories (bool, optional): Lädt Kategorien anstelle von Regeln.
                                         Default: False
        Returns:
            dict: Verzeichnis nach Namen der Filterregeln
        """
        rule_type = "rule" if categories else "category"
        if rule_name:
            # Bestimmte Regel laden
            raw_rule = self.db_handler.filter_metadata(
                [
                    {"key": "metatype", "value": rule_type},
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
            {"key": "metatype", "value": rule_type}
        )
        rules = {}
        for r in raw_rules:
            regex = r.get('regex')

            if regex:
                r['regex'] = re.compile(regex)

            rules[r.get('name')] = r

        return rules
