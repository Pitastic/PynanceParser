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
            result = client.delete(f'/api/truncateDatabase/{test_app.config['IBAN']}')
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
            result = client.get(f"/{test_app.config['IBAN']}")
            assert "<td class=" not in result.text, \
                "Die Datenbank war zum Start des Tests nicht leer"

            # Visit Form
            result = client.get('/')
            assert result.status_code == 200, "Der Statuscode der Startseite war falsch"
            assert 'Message Box' in result.text, \
                "Special Heading not found in the response"

            # Prepare File
            content = get_testfile_contents(EXAMPLE_CSV, binary=True)
            files = {'input_file': (io.BytesIO(content), 'commerzbank.csv')}
            # Post File
            result = client.post(
                f"/api/upload/{test_app.config['IBAN']}",
                data=files, content_type='multipart/form-data'
            )

            # Check Response
            assert result.status_code == 201, \
                f"Die Seite hat den Upload nicht wie erwartet verarbeitet: {result.text}"
            assert result.json.get('filename') == 'commerzbank.csv', \
                "Angaben zum Upload wurden nicht gefunden"

            # Aufruf der Transaktionen auf verschiedene Weisen
            response1 = client.get("/")
            response2 = client.get(f"/{test_app.config['IBAN']}")
            assert response1.status_code == response2.status_code == 200, \
                "Die Ergebnisseite mit den Transaktionen ist nicht (richtig) erreichbar"
            assert response2.text == response1.text, \
                "Der Aufruf des DEFAULT Kontos aus der Konfig ist nicht richtig"

        # -- Check Parsing --
        soup = BeautifulSoup(response1.text, features="html.parser")

        # 1. Example
        tx_hash = 'cf1fb4e6c131570e4f3b2ac857dead40'
        row1 = soup.css.select(f'#tr-{tx_hash}')
        assert len(row1) == 1, \
            f"Es wurden {len(row1)} rows für das erste Beispiel gefunden"

        content = row1[0].css.filter('.td-betrag')[0].contents[0]
        assert content == '-11.63', \
            f"Der Content von {tx_hash} ist anders als erwartet: '{content}'"

        # 2. Example
        tx_hash = '786e1d4e16832aa321a0176c854fe087'
        row2 = soup.css.select(f'#tr-{tx_hash}')
        assert len(row2) == 1, \
            f"Es wurden {len(row2)} rows für das zweite Beispiel gefunden"

        content = row2[0].css.filter('.td-betrag')[0].contents[0]
        assert content == '-221.98', \
            f"Der Content von {tx_hash} / 'betrag' ist anders als erwartet: '{content}'"

        content = [child.contents[0] for child in row2[0].select('.td-parsed p')]
        assert 'Mandatsreferenz' in content, \
            f"Der Content von {tx_hash} / 'parsed' ist anders als erwartet: '{content}'"


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

            result = client.get(f"/{test_app.config['IBAN']}")
            assert result.status_code == 200, "Der Statuscode der IBAN war falsch"


