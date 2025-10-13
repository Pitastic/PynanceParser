#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisc Module for easy Imports and Methods"""

import json
import os
import sys
import io
from bs4 import BeautifulSoup

# Add Parent for importing from 'app.py'
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper import get_testfile_contents

EXAMPLE_CSV = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'commerzbank.csv'
)


def test_truncate(test_app):
    """Leert die Datenbank und dient als Hilfsfunktion für folgende Tests"""
    with test_app.app_context():

        with test_app.test_client() as client:
            result = client.delete("/api/deleteDatabase/DE89370400440532013000")
            assert result.status_code == 200, "Fehler beim Leeren der Datenbank"


def test_upload_csv_commerzbank(test_app):
    """
    Lädt Beispieldaten über das Formular hoch und überprüft
    ob die Datei angenommen wird und die Serverseitige Verarbeitung durchläuft.
    """
    # Clear DB
    test_truncate(test_app)

    with test_app.app_context():

        with test_app.test_client() as client:
            # Cleared DB ?
            result = client.get("/DE89370400440532013000")
            assert "<td class=" not in result.text, \
                "Die Datenbank war zum Start des Tests nicht leer"

            # Visit Form
            result = client.get('/')
            assert result.status_code == 200, "Der Statuscode der Startseite war falsch"
            assert 'All rights reserved.' in result.text, \
                "Special Heading not found in the response"

            # Prepare File
            content = get_testfile_contents(EXAMPLE_CSV, binary=True)
            files = {'file-input': (io.BytesIO(content), 'commerzbank.csv')}
            # Post File
            result = client.post(
                "/api/upload/DE89370400440532013000",
                data=files, content_type='multipart/form-data'
            )

            # Check Response
            assert result.status_code == 201, \
                f"Die Seite hat den Upload nicht wie erwartet verarbeitet: {result.text}"
            assert result.json.get('filename') == 'commerzbank.csv', \
                "Angaben zum Upload wurden nicht gefunden"

            # Aufruf der Transaktionen
            response2 = client.get("/DE89370400440532013000")
            assert response2.status_code == 200, \
                "Die Ergebnisseite mit den Transaktionen ist nicht (richtig) erreichbar"

            # Aufruf der Umleitung von Logout nach Welcome
            response3 = client.get('/logout')
            assert response3.status_code == 302, \
                "Die Umleitung von Logout nach Welcome ist nicht (richtig) erreichbar"

        # -- Check Parsing --
        soup = BeautifulSoup(response2.text, features="html.parser")

        # 1. Example
        tx_hash = 'cf1fb4e6c131570e4f3b2ac857dead40'
        row1 = soup.css.select(f'#tr-{tx_hash}')
        assert len(row1) == 1, \
            f"Es wurden {len(row1)} rows für das erste Beispiel gefunden"

        content = row1[0].css.filter('.td-betrag')[0].contents[0]
        assert content == 'EUR -11.63', \
            f"Der Content von {tx_hash} ist anders als erwartet: '{content}'"

        # 2. Example
        tx_hash = '786e1d4e16832aa321a0176c854fe087'
        row2 = soup.css.select(f'#tr-{tx_hash}')
        assert len(row2) == 1, \
            f"Es wurden {len(row2)} rows für das zweite Beispiel gefunden"

        content = row2[0].css.filter('.td-betrag')[0].contents[0]
        assert content == 'EUR -221.98', \
            f"Der Content von {tx_hash} / 'betrag' ist anders als erwartet: '{content}'"


def test_reachable_endpoints(test_app):
    """
    Geht die Seiten der Ui durch und prüft,
    ob diese generell erreichbar sind.
    """
    with test_app.app_context():

        with test_app.test_client() as client:

            # /index
            result = client.get('/')
            assert result.status_code == 200, "Der Statuscode der Startseite war falsch"

            result = client.get("/DE89370400440532013000")
            assert result.status_code == 200, "Der Statuscode der IBAN war falsch"


