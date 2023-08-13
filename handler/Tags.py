#!/usr/bin/python3 # pylint: disable=invalid-name
"""Ausgelagerter Handler für die Umsatzuntersuchung."""

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

    def tag_regex(self, db_handler, ruleset, priority=1, dry_run=False, priority_override=None):
        """
        Automatische Kategorisierung anhand von hinterlegten RegExes je Kategorie.

        Args:
            db_handler, object: Instance for DB interaction (read/write)
            ruleset, dict: Rules to be applied on users transactions
            priority, int(1): Value of priority for this tagging run
                              in comparison with already tagged transactions
                              This value will be set as the new priority in DB
            priority_override, int(None): Compare with priority but set this value instead.
            dry_run, bool(False): Switch to show, which TX would be updated. Do not update.
        Returns:
            dict:
            - tagged: int, Anzahl der getaggten Datensätze (0 bei dry_run)
            - entries: list(dict),
                - uuid: UUID
                - primary_tag: Primäre Kategorie
                - primary_rule: Regel, die zu diesem Tag geführt hat
                - secondary_tag: Sekundäre Kategorie
                - secondary_rule: Regel, die zu diesem Tag geführt hat
        """
        #TODO: Pseudo Code only
        #db_handler.select
        return


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