def test_double_upload(test_app):
    """Lädt zwei Dateien hoch und prüft die unterschiedlichen HTTP Stati"""
    test_truncate(test_app)
    with test_app.app_context():
        # Clear DB

        with test_app.test_client() as client:
            # Cleared DB ?
            result = client.get(f"/{test_app.config['IBAN']}")
            assert "<td class=" not in result.text, \
                "Die Datenbank war zum Start des Tests nicht leer"

            # Prepare File
            content = get_testfile_contents(EXAMPLE_CSV, binary=True)
            files = {'input_file': (io.BytesIO(content), 'commerzbank.csv')}
            # Post File 1
            result = client.post(
                f"/api/upload/{test_app.config['IBAN']}",
                data=files, content_type='multipart/form-data'
            )

            # Check Response
            assert result.status_code == 201, \
                f"Die Seite hat den Upload nicht wie erwartet verarbeitet: {result.text}"
            assert result.json.get('filename') == 'commerzbank.csv', \
                "Angaben zum Upload wurden nicht gefunden"

            # Post File 2
            files = {'input_file': (io.BytesIO(content), 'commerzbank.csv')}
            result = client.post(
                f"/api/upload/{test_app.config['IBAN']}",
                data=files, content_type='multipart/form-data'
            )

            # Check Response (same TX: Keine neuen Einträge angelegt)
            assert result.status_code == 200, \
                ("Beim zweiten Upload der gleichen Transaktionen"
                f"dürfen keine neuen Datensätze angelegt werden: {result.text}")

            # Double-Check: Anzahl der Einträge
            result = client.get(f"/{test_app.config['IBAN']}")

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
            result = client.post("/api/saveMeta/parser", json=parameters)
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
            files = {'input_file': (io.BytesIO(parameters), 'commerzbank.csv')}
            result = client.post(
                "/api/saveMeta/",
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


def test_tag_stored(test_app):
    """Testet das Tagging, wenn es über den API Endpoint angesprochen wird"""
    with test_app.app_context():

        with test_app.test_client() as client:

            # Regel mit Namen aus der SystemDB holen (dry_run)
            parameters = {
                'rule_name': 'Supermarkets',
                'dry_run': True,
                'prio': 2
            }
            result = client.put(f"/api/tag/{test_app.config['IBAN']}", json=parameters)
            result = result.json

            assert result.get('tagged') == 0, \
                f"Trotz 'dry_run' wurden {result.get('tagged')} Einträge getaggt"

            tagged_entries = result.get('entries', [])
            assert len(tagged_entries) == 2, \
                f"Regel 'Supermarkets' hat {len(tagged_entries)} statt 2 Transactionen getroffen"

            # Regel mit Namen aus der UserDB holen (no dry_run)
            parameters = {
                'rule_name': 'City Tax',
                'prio': 2
            }
            result = client.put(f"/api/tag/{test_app.config['IBAN']}", json=parameters)
            result = result.json

            assert result.get('tagged') == 1, \
                f"Ohne 'dry_run' wurden trotzdem nur {result.get('tagged')} Einträge getaggt"

            tagged_entries = result.get('City Tax', {}).get('entries')
            assert len(tagged_entries) == 1, \
                f"Die Regel 'City Tax' hat {len(tagged_entries)} statt 1 Transactionen getroffen"

            # Test 'prio' set correctly
            query = {'key': 'prio', 'compare': '>', 'value': 0}
            result_filtered = test_app.host.db_handler.select(
                test_app.config['IBAN'],
                condition=query
            )
            assert len(result_filtered) == 1, \
                f"Falsche Anzahl an Datensätzen mit 'prio': {len(result_filtered)}"


def test_own_rules(test_app):
    """Eigene Regeln übermitteln; mit und ohne Treffer"""
    with test_app.app_context():

        with test_app.test_client() as client:

            # Eigene Regel taggen lassen (niedrige Prio)
            parameters = {
                'rule_name': 'My low Rule',
                'rule_category': 'Lebensmittel',
                'rule_tags': ['Supermarkt'],
                'rule_regex': r'EDEKA',
                'prio': 0,
            }
            result = client.put(f"/api/tag/{test_app.config['IBAN']}", json=parameters)
            result = result.json

            # Es sollte eine Transaktion zutreffen,
            # die wegen zu niedriger Prio nicht selektiert wird
            assert result.get('tagged') == 0, \
                f"Es wurden {result.get('tagged')} statt 0 Einträge im dry_run getaggt"

            tagged_entries = result.get('entries', [])
            assert len(tagged_entries) == 0, \
                f"Regel 'My low Rule' hat {len(tagged_entries)} statt 0 Transactionen getroffen"

            # Eigene Regel taggen lassen (hohe Prio)
            parameters = {
                'rule_name': 'My high Rule',
                'rule_category': 'Haus',
                'rule_tags': ['Garten'],
                'rule_regex': r'\sGARTEN\w',
                'prio': 9,
                'prio_set': 3,
            }
            result = client.put(f"/api/tag/{test_app.config['IBAN']}", json=parameters)
            result = result.json

            assert result.get('tagged') == 1, \
                f"Es wurden {result.get('tagged')} statt 1 Eintrag getaggt"
            tagged_entries = result.get('entries', [])
            assert len(tagged_entries) == 1, \
                f"DRegel 'My high Rule' hat {len(tagged_entries)} statt 1 Transactionen getroffen"


def test_manual_tagging(test_app):
    """Einem bestimmten Datenbankeintrag eine Kategorie zuweisen"""
    with test_app.app_context():

        with test_app.test_client() as client:
            new_tag = {
                'category': 'Tets_PRIMARY',
                'tags': ['Test_SECONDARY']
            }
            r = client.put(
                f"/api/setManualTag/{test_app.config['IBAN']}/6884802db5e07ee68a68e2c64f9c0cdd",
                json=new_tag
            )
            r = r.json
            assert r.get('updated') == 1, "Der Eintrag wurde nicht aktualisiert"

            # Check if new values correct stored
            r = client.get(
                f'/api/{test_app.config['IBAN']}/6884802db5e07ee68a68e2c64f9c0cdd'
            )
            r = r.json
            assert isinstance(r.get('tags'), list), "Tags wurde nicht als Liste gespeichert"
            assert r.get('tags') == ['Garten', 'Test_SECONDARY'], \
                "Es wurde ein falsches Tag gespeichert"

            # Add another Tag to the List
            new_tag = {
                'tags': ['Test_Another_SECONDARY']
            }
            r = client.put(
                f"/api/setManualTag/{test_app.config['IBAN']}/6884802db5e07ee68a68e2c64f9c0cdd",
                json=new_tag
            )
            r = r.json
            assert r.get('updated') == 1, "Der Eintrag wurde nicht erneut aktualisiert"

            # Check if new values correct stored
            r = client.get(
                f'/api/{test_app.config['IBAN']}/6884802db5e07ee68a68e2c64f9c0cdd'
            )
            r = r.json
            assert isinstance(r.get('tags'), list), "Tags wurde nicht als Liste gespeichert"
            tags = r.get('tags')
            assert 'Test_SECONDARY' in tags and 'Test_Another_SECONDARY' in tags, \
                "Es wurden falsche Tags gespeichert"


def test_manual_multi_tagging(test_app):
    """Mehrere Einträge mit bestimmter Kategorie taggen"""
    with test_app.app_context():

        with test_app.test_client() as client:
            new_tag = {
                'category': 'Tets_PRIMARY_2',
                'tags': ['Test_SECONDARY_2'],
                't_ids': ["6884802db5e07ee68a68e2c64f9c0cdd",
                          "fdd4649484137572ac642e2c0f34f9af"]
            }
            r = client.put(
                f"/api/setManualTags/{test_app.config['IBAN']}",
                json=new_tag
            )
            r = r.json
            assert r.get('updated') == 2, "Der Eintrag wurde nicht aktualisiert"


def test_get_tx(test_app):
    """Testet den API-Endpoint für die Transaktionsdetails"""
    with test_app.app_context():

        with test_app.test_client() as client:
            # Get Transaction
            result = client.get(
                f"/api/{test_app.config['IBAN']}/6884802db5e07ee68a68e2c64f9c0cdd"
            )
            assert result.status_code == 200, \
                "Der Statuscode der Transaktion war falsch"

            # Check Content
            result = result.json
            assert result.get('category') == 'Tets_PRIMARY_2', \
                "Der Primary Tag war nicht wie erwartet"

def test_remove_tag(test_app):
    """Testet das Entfernen eines Tags"""
    with test_app.app_context():

        with test_app.test_client() as client:
            # Remove Tag
            result = client.put(
                f"/api/removeTag/{test_app.config['IBAN']}/6884802db5e07ee68a68e2c64f9c0cdd"
            )
            result = result.json
            assert result.get('updated') == 1, \
                "Der Tag wurde nicht entfernt"
            assert not result.get('category'), \
                "Der Kategorie war nicht wie erwartet"
            assert not result.get('tags'), \
                "Die Tags waren nicht wie erwartet"
            assert not result.get('prio'), \
                "Die Prio war nicht wie erwartet"