def test_double_upload(test_app):
    """Lädt zwei Dateien hoch und prüft die unterschiedlichen HTTP Stati"""
    test_truncate(test_app)
    with test_app.app_context():
        # Clear DB

        with test_app.test_client() as client:
            # Cleared DB ?
            result = client.get("/DE89370400440532013000")
            assert "<td class=" not in result.text, \
                "Die Datenbank war zum Start des Tests nicht leer"

            # Prepare File
            content = get_testfile_contents(EXAMPLE_CSV, binary=True)
            files = {'file-input': (io.BytesIO(content), 'commerzbank.csv')}
            # Post File 1
            result = client.post(
                "/api/upload/DE89370400440532013000",
                data=files, content_type='multipart/form-data'
            )

            # Check Response
            assert result.status_code == 201, \
                f"Die Seite hat den Upload nicht wie erwartet verarbeitet: {result.text}"
            assert result.json.get('filename') == 'commerzbank.csv', \
                "Angaben zum Upload wurden nicht gefunden"

            # Post File 2
            files = {'file-input': (io.BytesIO(content), 'commerzbank.csv')}
            result = client.post(
                "/api/upload/DE89370400440532013000",
                data=files, content_type='multipart/form-data'
            )

            # Check Response (same TX: Keine neuen Einträge angelegt)
            assert result.status_code == 200, \
                ("Beim zweiten Upload der gleichen Transaktionen"
                f"dürfen keine neuen Datensätze angelegt werden: {result.text}")

            # Double-Check: Anzahl der Einträge
            result = client.get("/DE89370400440532013000")

            soup = BeautifulSoup(result.text, features="html.parser")
            rows = soup.css.select('table .td-date_tx')

            assert len(rows) == 5, f"Es wurden zu viele Einträge ({len(rows)}) angelegt"


def test_save_meta(test_app):
    """Testet das Speichern Metadaten"""
    with test_app.app_context():

        with test_app.test_client() as client:

            # Parser in MetadaDB schreiben (form)
            parameters = {
                'uuid': '555',
                'name': 'Test Parsing 4 Digits',
                'regex': '[0-9]]{4}'
            }
            result = client.put("/api/saveMeta/parser", json=parameters)
            assert result.status_code == 201, \
                "Der Statuscode war nicht wie erwartet"

            result = result.json
            assert result.get('inserted') == 1, "Es wurde nichts eingefügt"

            # Parser in MetadaDB schreiben (file upload)
            parameters = {
                'uuid': '0987654321',
                'name': 'By File',
                'regex': '[0-5]]{4}'
            }
            parameters = json.dumps(parameters).encode('utf-8')
            files = {'file-input': (io.BytesIO(parameters), 'commerzbank.csv')}
            result = client.post(
                "/api/upload/metadata/parser",
                data=files, content_type='multipart/form-data'
            )
            assert result.status_code == 201, \
                "Der Statuscode war nicht wie erwartet"

            result = result.json
            assert result.get('inserted') == 1, "Es wurde nichts eingefügt"


def test_list_meta(test_app):
    """Testet das Speichern Metadaten"""
    with test_app.app_context():

        with test_app.test_client() as client:

            # Alle Einträge aus MetadatenDB holen
            result = client.get("/api/getMeta/")
            result = result.json
            assert isinstance(result, list), \
                "Die Antwort war keine Liste"
            assert len(result) > 0, \
                "Die Liste war leer"

            # Alle Parser aus MetadatenDB holen
            result = client.get("/api/getMeta/parser")
            result = result.json
            assert isinstance(result, list), \
                "Die Antwort war keine Liste"
            assert len(result) > 0, \
                "Die Liste war leer"

            # Regel mit Namen aus der UserDB holen
            result = client.get("/api/getMeta/555")
            result = result.json
            assert isinstance(result, dict), \
                "Die Antwort war kein Dictionary"
            assert result.get('name') == 'Test Parsing 4 Digits', \
                "Die Regel war nicht wie erwartet"
            assert result.get('regex') == '[0-9]]{4}', \
                "Die Regel war nicht wie erwartet"
            assert result.get('uuid') == '555', \
                "Die Regel war nicht wie erwartet"


def test_get_tx(test_app):
    """Testet den API-Endpoint für die Transaktionsdetails"""
    with test_app.app_context():

        with test_app.test_client() as client:
            # Get Transaction
            result = client.get(
                "/api/DE89370400440532013000/6884802db5e07ee68a68e2c64f9c0cdd"
            )
            assert result.status_code == 200, \
                "Der Statuscode der Transaktion war falsch"

            # Check Content
            result = result.json
            assert result.get('currency') == 'EUR', \
                "Der Inhalt der Testtransaktion wurde nicht wie erwartet selektiert"


