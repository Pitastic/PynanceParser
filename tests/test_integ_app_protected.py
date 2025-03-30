#!/usr/bin/python3 # pylint: disable=invalid-name
"""Testmodul für die privaten/protected Methoden des Main-Skripts"""

import os
import pytest


def test_read_input_csv(test_app):
    """
    Testet den Handler für das Einlesen übermittelter Daten im CSV Format.
    Die Methode wird bei gerade hochgeladenen Daten genutzt. Das Format 
    wird bei 'None' belassen, um auch das Erraten des Formats zu testen.
    """
    with test_app.app_context():
        found_rows = test_app.host._read_input(os.path.join( # pylint: disable=protected-access
            os.path.dirname(os.path.abspath(__file__)),
            'commerzbank.csv'
        ), bank='Commerzbank', data_format=None)

        # Check Return Value
        assert found_rows == 5, (f'Es wurden {found_rows} statt der '
                                    'erwarteten 5 Einträge aus der Datei eingelesen.')
        assert len(test_app.host.data) == 5, \
            (f'Es wurden {len(test_app.host.data)} Einträge statt '
            'der 5 erwarteten in der Instanz UserInterface gespeichert')

@pytest.mark.skip(reason="Currently not implemented yet")
def test_read_input_pdf():
    """
    Testet den Handler für das Einlesen übermittelter Daten im PDF Format.
    Die Methode wird bei gerade hochgeladenen Daten genutzt. Das Format 
    wird bei 'None' belassen, um auch das Erraten des Formats zu testen.
    """
    return

@pytest.mark.skip(reason="Currently not implemented yet")
def test_read_input_html():
    """
    Testet den Handler für das Einlesen übermittelter Daten im HTML Format.
    Die Methode wird bei gerade hochgeladenen Daten genutzt. Das Format 
    wird bei 'None' belassen, um auch das Erraten des Formats zu testen.
    """
    return

def test_flush_to_db(test_app):
    """Testet das Wegschreiben von Daten aus der Instanz in die Datenbank"""

    # Muss Daten in der Instanz haben
    # Leeren und 5 Datensätze einlesen
    test_app.host.data = None
    test_read_input_csv(test_app)

    with test_app.app_context():
        # Methode ausführen
        inserted = test_app.host._flush_to_db() # pylint: disable=protected-access

        # Überprüfen
        assert inserted == 5, \
            (f'Es wurden {inserted} Einträge statt '
            'der 5 erwarteten von UserInterface gespeichert')

        r = test_app.host.db_handler.select()
        assert len(r) == 5, \
            (f'Es wurden {len(r)} Einträge statt '
            'der 5 erwarteten von UserInterface gespeichert')

def test_set_manual_tag(test_app):
    """
    Testet das Setzen eines Tags für einen Eintrag in der Instanz.
    """
    with test_app.app_context():
        iban = test_app.config['IBAN']
        t_id = '6884802db5e07ee68a68e2c64f9c0cdd'

        # Setzen des Tags
        r = test_app.host._set_manual_tag( # pylint: disable=protected-access
            iban, t_id,
            {
                'primary_tag': 'Test_Pri',
                'secondary_tag': 'Test_Second'
            }
        )
        assert r.get('updated') == 1, 'Es wurde kein Eintrag aktualisiert. '

        # Überprüfen
        condition = {
            'key': 'uuid',
            'value': t_id,
            'compare': '=='
        }
        rows = test_app.host.db_handler.select(iban, condition)
        assert rows[0].get('primary_tag') == 'Test_Pri' and \
            rows[0].get('secondary_tag') == 'Test_Second', \
            f'Der Tag wurde nicht gesetzt: {rows[0]}'

@pytest.mark.skip(reason="Currently not implemented yet")
def test_create_user():
    """Testet das Anlegen eines Users"""
    return

@pytest.mark.skip(reason="Currently not implemented yet")
def test_save_rule():
    """Testet das Speichern einer Regel (mehrfach) sowie das Update einer Regel"""
    return

def test_load_ruleset_all(test_app):
    """Testet das Laden aller Regeln für den anfragenden Benutzer"""
    #TODO: User erkennen und für den Test setzen
    with test_app.app_context():
        rules = test_app.host.tagger._load_ruleset() # pylint: disable=protected-access

        # Fake Rules sind 'Supermarkets' und 'City Tax'
        assert rules.get('Supermarkets'), "Die Regel 'Supermarkets' wurde nicht gefunden"
        assert rules.get('City Tax'), "Die Regel 'City Tax' wurde nicht gefunden"

def test_load_ruleset_one(test_app):
    """Testet das Laden einer bestimmten Regeln für den anfragenden Benutzer"""
    #TODO: User erkennen und für den Test setzen
    with test_app.app_context():
        rules = test_app.host.tagger._load_ruleset('Supermarkets') # pylint: disable=protected-access
        assert rules.get('Supermarkets'), "Die Regel 'Supermarkets' wurde nicht gefunden"

@pytest.mark.skip(reason="Currently not implemented yet")
def test_delete_user():
    """Testet das Löschen eines Users"""
    return
