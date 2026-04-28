#!/usr/bin/python3 # pylint: disable=invalid-name
"""Testmodul für die Filterung von Transaktionen"""

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
    'input_commerzbank.csv'
)


def test_truncate_and_upload(test_app):
    """Leert die Datenbank und lädt Beispieldaten hoch"""
    with test_app.app_context():

        with test_app.test_client() as client:
            result = client.delete("/api/deleteDatabase/DE89370400440532013000")
            assert result.status_code == 200, "Fehler beim Leeren der Datenbank"

            # Prepare File
            content = get_testfile_contents(EXAMPLE_CSV, binary=True)
            files = {
                'file-batch': (io.BytesIO(content), 'input_commerzbank.csv'),
                'bank': 'Commerzbank'
            }
            # Post File
            result = client.post(
                "/api/upload/DE89370400440532013000",
                data=files, content_type='multipart/form-data'
            )

            # Check Response
            assert result.status_code == 201, \
                f"Die Seite hat den Upload nicht wie erwartet verarbeitet: {result.text}"
            assert result.json.get('filename') == 'input_commerzbank.csv', \
                "Angaben zum Upload wurden nicht gefunden"

            # Add Tags ("786e1d4e16832aa321a0176c854fe087" : ohne Tags)
            new_tag = {
                'tags': ['TestTag1', 'TestTag2'],
                't_ids': ["6884802db5e07ee68a68e2c64f9c0cdd",
                          "fdd4649484137572ac642e2c0f34f9af"]
            }
            r = client.put(
                "/api/setManualTags/DE89370400440532013000",
                json=new_tag
            )
            r = r.json
            assert r.get('updated') == 2, "Der Eintrag wurde nicht aktualisiert"

            new_tag = {
                'tags': ['TestTag2'],
                't_ids': ["524a0184ca2ba4a5e438f362da95cffc"]
            }
            r = client.put(
                "/api/setManualTags/DE89370400440532013000",
                json=new_tag
            )
            r = r.json
            assert r.get('updated') == 1, "Der Eintrag wurde nicht aktualisiert"

            new_tag = {
                'tags': ['TestTag1', 'TestTag3', 'TestTag4'],
                't_ids': ["cf1fb4e6c131570e4f3b2ac857dead40"]
            }
            r = client.put(
                "/api/setManualTags/DE89370400440532013000",
                json=new_tag
            )
            r = r.json
            assert r.get('updated') == 1, "Der Eintrag wurde nicht aktualisiert"


def test_iban_filtering_tags_in(test_app):
    """Tag-Filter: in """
    with test_app.app_context():

        with test_app.test_client() as client:

            # in
            result = client.get(r"/DE89370400440532013000?tags=TestTag1%2CTestTag3&tag_mode=in")
            soup = BeautifulSoup(result.text, features="html.parser")
            rows = soup.css.select('table.transactions tr[name] td input.row-checkbox')
            assert result.status_code == 200, \
                "Die Ergebnisseite mit den Transaktionen ist nicht (richtig) erreichbar"
            assert len(rows) == 3, \
                f"Es wurden {len(rows)} Einträge gefunden, statt der erwarteten 4"


def test_iban_filtering_tags_notin(test_app):
    """Tag-Filter: not-in """
    with test_app.app_context():

        with test_app.test_client() as client:

            result = client.get(r"/DE89370400440532013000?tags=TestTag1%2CTestTag3&tag_mode=notin")
            soup = BeautifulSoup(result.text, features="html.parser")
            rows = soup.css.select('table.transactions tr[name] td input.row-checkbox')
            assert result.status_code == 200, \
                "Die Ergebnisseite mit den Transaktionen ist nicht (richtig) erreichbar"
            assert len(rows) == 2, \
                f"Es wurden {len(rows)} Einträge gefunden, statt der erwarteten 1"


def test_iban_filtering_tags_all(test_app):
    """Tag-Filter: all """
    with test_app.app_context():

        with test_app.test_client() as client:

            # all
            result = client.get(
                r"/DE89370400440532013000?tags=TestTag1%2CTestTag3%2CTestTag4&tag_mode=all")
            soup = BeautifulSoup(result.text, features="html.parser")
            rows = soup.css.select('table.transactions tr[name] td input.row-checkbox')
            assert result.status_code == 200, \
                "Die Ergebnisseite mit den Transaktionen ist nicht (richtig) erreichbar"
            assert len(rows) == 1, \
                f"Es wurden {len(rows)} Einträge gefunden, statt der erwarteten 1"


def test_iban_filtering_tags_equal(test_app):
    """Tag-Filter: exact (==) """
    with test_app.app_context():

        with test_app.test_client() as client:

            # exact (== no tags)
            result = client.get(
                r"/DE89370400440532013000?tags=&tag_mode=exact")
            soup = BeautifulSoup(result.text, features="html.parser")
            rows = soup.css.select('table.transactions tr[name] td input.row-checkbox')
            assert result.status_code == 200, \
                "Die Ergebnisseite mit den Transaktionen ist nicht (richtig) erreichbar"
            assert len(rows) == 1, \
                f"Es wurden {len(rows)} Einträge gefunden, statt der erwarteten 1"

            # exact (==)
            result = client.get(
                r"/DE89370400440532013000?tags=TestTag1%2CTestTag2&tag_mode=exact")
            soup = BeautifulSoup(result.text, features="html.parser")
            rows = soup.css.select('table.transactions tr[name] td input.row-checkbox')
            assert result.status_code == 200, \
                "Die Ergebnisseite mit den Transaktionen ist nicht (richtig) erreichbar"
            assert len(rows) == 2, \
                f"Es wurden {len(rows)} Einträge gefunden, statt der erwarteten 2"

            result = client.get(
                r"/DE89370400440532013000?tags=TestTag1%2CTestTag3&tag_mode=exact")
            soup = BeautifulSoup(result.text, features="html.parser")
            rows = soup.css.select('table.transactions tr[name] td input.row-checkbox')
            assert result.status_code == 200, \
                "Die Ergebnisseite mit den Transaktionen ist nicht (richtig) erreichbar"
            assert len(rows) == 0, \
                f"Es wurden {len(rows)} Einträge gefunden, statt der erwarteten 0"