def test_tag_stored_rules(test_app):
    """Testet das Tagging über den API Endpunkt:
    - Tagging mit einer definierten Regel
    - Tagging mit allen Default-Regeln
    """
    with test_app.app_context():

        with test_app.test_client() as client:

            # Regel mit Namen aus der SystemDB holen (dry_run)
            parameters = {
                'rule_name': 'Supermarkets',
                'dry_run': True
            }
            result = client.put("/api/tag/DE89370400440532013000", json=parameters)
            result = result.json

            assert result.get('tagged') == 0, \
                f"Trotz 'dry_run' wurden {result.get('tagged')} Einträge getaggt"

            matched_entries = result.get('entries', [])
            assert len(matched_entries) == 2, \
                f"Regel 'Supermarkets' hat {len(matched_entries)} statt 2 Transactionen getroffen"

            # Regel mit Namen aus der UserDB holen (no dry_run)
            parameters = {
                'rule_name': 'City Tax',
                'prio': 2
            }
            result = client.put("/api/tag/DE89370400440532013000", json=parameters)
            result = result.json

            assert result.get('tagged') == 1, \
                f"Ohne 'dry_run' wurden trotzdem nur {result.get('tagged')} Einträge getaggt"

            matched_entries = result.get('entries')
            assert len(matched_entries) == 1, \
                f"Die Regel 'City Tax' hat {len(matched_entries)} statt 1 Transactionen getroffen"


def test_categorize_stored_rules(test_app):
    """Testet das Kategorisieren über den API Endpunkt:
    - Kategorisieren mit einer definierten Regel
    - Kategorisieren mit allen Default-Regeln
    """
    with test_app.app_context():

        with test_app.test_client() as client:

            # Regel mit Namen aus der SystemDB holen (dry_run)
            parameters = {
                'rule_name': 'Abgaben',
                'dry_run': True
            }
            result = client.put("/api/cat/DE89370400440532013000", json=parameters)
            result = result.json

            assert result.get('categorized') == 0, \
                f"Trotz 'dry_run' wurden {result.get('tagged')} Einträge getaggt"

            matched_entries = result.get('entries', [])
            assert len(matched_entries) == 1, \
                f"Regel 'Abgaben' hat {len(matched_entries)} " + \
                "statt 2 Transactionen getroffen"


            # Regel mit Namen aus der UserDB holen (no dry_run)
            parameters = {
                'rule_name': 'Abgaben',
                'prio': 2
            }
            result = client.put("/api/cat/DE89370400440532013000", json=parameters)
            result = result.json

            assert result.get('categorized') == 1, \
                f"Ohne 'dry_run' wurden trotzdem nur {result.get('categorized')} Einträge getaggt"

            matched_entries = result.get('entries')
            assert len(matched_entries) == 1, \
                f"Die Regel 'City Tax' hat {len(matched_entries)} statt 1 Transactionen getroffen"

            # Test 'prio' set correctly
            query = {'key': 'prio', 'compare': '>', 'value': 0}
            result_filtered = test_app.host.db_handler.select(
                "DE89370400440532013000",
                condition=query
            )
            assert len(result_filtered) == 1, \
                f"Falsche Anzahl an Datensätzen mit 'prio': {len(result_filtered)}"            


def test_tag_custom_rules(test_app):
    """Testet das Tagging über den API Endpunkt:
    - Tagging mit einer custom-Regel, die übermittelt wird (mit Treffern)
    - Tagging mit einer custom-Regel, die übermittelt wird (ohne Treffer)
    """
    with test_app.app_context():

        with test_app.test_client() as client:

            # Eigene Regel taggen lassen (niedrige Prio)
            parameters = {
                'tags': ['Supermarkt'],
                'filters': [
                    {'key':'text_tx', 'value': r'EDEKA', 'compare': 'regex'}
                ],
            }
            result = client.put("/api/tag-and-cat/DE89370400440532013000", json=parameters)
            result = result.json

            # Es sollte eine Transaktion zutreffen,
            assert result.get('tagged') == 1, \
                f"Es wurden {result.get('tagged')} statt 1 Einträge getaggt"

            tagged_entries = result.get('entries', [])
            assert len(tagged_entries) == 1, \
                f"Regel hat {len(tagged_entries)} statt 1 Transactionen getroffen"


