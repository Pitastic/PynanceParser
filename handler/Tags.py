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

    def tag_regex(self, data, take_all=False):
        """
        Automatische Kategorisierung anhand von hinterlegten RegExes je Kategorie.

        Args:
            take_all, bool(False): Switch um nur ungetaggte oder alle Datensätze zu untersuchen.
        Returns:
            Anzahl der getaggten Datensätze
        """
        #TODO: Fake Funktion
        cherrypy.log("Tagging with RegExes....")
        count = 0
        for transaction in data:
            if transaction.get('primary_tag') is None or take_all:
                # Komplette Untersuchung
                # Setzt 'primary' und 'secondary' (ggf. None) soweit erkannt
                count = count + 1
        cherrypy.log("Tagging with RegExes....DONE")
        return random.randint(0, count)

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
