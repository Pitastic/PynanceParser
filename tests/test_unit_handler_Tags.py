#!/usr/bin/python3 # pylint: disable=invalid-name
"""
Testmodul für die Funktionen des Taggers.
(Erfolgreiche Tests der DB Handler sind erforderlich)
"""

import os
import sys
import json
import pytest
import cherrypy

# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from handler.Tags import Tagger
from handler.TinyDb import TinyDbHandler
from handler.MongoDb import MongoDbHandler

class TestTagHandler():
    """PyTest Klasse für Tests mit dem Tagger"""

    def setup_class(self):
        """Vorbereitung der Testklasse"""

        # Config
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'config.conf'
        )
        cherrypy.config.update(config_path)
        assert cherrypy.config.get('iban'), "Unable to read Test Config"
        assert cherrypy.config['iban'] != "", "IBAN not set in Config"
        assert cherrypy.config.get('database.backend'), \
            "Unable to read Test Config"
        assert cherrypy.config.get('database.backend') != "" and \
               cherrypy.config.get('database.name') != "" and \
               cherrypy.config.get('database.uri') != "", \
            "DB Handler is not set properly in Config"
        print('[', 16*'-', f"> ]  Testing {cherrypy.config.get('database.backend')}",
              "(change Config for another Handler)")

        # Instanziieren des Taggers
        self.tagger = Tagger()
        assert self.tagger, "Tagger Klasse konnte nicht instanziiert werden"

        # Starten des Mock-DbHandlers
        self.db_handler = MockDatabase()

        # Fake Daten laden
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'commerzbank.json'
        )
        with open(path, 'rb') as test_data:
            self.data = json.load(test_data)
        assert self.data, "Test Kontoumsätze konnten nicht geladen werden"

        # Test Tagging-Ruleset hinterlegen
        self.ruleset = {
            'Supermarkets': {
                'primary': 'Lebenserhaltungskosten',
                'secondary': 'Lebensmittel',
                'regex': r"(EDEKA|Wucherpfennig|Penny|Aldi|Kaufland|netto)",
            },
            'City Tax': {
                'primary': 'Haus und Grund',
                'secondary': 'Stadtabgaben',
                'parsed': {
                    'Gläubiger-ID': r'DE7000100000077777'
                },
            }
        }


    def test_parsing_regex(self):
        """Testet das Parsen der Datensätze mit den fest hinterlegten RegExes"""
        parsed_data = self.tagger.parse(self.data)
        # Check if specific entries were tagged
        for i, entry in enumerate(parsed_data):
            if entry.get('date_tx') == 1672876800 and entry.get('betrag') == -221.98:
                # Eintrag mit Gläubiger-ID und Mandatsreferenz
                assert entry.get('parsed').get('Mandatsreferenz'), \
                    f"Die Mandatsreferenz wurde in Eintrag {i} nicht erkannt: {entry}"
                assert entry.get('parsed').get('Gläubiger-ID'), \
                    f"Die Gläubiger-ID wurde in Eintrag {i} nicht erkannt: {entry}"
            else:
                assert not entry.get('parsed'), \
                    f"In Eintrag {i} gab es False-Positives"

    def test_regex(self):
        """Testet das Kategorisieren der Datensätze mit fest hinterlegten Regeln.
        Berücksichtigt alle Umsätze ohne Kategorie"""
        tagging_result = self.tagger.tag_regex(self.db_handler, ruleset=self.ruleset)
        assert tagging_result.get('Supermarkets').get('tagged') == 2, \
            "Die Regel 'Supermarkets' hat nicht die richtige Anzahl an Einträgen getroffen"
        assert tagging_result.get('City Tax').get('tagged') == 1, \
            "Die Regel 'City Tax' hat nicht die richtige Anzahl an Einträgen getroffen"

    def test_regex_untagged(self):
        """Testet das Kategorisieren der Datensätzemit fest hinterlegten Regeln.
        Berücksichtigt alle Umsätze nud überschreibt auch vorhandene Kategorien."""
        # prio auf 4 aber override auf 1
        tagging_result = self.tagger.tag_regex(self.db_handler, ruleset=self.ruleset, dry_run=True,
                                               prio=9, prio_set=1)
        assert tagging_result.get('tagged') == 0, \
            "Die Option dry_run hat trotzdem Datensätze verändert"
        assert len(tagging_result.get('Supermarkets').get('entries')) == 2, \
            "Die Regel 'Supermarkets' hat nicht die richtige Anzahl an Einträgen getroffen"
        assert len(tagging_result.get('City Tax').get('entries')) == 1, \
            "Die Regel 'City Tax' hat nicht die richtige Anzahl an Einträgen getroffen"

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_regex_custom(self):
        """Testet das Kategorisieren der Datensätze mit Regeln,
        die vom Benutzer hinterlegt worden sind"""
        return None

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_ai(self):
        """Testet das Kategorisieren der Datensätze mit Hilfe der KI"""
        return None