def test_categorize_custom_rules(test_app):
    """Testet das Kategorisieren über den API Endpunkt:
    - Kategorisieren mit einer custom-Regel, die übermittelt wird (mit Treffern)
    - Kategorisieren mit einer custom-Regel, die übermittelt wird (ohne Treffer)
    """
    with test_app.app_context():

        with test_app.test_client() as client:

            # Eigene Regel kategorisieren lassen (niedrige Prio)
            parameters = {
                'category': "Overwriting Cat",
                'tags': ['Stadt']
            }
            result = client.put("/api/tag-and-cat/DE89370400440532013000", json=parameters)
            result = result.json

            # Es sollte eine Transaktion zutreffen,
            # die wegen zu niedriger Prio nicht selektiert wird
            cat_entries = result.get('entries', [])
            assert len(cat_entries) == 0, \
                f"Regel hat {len(cat_entries)} statt 1 Transactionen getroffen"

            assert result.get('categorized') == 0, \
                f"Es wurden {result.get('categorized')} statt 0 Einträge getaggt"

            # Eigene Regel kategorisieren lassen (hohe Prio)
            parameters = {
                'category': 'Force Overwrite',
                'tags': ['Stadt'],
                'prio': 9,
                'prio_set': 3,
            }
            result = client.put("/api/tag-and-cat/DE89370400440532013000", json=parameters)
            result = result.json

            assert result.get('categorized') == 1, \
                f"Es wurden {result.get('categorized')} statt 1 Eintrag getaggt"
            cat_entries = result.get('entries', [])
            assert len(cat_entries) == 1, \
                f"Die hohe Prio-Regel hat {len(cat_entries)} statt 1 Transactionen getroffen"


def test_tag_manual(test_app):
    """Testet das Tagging über den API Endpunkt:
    - Einem bestimmten Datenbankeintrag ein bestimmtes Tag zuweisen"""
    with test_app.app_context():

        with test_app.test_client() as client:
            new_tag = {
                'tags': ['Test_TAG']
            }
            r = client.put(
                "/api/setManualTag/DE89370400440532013000/6884802db5e07ee68a68e2c64f9c0cdd",
                json=new_tag
            )
            r = r.json
            assert r.get('updated') == 1, "Der Eintrag wurde nicht aktualisiert"

            # Check if new values correct stored
            r = client.get(
                "/api/DE89370400440532013000/6884802db5e07ee68a68e2c64f9c0cdd"
            )
            r = r.json
            assert isinstance(r.get('tags'), list), "Tags wurde nicht als Liste gespeichert"
            assert 'Test_TAG' in r.get('tags', []), \
                "Es wurde ein falsches Tag gespeichert"

            # Add another Tag to the List
            new_tag = {
                'tags': ['Test_Another_SECONDARY']
            }
            r = client.put(
                "/api/setManualTag/DE89370400440532013000/6884802db5e07ee68a68e2c64f9c0cdd",
                json=new_tag
            )
            r = r.json
            assert r.get('updated') == 1, "Der Eintrag wurde nicht erneut aktualisiert"

            # Check if new values correct stored
            r = client.get(
                '/api/DE89370400440532013000/6884802db5e07ee68a68e2c64f9c0cdd'
            )
            r = r.json
            assert isinstance(r.get('tags'), list), "Tags wurde nicht als Liste gespeichert"
            tags = r.get('tags')
            assert 'Test_TAG' in tags and 'Test_Another_SECONDARY' in tags, \
                "Es wurden falsche Tags gespeichert"


def test_categorize_manual(test_app):
    """Testet das Kategorisieren über den API Endpunkt:
    - Einem bestimmten Datenbankeintrag eine bestimmte Kategorie zuweisen"""
    with test_app.app_context():

        with test_app.test_client() as client:
            new_cat = {
                'category': 'Test_CAT'
            }
            r = client.put(
                "/api/setManualCat/DE89370400440532013000/6884802db5e07ee68a68e2c64f9c0cdd",
                json=new_cat
            )
            r = r.json
            assert r.get('updated') == 1, "Der Eintrag wurde nicht aktualisiert"

            # Check if new values correct stored
            r = client.get(
                "/api/DE89370400440532013000/6884802db5e07ee68a68e2c64f9c0cdd"
            )
            r = r.json
            assert 'Test_CAT' == r.get('category'), \
                "Es wurde ein falsches Tag gespeichert"
            assert r.get('prio') == 99, \
                "Die Prio wurde nicht korrekt gesetzt"

def test_tag_manual_multi(test_app):
    """Testet das Tagging über den API Endpunkt:
    - Mehrere Einträge mit bestimmten Tag taggen"""
    with test_app.app_context():

        with test_app.test_client() as client:
            new_tag = {
                'tags': ['Test_SECONDARY_2'],
                't_ids': ["6884802db5e07ee68a68e2c64f9c0cdd",
                          "fdd4649484137572ac642e2c0f34f9af"]
            }
            r = client.put(
                "/api/setManualTags/DE89370400440532013000",
                json=new_tag
            )
            r = r.json
            assert r.get('updated') == 2, "Der Eintrag wurde nicht aktualisiert"

            # Check if new values correct stored
            r = client.get(
                "/api/DE89370400440532013000/6884802db5e07ee68a68e2c64f9c0cdd"
            )
            r1 = r.json
            r = client.get(
                "/api/DE89370400440532013000/fdd4649484137572ac642e2c0f34f9af"
            )
            r2 = r.json
            assert "Test_SECONDARY_2" in r1.get('tags', []) and \
                "Test_SECONDARY_2" in r2.get('tags', []), \
                "Es wurden falsche Tags gespeichert"
            assert "Test_TAG" in r1.get('tags', []), \
                "Das vorherige Tag wurde überschrieben und nicht ergänzt"


