#!/usr/bin/python3 # pylint: disable=invalid-name
"""Testmodul für die privaten/protected Methoden des Main-Skripts"""

import os
import pytest


def test_add_iban(test_app):
    """
    Testet das Hinzufügen einer IBAN in der Instanz.
    """
    with test_app.app_context():

        with test_app.test_client() as client:
            result = client.put("/api/add/DE89370400440532013000")
            assert result.status_code == 201, 'Die IBAN wurde nicht hinzugefügt.'

            # No Doublettes
            result = client.put("/api/add/DE89370400440532013000")
            assert result.status_code == 400, 'Die IBAN wurde doppelt hinzugefügt.'


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
        found_rows_len = len(found_rows)
        assert found_rows_len == 5, (f'Es wurden {found_rows_len} statt der '
                                    'erwarteten 5 Einträge aus der Datei eingelesen.')
        # Savev to DB for next Tests
        r = test_app.host.db_handler.insert(found_rows, "DE89370400440532013000")
        assert r.get('inserted') == 5, \
            "Es wurden nicht alle Einträge in die DB eingefügt."

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


def test_set_manual_tag(test_app):
    """
    Testet das Setzen eines Tags für einen Eintrag in der Instanz.
    """
    with test_app.app_context():
        iban = "DE89370400440532013000"
        t_id = '6884802db5e07ee68a68e2c64f9c0cdd'

        # Setzen des Tags
        r = test_app.host._set_manual_tag_and_cat( # pylint: disable=protected-access
            iban, t_id, tags= ['Test_Second'], category='Test_Pri'
        )
        assert r.get('updated') == 1, 'Es wurde kein Eintrag aktualisiert. '

        # Überprüfen
        condition = {
            'key': 'uuid',
            'value': t_id,
            'compare': '=='
        }
        rows = test_app.host.db_handler.select(iban, condition)
        assert rows[0].get('category') == 'Test_Pri' and \
            'Test_Second' in rows[0].get('tags'), \
            f'Der Tag wurde nicht gesetzt: {rows[0]}'

@pytest.mark.skip(reason="Currently not implemented yet")
def test_create_user():
    """Testet das Anlegen eines Users"""
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
