#!/usr/bin/python3 # pylint: disable=invalid-name
"""
Testmodul für die Funktionen des Taggers.
(Erfolgreiche Tests der DB Handler sind erforderlich)
"""

import copy
import os
import sys
import json


# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper import MockDatabase
from handler.Tags import Tagger


def test_parsing_regex(test_app):
    """Testet das Parsen der Datensätze mit den fest hinterlegten RegExes"""
    with test_app.app_context():
        tagger = Tagger(MockDatabase())

        # Fake Daten laden
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'input_commerzbank.json'
        )
        with open(path, 'rb') as test_data:
            data = json.load(test_data)

        assert data, "Test Kontoumsätze konnten nicht geladen werden"
        parsed_data = tagger.parse(data)

        # Check if specific entries were tagged
        for i, entry in enumerate(parsed_data):

            if entry.get('date_tx') == 1672876800 and entry.get('amount') == -221.98:

                # Eintrag mit Gläubiger-ID und Mandatsreferenz
                assert entry.get('parsed').get('Mandatsreferenz'), \
                    f"Die Mandatsreferenz wurde in Eintrag {i} nicht erkannt: {entry}"
                assert entry.get('parsed').get('Gläubiger-ID'), \
                    f"Die Gläubiger-ID wurde in Eintrag {i} nicht erkannt: {entry}"

            else:
                assert not entry.get('parsed'), \
                    f"In Eintrag {i} gab es False-Positives"


def test_categorize(test_app):
    """Testet das Kategorisieren einzelner Datensätze"""
    with test_app.app_context():
        tagger = Tagger(MockDatabase())
        mocker_result = tagger.categorize(iban="DE89370400440532013000")
        assert mocker_result.get('entries') == ['test_categorize'], \
            "Result does not match with Mocker Fake"


def test_tag(test_app):
    """Testet das vergeben von Tags an einzelne Datensätze"""
    with test_app.app_context():
        tagger = Tagger(MockDatabase())
        mocker_result = tagger.tag(iban="DE89370400440532013000")
        print("Mocker Result:", mocker_result)
        assert 'test_tag' in mocker_result.get('entries') and \
            'test_tag2' in mocker_result.get('entries'), \
            "Result does not match with Mocker Fake"



def test_tag_and_cat(test_app):
    """Testet den ganzen Ablauf mit automatischem Tagging und Kategorisierung"""
    with test_app.app_context():
        tagger = Tagger(MockDatabase())

        # AI Tagging
        mocker_result = tagger.tag_and_cat(iban="DE89370400440532013000", rule_name='ai')
        assert mocker_result.get('entries') == [
            'b5aaffc31fa63a466a8b55962995ebcc', 'test_categorize'], \
                "Result does not match with Mocker Fake"

        # Normal Tagging
        mocker_result = tagger.tag_and_cat(iban="DE89370400440532013000")
        assert 'test_tag' in mocker_result.get('entries') and \
            'test_tag2' in mocker_result.get('entries') and \
            'test_categorize' in mocker_result.get('entries'), \
            "Result does not match with Mocker Fake"


def test_tag_or_cat_custom(test_app):
    """Testet das Kategorisieren und Taggen von Datensätze mit
    Parametern, die beim Aufruf übergeben werden (benutzerdefinierte Regeln)"""
    with test_app.app_context():
        tagger = Tagger(MockDatabase())

        # Tagging
        mocker_result = tagger.tag_or_cat_custom(
            iban="DE89370400440532013000", tags=['custom_tagging1', 'custom_tagging2'],
            filters=[{'key': 'amount', 'compare': '<', 'value': -100}],
            parsed_keys=['custom_key1', 'custom_key2'],
            parsed_vals=['custom_val1', 'custom_val2'], multi='AND',
        )
        assert mocker_result.get('entries') == ['custom_tagging_uuid'], \
            "Result does not match with Mocker Fake"

        # Categorizing
        mocker_result = tagger.tag_or_cat_custom(
            iban="DE89370400440532013000", category='custom_category',
            filters=[{'key': 'amount', 'compare': '<', 'value': -999}],
            prio=22, prio_set=33,
            parsed_keys=['custom_key1', 'custom_key2'],
            parsed_vals=['custom_val1', 'custom_val2'], multi='AND',
        )
        assert mocker_result.get('entries') == ['custom_categorize_uuid'], \
            "Result does not match with Mocker Fake"


def test_tag_streaming(test_app):
    """Test that `tag(..., streaming=True)` yields partials per matched entry and a final result."""
    with test_app.app_context():
        tagger = Tagger(MockDatabase())

        partials = []
        final = None

        for item in tagger.tag(iban="DE89370400440532013000", streaming=True):

            # Generator yields mutable partial dicts; copy to capture state at yield-time
            if isinstance(item, dict) and item.get('rule') is not None:
                print(f"Received partial:", item)
                partials.append(copy.deepcopy(item))

            else:
                final = item

        # According to MockDatabase there are 1 match for first rule and 2 for second => 3 partials
        assert len(partials) == 5, f"Expected 5 partial yields, got {len(partials)}"

        # Final result must contain aggregated entries for the tagging operation
        assert final is not None and isinstance(final, dict), "Final result missing or invalid"
        assert 'test_tag' in final.get('entries', []) and 'test_tag2' in final.get('entries', []), \
            "Final result does not contain expected tagged UUIDs"


def test_categorize_streaming(test_app):
    """Test that `categorize(..., streaming=True)` yields partials per matched entry and a final result."""
    with test_app.app_context():
        tagger = Tagger(MockDatabase())

        gen = tagger.categorize(iban="DE89370400440532013000", streaming=True)

        partials = []
        final = None

        for item in gen:
            if isinstance(item, dict) and item.get('rule') is not None:
                print(f"Received partial:", item)
                partials.append(copy.deepcopy(item))
            else:
                final = item

        # MockDatabase returns a single match for categorize
        assert len(partials) == 2, f"Expected 2 partial yields, got {len(partials)}"

        assert final is not None and isinstance(final, dict), "Final result missing or invalid"
        assert 'test_categorize' in final.get('entries', []), "Final result does not contain expected categorized UUID"