def test_categorize_manual_multi(test_app):
    """Testet das Kategorisieren über den API Endpunkt:
    - Mehrere Einträge mit bestimmten Kategorie kategorisieren"""
    with test_app.app_context():

        with test_app.test_client() as client:
            new_cat = {
                'category': 'Multi-Category',
                't_ids': ["6884802db5e07ee68a68e2c64f9c0cdd",
                          "fdd4649484137572ac642e2c0f34f9af"]
            }
            r = client.put(
                "/api/setManualCats/DE89370400440532013000",
                json=new_cat
            )
            r = r.json
            assert r.get('updated') == 2, "Der Eintrag wurde nicht aktualisiert"

            # Check if new values correct stored
            r = client.get(
                "/api/DE89370400440532013000/fdd4649484137572ac642e2c0f34f9af"
            )
            r = r.json
            assert 'Multi-Category' == r.get('category'), \
                "Es wurde eine falsche Kategorie gespeichert"
            assert r.get('prio') == 99, \
                "Die Prio wurde nicht korrekt gesetzt"


def test_remove_category(test_app):
    """Testet das Entfernen einer Kategorie.
    Alle anderen Einträge zur Transaktion bleiben erhalten."""
    with test_app.app_context():

        with test_app.test_client() as client:
            # Remove Cat
            result = client.put(
                "/api/removeCat/DE89370400440532013000/fdd4649484137572ac642e2c0f34f9af"
            )
            result = result.json
            assert result.get('updated') == 1, \
                "Die Kategorie wurde nicht entfernt"

            # Check if new values correct stored
            result = client.get(
                "/api/DE89370400440532013000/fdd4649484137572ac642e2c0f34f9af"
            )
            result = result.json
            assert result.get('category') is None, \
                "Der Kategorie wurde nicht entfernt"
            assert result.get('tags'), \
                "Die Tags wurden fälschlicherweise entfernt"
            assert result.get('prio') == 0, \
                "Die Prio wurde nicht geändert"


def test_remove_tag(test_app):
    """Testet das Entfernen aller Tags eines Eintrages.
    Alle anderen Einträge zur Transaktion bleiben erhalten."""
    with test_app.app_context():

        with test_app.test_client() as client:
            # Remove Tag
            result = client.put(
                "/api/removeTag/DE89370400440532013000/6884802db5e07ee68a68e2c64f9c0cdd"
            )
            result = result.json
            assert result.get('updated') == 1, \
                "Der Tag wurde nicht entfernt"

            # Check if new values correct stored
            result = client.get(
                "/api/DE89370400440532013000/6884802db5e07ee68a68e2c64f9c0cdd"
            )
            result = result.json
            assert result.get('category') is not None, \
                "Der Kategorie wurde fälschlicherweise entfernt"
            assert not result.get('tags'), \
                "Die Tags wurden nicht entfernt"
            assert result.get('prio') == 99, \
                "Die Prio wurde geändert"


def test_remove_tag_multi(test_app):
    """Testet das Entfernen aller Tags mehrerer Einträge.
    Alle anderen Einträge zur Transaktion bleiben erhalten."""
    with test_app.app_context():

        with test_app.test_client() as client:
            # Remove Tag
            result = client.put(
                "/api/removeTags/DE89370400440532013000",
                json={
                    't_ids': ["786e1d4e16832aa321a0176c854fe087",
                              "fdd4649484137572ac642e2c0f34f9af"]
                }
            )
            result = result.json
            assert result.get('updated') == 2, \
                "Die Tags wurde nicht entfernt"

            # Check if new values correct stored
            result = client.get(
                "/api/DE89370400440532013000/786e1d4e16832aa321a0176c854fe087"
            )
            result = result.json
            assert result.get('category') is not None, \
                "Der Kategorie wurde fälschlicherweise entfernt"
            assert not result.get('tags'), \
                "Die Tags wurden nicht entfernt"
            assert result.get('prio') != 0, \
                "Die Prio wurde geändert"
