#!/usr/bin/python3 # pylint: disable=invalid-name
"""
Testmodul für die Funktionen des Taggers.
(Erfolgreiche Tests der DB Handler sind erforderlich)
"""

import os
import sys
import json
import pytest

# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper import MockDatabase
from handler.Tags import Tagger


# Test Tagging-Ruleset hinterlegen
RULESET = {
    "Supermarkets" : {
        "name": "Supermarkets",
        "metatype": "rule",
        "category": "Lebenserhaltungskosten",
        "subcategory": "Supermarkt",
        "tags": ["Lebensmittel"],
        "regex": r"(EDEKA|Wucherpfennig|Penny|Aldi|Kaufland|netto)"
    },
    "City Tax": {
        "name": "City Tax",
        "metatype": "rule",
        "category": "Haus und Grund",
        "subcategory": "Abgaben",
        "tags": ["Stadtabgaben"],
        "parsed": {
            "multi": "AND",
            "query": {
                'Gläubiger-ID': r'DE7000100000077777'
            }
        }
    }
}

def test_parsing_regex(test_app):
    """Testet das Parsen der Datensätze mit den fest hinterlegten RegExes"""
    with test_app.app_context():
        tagger = Tagger(MockDatabase())

        # Fake Daten laden
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'commerzbank.json'
        )
        with open(path, 'rb') as test_data:
            data = json.load(test_data)

        assert data, "Test Kontoumsätze konnten nicht geladen werden"
        parsed_data = tagger.parse(data)

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

def test_regex(test_app):
    """Testet das Kategorisieren der Datensätze mit fest hinterlegten Regeln.
    Berücksichtigt alle Umsätze ohne Kategorie"""
    with test_app.app_context():
        tagger = Tagger(MockDatabase())
        tagging_result = tagger.tag_regex(ruleset=RULESET)

        assert tagging_result.get('tagged') == 3, \
            "Die Regeln haben nicht die richtige Anzahl an Einträgen getroffen"

def test_regex_untagged(test_app):
    """Testet das Kategorisieren der Datensätzemit fest hinterlegten Regeln.
    Berücksichtigt alle Umsätze nud überschreibt auch vorhandene Kategorien."""
    with test_app.app_context():
        # prio auf 4 aber override auf 1
        tagger = Tagger(MockDatabase())
        tagging_result = tagger.tag_regex(ruleset=RULESET, dry_run=True, prio=1, prio_set=9)

        assert tagging_result.get('tagged') == 0, \
            "Die Option dry_run hat trotzdem Datensätze verändert"
        # Treffer insgesamt für alle Regeln zählen
        assert len(tagging_result.get('entries')) == 3, \
            "Die Regel 'City Tax' hat nicht die richtige Anzahl an Einträgen getroffen"

@pytest.mark.skip(reason="Currently not implemented yet")
def test_regex_custom():
    """Testet das Kategorisieren der Datensätze mit Regeln,
    die vom Benutzer hinterlegt worden sind"""
    return


def test_ai_guess(test_app):
    """Prüft zunächst, ob die Methode für das KI Tagging die
    richtigen Datensätze selektiert und ein Guess hinterlässt"""
    with test_app.app_context():
        tagger = Tagger(MockDatabase())
        tagging_result = tagger.tag_ai(dry_run=True)
        assert tagging_result.get('guessed') == 0, \
            "Die Option dry_run hat trotzdem Datensätze verändert"
        assert len(tagging_result.get('ai').get('entries')) == 5, \
            "Die Methode hat nicht die richtige Anzahl an Einträgen getroffen"
