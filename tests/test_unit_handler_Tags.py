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

        # Starten von DbHandler
        if cherrypy.config['database.backend'] == 'tiny':
            self.db_handler = TinyDbHandler()
        elif cherrypy.config['database.backend'] == 'mongo':
            self.db_handler = MongoDbHandler()
        else:
            raise NotImplementedError(("The configure database engine ",
                                     f"{cherrypy.config['database.backend']} ",
                                      "is not supported !"))
        assert self.db_handler, \
            (f"DbHandler {cherrypy.config['database.backend']} Klasse konnte nicht ",
            "instanziiert werden")
        self.db_handler.truncate()

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
            'City Tax ': {
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
                    f"In Eintrag {i} gab es false-positives"

        # Checks passed, save to DB
        inserted_db = self.db_handler.insert(parsed_data)
        assert inserted_db.get('inserted') > 0, \
            "Die Testdaten konnten nicht in die DB eingefügt werden"

    def test_regex(self):
        """Testet das Kategorisieren der Datensätzemit fest hinterlegten Regeln.
        Berücksichtigt alle Umsätze ohne Kategorie"""
        tagging_result = self.tagger.tag_regex(self.db_handler, ruleset=self.ruleset)
        for i, entry in enumerate(tagging_result.get('entries')):
            if entry.get('uuid') != 'print-for-now':
                #TODO: Find uuids zu Results zum Testen
                print(entry)

        

    def test_regex_untagged(self):
        """Testet das Kategorisieren der Datensätzemit fest hinterlegten Regeln.
        Berücksichtigt alle Umsätze nud überschreibt auch vorhandene Kategorien."""
        # prio auf 4 aber override auf 1
        #TODO: Change a Tag in self.data
        #TODO: Delete a Tag in self.data
        # Change Tagging rules to test overwrite
        self.ruleset['City Tax']['secondary'] = 'Grundsteuer'
        tagging_result = self.tagger.tag_regex(self.db_handler, ruleset=self.ruleset, dry_run=True,
                                               priority=9, priority_override=1)
        assert tagging_result.get('tagged') == 0, \
            "Die Option dry_run hat trotzdem Datensätze verändert"
        #TODO: Check 'Grundsteuer' is present with priority 1
        assert True

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_regex_custom(self):
        """Testet das Kategorisieren der Datensätze mit Regeln,
        die vom Benutzer hinterlegt worden sind"""
        return None

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_ai(self):
        """Testet das Kategorisieren der Datensätze mit Hilfe der KI"""
        return None
