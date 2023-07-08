#!/usr/bin/python3 # pylint: disable=invalid-name
"""Ausgelagerter Handler für die Umsatzuntersuchung."""

import random
#import cherrypy


class Tagger(object):
    """
    Handler für die Untersuchung und Markierung von Umsätzen.
    """
    def __init__(self):
        pass

    def tag_regex(self, data, take_all=False):
        """
        Automatische Kategorisierung anhand von hinterlegten RegExes je Kategorie.

        Args:
            take_all, bool(False): Switch um nur ungetaggte oder alle Datensätze zu untersuchen.
        Returns:
            Anzahl der getaggten Datensätze
        """
        #TODO: Fake Funktion
        count = 0
        for transaction in data:
            if transaction.get('primary_tag') is None or take_all:
                # Komplette Untersuchung
                # Setzt 'primary' und 'secondary' (ggf. None) soweit erkannt
                count = count + 1
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
        return random.randint(0, count)
