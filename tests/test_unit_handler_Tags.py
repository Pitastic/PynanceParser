#!/usr/bin/python3 # pylint: disable=invalid-name
"""Testmodul für die Funktionen des Taggers"""

import os
import sys
import json
import pytest
import cherrypy

# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from handler.Tags import Tagger


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

        # Instanziieren des Taggers
        self.tagger = Tagger()
        assert self.tagger, "Tagger Klasse konnte nicht instanziiert werden"

        # Fake Daten laden
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'commerzbank.json'
        )
        with open(path, 'rb') as test_data:
            self.data = json.load(test_data)
        assert self.data, "Test Kontoumsätze konnten nicht geladen werden"


    def test_parsing_regex(self):
        """Testet das Taggen der Datensätze mit den fest hinterlegten RegExes"""
        #TODO: Build own Dict - nur mit hash, text_tx "" und parsed {}
        tagged_data = self.tagger.parse(self.data)
        # Check if specific entries were tagged
        for i, entry in enumerate(tagged_data):
            if entry.get('date_tx') == 1672876800 and entry.get('betrag') == -221.98:
                # Eintrag mit Gläubiger-ID und Mandatsreferenz
                assert entry.get('parsed').get('Mandatsreferenz'), \
                    f"Die Mandatsreferenz wurde in Eintrag {i} nicht erkannt: {entry}"
                assert entry.get('parsed').get('Gläubiger-ID'), \
                    f"Die Gläubiger-ID wurde in Eintrag {i} nicht erkannt: {entry}"
        self.data = tagged_data

    def test_regex_all(self):
        """Testet das Kategorisieren der Datensätzemit fest hinterlegten Regeln.
        Berücksichtigt alle Umsätze."""
        categorized_data = self.tagger.tag_regex(self.data)
        #TODO: Check if specific entries were categorized
        assert True
        self.data = categorized_data

    def test_regex_untagged(self):
        """Testet das Kategorisieren der Datensätzemit fest hinterlegten Regeln.
        Berücksichtigt nur ungetaggte Umsätze."""
        #TODO: Change a Tag in self.data
        #TODO: Delete a Tag in self.data
        categorized_data = self.tagger.tag_regex(self.data, take_all=False)
        #TODO: Check if manual changed entry is unchanged and delted entry is tagged
        assert True
        self.data = categorized_data

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_regex_custom(self):
        """Testet das Kategorisieren der Datensätze mit Regeln,
        die vom Benutzer hinterlegt worden sind"""
        return None

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_ai(self):
        """Testet das Kategorisieren der Datensätze mit Hilfe der KI"""
        return None
