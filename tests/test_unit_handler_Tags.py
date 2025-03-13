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

from handler.Tags import Tagger


# Test Tagging-Ruleset hinterlegen
RULESET = {
    'Supermarkets': {
        'primary': 'Lebenserhaltungskosten',
        'secondary': 'Lebensmittel',
        'regex': r"(EDEKA|Wucherpfennig|Penny|Aldi|Kaufland|netto)",
    },
    'City Tax': {
        'primary': 'Haus und Grund',
        'secondary': 'Stadtabgaben',
        'parsed': {
            'Gläubiger-ID': r'DE7000100000077777'
        },
    }
}


def test_parsing_regex(mocked_db):
    """Testet das Parsen der Datensätze mit den fest hinterlegten RegExes"""
    with mocked_db.app_context():
        tagger = Tagger()

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

def test_regex(mocked_db):
    """Testet das Kategorisieren der Datensätze mit fest hinterlegten Regeln.
    Berücksichtigt alle Umsätze ohne Kategorie"""
    with mocked_db.app_context():
        tagger = Tagger()
        tagging_result = tagger.tag_regex(mocked_db.host.db_handler, ruleset=RULESET)

        assert tagging_result.get('Supermarkets').get('tagged') == 2, \
            "Die Regel 'Supermarkets' hat nicht die richtige Anzahl an Einträgen getroffen"
        assert tagging_result.get('City Tax').get('tagged') == 1, \
            "Die Regel 'City Tax' hat nicht die richtige Anzahl an Einträgen getroffen"

def test_regex_untagged(mocked_db):
    """Testet das Kategorisieren der Datensätzemit fest hinterlegten Regeln.
    Berücksichtigt alle Umsätze nud überschreibt auch vorhandene Kategorien."""
    with mocked_db.app_context():
        # prio auf 4 aber override auf 1
        tagger = Tagger()
        tagging_result = tagger.tag_regex(mocked_db.host.db_handler, ruleset=RULESET,
                                          dry_run=True, prio=9, prio_set=1)

        assert tagging_result.get('tagged') == 0, \
            "Die Option dry_run hat trotzdem Datensätze verändert"
        assert len(tagging_result.get('Supermarkets').get('entries')) == 2, \
            "Die Regel 'Supermarkets' hat nicht die richtige Anzahl an Einträgen getroffen"
        assert len(tagging_result.get('City Tax').get('entries')) == 1, \
            "Die Regel 'City Tax' hat nicht die richtige Anzahl an Einträgen getroffen"

@pytest.mark.skip(reason="Currently not implemented yet")
def test_regex_custom():
    """Testet das Kategorisieren der Datensätze mit Regeln,
    die vom Benutzer hinterlegt worden sind"""
    return

@pytest.mark.skip(reason="Currently not implemented yet")
def test_ai():
    """Testet das Kategorisieren der Datensätze mit Hilfe der KI"""
    return