class MockDatabase:
    """
    Mock the Database connection and work with fake entries.
    """

    def __init__(self):
        """Konstruktor hinterlegt Variablen"""
        self.query1 = [
            {
                'key': 'priority', 'value': 1,
                'compare': '<'
            }, {
                'key': 'tx_text', 'value': '(EDEKA|Wucherpfennig|Penny|Aldi|Kaufland|netto)',
                'compare': 'regex'
            }
            ]
        self.query2 = [
            {
                'key': 'priority', 'value': 1,
                'compare': '<'
            }, {
                'key': {'parsed': 'Gläubiger-ID'}, 'value': 'DE7000100000077777',
                'compare': 'regex'
            }
        ]
        self.db_all = [

            {
            'date_tx': 1672531200, 'date_wert': 1684195200, 'art': 'Überweisung',
            'text_tx': ('Wucherpfennig sagt Danke 88//HANNOV 2023-01-01T08:59:42 '
                        'KFN 9 VJ 7777 Kartenzahlung'),
            'betrag': -11.63, 'iban': 'DE89370400440532013000', 'currency': 'USD',
            'parsed': {}, 'primary_tag': 'Updated', 'secondary_tag': None,
            'uuid': 'b5aaffc31fa63a466a8b55962995ebcc', 'prio': 0
            },

            {
            'date_tx': 1672617600, 'date_wert': 1684108800, 'art': 'Überweisung',
            'text_tx': ('MEIN GARTENCENTER//Berlin 2023-01-02T12:57:02 KFN 9 VJ 7777 '
                        'Kartenzahlung'),
            'betrag': -118.94, 'iban': 'DE89370400440532013000', 'currency': 'USD',
            'parsed': {}, 'primary_tag': 'Updated', 'secondary_tag': None,
            'uuid': '13d505688ab3b940dbed47117ffddf95', 'prio': 0
            },

            {
            'date_tx': 1672704000, 'date_wert': 1684108800, 'art': 'Überweisung',
            'text_tx': ('EDEKA, München//München/ 2023-01-03T14:39:49 KFN 9 VJ '
                        '7777 Kartenzahlung'),
            'betrag': -99.58, 'iban': 'DE89370400440532013000', 'currency': 'EUR',
            'parsed': {}, 'primary_tag': None, 'secondary_tag': None,
            'uuid': 'a8bd1aa187c952358c474ca4775dbff8', 'prio': 0
            },

            {
            'date_tx': 1672790400, 'date_wert': 1684108800, 'art': 'Überweisung',
            'text_tx': ('DM FIL.2222 F:1111//Frankfurt/DE 2023-01-04T13:22:16 KFN 9 VJ '
                        '7777 Kartenzahlung'),
            'betrag': -71.35, 'iban': 'DE89370400440532013000', 'currency': 'EUR',
            'parsed': {}, 'primary_tag': None, 'secondary_tag': None,
            'uuid': 'a1eb37e4ed4a22a38bdeef2f34fb76c3', 'prio': 0
            },

            {
            'date_tx': 1672876800, 'date_wert': 1684108800, 'art': 'Überweisung',
            'text_tx': ('Stadt Halle 0000005112 OBJEKT 0001 ABGABEN LT. BESCHEID '
                        'End-to-End-Ref.: 2023-01-00111-9090-0000005112 '
                        'Mandatsref: M1111111 Gläubiger-ID: DE7000100000077777 '
                        'SEPA-BASISLASTSCHRIFT wiederholend'),
            'betrag': -221.98, 'iban': 'DE89370400440532013000', 'currency': 'EUR',
            'parsed': {'Mandatsreferenz': 'M1111111'}, 'primary_tag': None, 'secondary_tag': None,
            'uuid': 'ba9e5795e4029213ae67ac052d378d84', 'prio': 0
            }

        ]

    def select(self, collection=None, condition=None, multi=None): # pylint: disable=unused-argument
        """
        Nimmt alle Argumente der echten Funktion entgegen und gibt Fake-Daten zurück.
        Condition wird für die Auswahl der Fake-Datensätze geprüft.

        Returns:
            dict:
                - result, list: Liste der ausgewählten Fake-Datensätze
        """
        if condition == self.query1:
            return [self.db_all[0], self.db_all[2]]

        if condition == self.query2:
            return [self.db_all[4]]

        return []

    def update(self, data, collection=None, condition=None, multi=None): # pylint: disable=unused-argument
        """
        Nimmt alle Argumente der echten Funktion entgegen und gibt Fake-Daten zurück.
        Condition wird für die Auswahl der Fake-Datensätze geprüft.

        Returns:
            dict:
                - updated, int: Anzahl der angeblich aktualisierten Datensätze
        """
        if condition.get('key') == 'uuid':
            return 1

        return
