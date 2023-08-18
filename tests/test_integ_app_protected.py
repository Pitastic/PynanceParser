#!/usr/bin/python3 # pylint: disable=invalid-name
"""Testmodul für die privaten/protected Methoden des Main-Skripts"""

import os
import sys
import cherrypy
import pytest

# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from app.app import UserInterface


class TestUserInterfaceProtected():
    """PyTest Klasse für die Tests am UserInterface"""

    def setup_class(self):
        """Vorbereitung der Testklasse"""

        # Config
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'config.conf'
        )
        cherrypy.config.update(config_path)
        assert cherrypy.config.get('database.backend'), \
            "Unable to read Test Config"

        # Instanziieren der Klasse
        self.ui = UserInterface()


    def test_read_input_csv(self):
        """
        Testet den Handler für das Einlesen übermittelter Daten im CSV Format.
        Die Methode wird bei gerade hochgeladenen Daten genutzt. Das Format 
        wird bei 'None' belassen, um auch das Erraten des Formats zu testen.
        """
        found_rows = self.ui._read_input(os.path.join( # pylint: disable=protected-access
            os.path.dirname(os.path.abspath(__file__)),
            'commerzbank.csv'
        ), bank='Commerzbank', data_format=None)

        # Check Return Value
        assert found_rows == 5, (f'Es wurden {found_rows} statt der '
                                 'erwarteten 5 Einträge aus der Datei eingelesen.')
        assert len(self.ui.data) == 5, \
            (f'Es wurden {len(self.ui.data)} Einträge statt '
            'der 5 erwarteten in der Instanz UserInterface gespeichert')

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_read_input_pdf(self):
        """
        Testet den Handler für das Einlesen übermittelter Daten im PDF Format.
        Die Methode wird bei gerade hochgeladenen Daten genutzt. Das Format 
        wird bei 'None' belassen, um auch das Erraten des Formats zu testen.
        """
        return

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_read_input_html(self):
        """
        Testet den Handler für das Einlesen übermittelter Daten im HTML Format.
        Die Methode wird bei gerade hochgeladenen Daten genutzt. Das Format 
        wird bei 'None' belassen, um auch das Erraten des Formats zu testen.
        """
        return

    def test_flush_to_db(self):
        """Testet das Wegschreiben von Daten aus der Instanz in die Datenbank"""

        # Muss Daten in der Instanz haben
        # Leeren und 5 Datensätze einlesen
        self.ui.data = None
        self.test_read_input_csv()

        # Methode ausführen
        inserted = self.ui._flush_to_db() # pylint: disable=protected-access

        # Überprüfen
        assert inserted == 5, \
            (f'Es wurden {len(r)} Einträge statt '
            'der 5 erwarteten von UserInterface gespeichert')

        r = self.ui.db_handler.select()
        assert len(r) == 5, \
            (f'Es wurden {len(r)} Einträge statt '
            'der 5 erwarteten von UserInterface gespeichert')

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_create_user(self):
        """Testet das Anlegen eines Users"""
        return

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_save_rule(self):
        """Testet das Speichern einer Regel (mehrfach) sowie das Update einer Regel"""
        return

    def test_load_ruleset_all(self):
        """Testet das Laden aller Regeln für den anfragenden Benutzer"""
        #TODO: User erkennen und für den Test setzen
        # cherrypy.request.user = 'Test'
        rules = self.ui._load_ruleset() # pylint: disable=protected-access
        # Fake Rules sind 'Supermarkets' und 'City Tax'
        assert rules.get('Supermarkets'), "Die Regel 'Supermarkets' wurde nicht gefunden"
        assert rules.get('City Tax'), "Die Regel 'City Tax' wurde nicht gefunden"

    def test_load_ruleset_one(self):
        """Testet das Laden einer bestimmten Regeln für den anfragenden Benutzer"""
        #TODO: User erkennen und für den Test setzen
        # cherrypy.request.user = 'Test'
        rules = self.ui._load_ruleset('Supermarkets') # pylint: disable=protected-access
        assert rules.get('Supermarkets'), "Die Regel 'Supermarkets' wurde nicht gefunden"

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_delete_user(self):
        """Testet das Löschen eines Users"""
        return