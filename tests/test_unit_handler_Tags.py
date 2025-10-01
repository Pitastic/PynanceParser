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
        assert mocker_result.get('entries') == ['test_tag'], \
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
        assert mocker_result.get('entries') == ['test_tag', 'test_categorize'], \
            "Result does not match with Mocker Fake"


def test_tag_or_cat_custom(test_app):
    """Testet das Kategorisieren und Taggen von Datensätze mit
    Parametern, die beim Aufruf übergeben werden (benutzerdefinierte Regeln)"""
    with test_app.app_context():
        tagger = Tagger(MockDatabase())

        # Tagging
        mocker_result = tagger.tag_or_cat_custom(
            iban="DE89370400440532013000", tags=['custom_tagging1', 'custom_tagging2'],
            filters=[{'key': 'betrag', 'compare': '<', 'value': -100}],
            parsed_keys=['custom_key1', 'custom_key2'],
            parsed_vals=['custom_val1', 'custom_val2'], multi='AND',
        )
        assert mocker_result.get('entries') == ['custom_tagging_uuid'], \
            "Result does not match with Mocker Fake"

        # Categorizing
        mocker_result = tagger.tag_or_cat_custom(
            iban="DE89370400440532013000", category='custom_category',
            filters=[{'key': 'betrag', 'compare': '<', 'value': -999}],
            prio=22, prio_set=33,
            parsed_keys=['custom_key1', 'custom_key2'],
            parsed_vals=['custom_val1', 'custom_val2'], multi='AND',
        )
        assert mocker_result.get('entries') == ['custom_categorize_uuid'], \
            "Result does not match with Mocker Fake"
