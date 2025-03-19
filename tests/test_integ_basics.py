#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisc Module for easy Imports and Methods"""

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
            result = client.get('/truncateDatabase/')
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
            result = client.get(f"/view/{test_app.config['IBAN']}")
            assert "<td class=" not in result.text, \
                "Die Datenbank war zum Start des Tests nicht leer"

            # Visit Form
            result = client.get('/')
            assert result.status_code == 200, "Der Statuscode der Startseite war falsch"
            assert 'type="submit"' in result.text, \
                "Submit button not found in the response"

            # Prepare File
            content = get_testfile_contents(EXAMPLE_CSV, binary=True)
            files = {'tx_file': (io.BytesIO(content), 'commerzbank.csv')}
            # Post File
            result = client.post("/upload", data=files, content_type='multipart/form-data')

            # Check Response
            assert result.status_code == 201, \
                "Die Seite hat den Upload nicht wie erwartet verarbeitet"
            assert 'tx_file filename: commerzbank.csv' in result.text, \
                "Angaben zum Upload wurden nicht gefunden"

            # Aufruf der Transaktionen auf verschiedene Weisen
            response1 = client.get("/view/")
            response2 = client.get(f"/view/{test_app.config['IBAN']}")
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
        assert content == '-11.63 EUR', \
            f"Der Content von {tx_hash} ist anders als erwartet: '{content}'"

        # 2. Example
        tx_hash = '786e1d4e16832aa321a0176c854fe087'
        row2 = soup.css.select(f'#tr-{tx_hash}')
        assert len(row2) == 1, \
            f"Es wurden {len(row2)} rows für das zweite Beispiel gefunden"

        content = row2[0].css.filter('.td-betrag')[0].contents[0]
        assert content == '-221.98 EUR', \
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

            #/view
            result = client.get('/view/')
            assert result.status_code == 200, "Der Statuscode der Ansicht war falsch"

            result = client.get(f"/view/{test_app.config['IBAN']}")
            assert result.status_code == 200, "Der Statuscode der IBAN war falsch"


def test_double_upload(test_app):
    """Lädt zwei Dateien hoch und prüft die unterschiedlichen HTTP Stati"""
    test_truncate(test_app)
    with test_app.app_context():
        # Clear DB

        with test_app.test_client() as client:
            # Cleared DB ?
            result = client.get(f"/view/{test_app.config['IBAN']}")
            assert "<td class=" not in result.text, \
                "Die Datenbank war zum Start des Tests nicht leer"

            # Prepare File
            content = get_testfile_contents(EXAMPLE_CSV, binary=True)
            files = {'tx_file': (io.BytesIO(content), 'commerzbank.csv')}
            # Post File 1
            result = client.post("/upload", data=files, content_type='multipart/form-data')

            # Check Response
            assert result.status_code == 201, \
                "Die Seite hat den Upload nicht wie erwartet verarbeitet"
            assert 'tx_file filename: commerzbank.csv' in result.text, \
                "Angaben zum Upload wurden nicht gefunden"

            # Post File 2
            files = {'tx_file': (io.BytesIO(content), 'commerzbank.csv')}
            result = client.post("/upload", data=files, content_type='multipart/form-data')

            # Check Response (same TX: Keine neuen Einträge angelegt)
            assert result.status_code == 200, \
                ("Beim zweiten Upload der gleichen Transaktionen"
                "dürfen keine neuen Datensätze angelegt werden")

            # Double-Check: Anzahl der Einträge
            result = client.get(f"/view/{test_app.config['IBAN']}")

            soup = BeautifulSoup(result.text, features="html.parser")
            rows = soup.css.select('table .td-uuid')

            assert len(rows) == 5, f"Es wurden zu viele Einträge ({len(rows)}) angelegt"


def test_tag_stored(test_app):
    """Testet das Tagging, wenn es über den API Endpoint angesprochen wird"""
    with test_app.app_context():

        with test_app.test_client() as client:

            # Regel mit Namen aus der SystemDB holen
            parameters = {
                'rule_name': 'Supermarkets',
                'dry_run': True,
                'prio': 2
            }
            result = client.post("/tag", json=parameters)
            result = result.json

            assert result.get('tagged') == 0, \
                f"Trotz 'dry_run' wurden {result.get('tagged')} Einträge getaggt"

            tagged_entries = result.get('Supermarkets', {}).get('entries')
            assert len(tagged_entries) == 2, \
                f"Regel 'Supermarkets' hat {len(tagged_entries)} statt 2 Transactionen getroffen"

            # Regel mit Namen aus der UserDB holen
            parameters = {
                'rule_name': 'City Tax',
                'dry_run': True,
                'prio': 2
            }
            result = client.post("/tag", json=parameters)
            result = result.json

            assert result.get('tagged') == 0, \
                f"Trotz 'dry_run' wurden {result.get('tagged')} Einträge getaggt"

            tagged_entries = result.get('City Tax', {}).get('entries')
            assert len(tagged_entries) == 1, \
                f"Die Regel 'City Tax' hat {len(tagged_entries)} statt 1 Transactionen getroffen"


def test_own_rules(test_app):
    """Eigene Regeln übermitteln; mit und ohne Treffer"""
    with test_app.app_context():

        with test_app.test_client() as client:

            # Eigene Regel taggen lassen (niedrige Prio)
            parameters = {
                'rule_name': 'My low Rule',
                'rule_primary': 'Lebensmittel',
                'rule_secondary': 'Supermarkt',
                'rule_regex': r'EDEKA',
                'prio': 0,
                'dry_run': False
            }
            result = client.post("/tag", json=parameters)
            result = result.json

            # Es sollte eine Transaktion zutreffen,
            # die wegen zu niedriger Prio nicht selektiert wird
            assert result.get('tagged') == 0, \
                f"Es wurden {result.get('tagged')} statt 0 Einträge im dry_run getaggt"

            tagged_entries = result.get('My low Rule').get('entries')
            assert len(tagged_entries) == 0, \
                f"Regel 'My low Rule' hat {len(tagged_entries)} statt 0 Transactionen getroffen"

            # Eigene Regel taggen lassen (hohe Prio)
            parameters = {
                'rule_name': 'My high Rule',
                'rule_primary': 'Haus',
                'rule_secondary': 'Garten',
                'rule_regex': r'\sGARTEN\w',
                'prio': 9,
                'prio_set': 3,
                'dry_run': False
            }
            result = client.post("/tag", json=parameters)
            result = result.json

            assert result.get('tagged') == 1, \
                f"Es wurden {result.get('tagged')} statt 1 Eintrag getaggt"
            tagged_entries = result.get('My high Rule', {}).get('entries')
            assert len(tagged_entries) == 1, \
                f"DRegel 'My high Rule' hat {len(tagged_entries)} statt 1 Transactionen getroffen"
