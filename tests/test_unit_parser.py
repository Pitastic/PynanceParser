#!/usr/bin/python3 # pylint: disable=invalid-name
"""
Testmodul für das einzelne Testen von allen Parser-Regexes
"""

import os
import sys

# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper import MockTaggerParser


# Global test strings
test_string1 = (
    "Stadt Halle 0000005112 OBJEKT 0001 ABGABEN LT. "
    "BESCHEID EREF: 2023-01-00111-9090-0000005112 "
    "MREF: M1111111 Gläubiger-ID: DE7000100000077777 "
    "SEPA-BASISLASTSCHRIFT wiederholend"
)
test_string2 = (
    "Stadt Halle 0000005112 OBJEKT 0001 ABGABEN LT. "
    "BESCHEID End-to-End-Ref.: 2023-01-00111-9090-0000005112 "
    "Mandatsref: M1111111 Gläubiger-ID: DE7000100000077777 "
    "SEPA-BASISLASTSCHRIFT wiederholend"
)

def test_parser_mandatsreferenz(test_app):
    """
    Testet die Mandatsreferenz-Regex
    """
    # Load specific parser rule
    rule_name = "Mandatsreferenz"
    tagger = MockTaggerParser(rule_name)

    # Matching
    result = tagger.parse([{'parsed': {}, 'text_tx': test_string1}])[0]
    assert result.get('parsed', {}).get(rule_name) == "M1111111"

    result = tagger.parse([{'parsed': {}, 'text_tx': test_string2}])[0]
    assert result.get('parsed', {}).get(rule_name) == "M1111111"


def test_parser_mandatsreferenz(test_app):
    """
    Testet die End-to-End-Regex
    """
    # Load specific parser rule
    rule_name = "End-to-End-Referenz"
    tagger = MockTaggerParser(rule_name)

    # Matching
    result = tagger.parse([{'parsed': {}, 'text_tx': test_string1}])[0]
    assert result.get('parsed', {}).get(rule_name) == "2023-01-00111-9090-0000005112"

    result = tagger.parse([{'parsed': {}, 'text_tx': test_string2}])[0]
    assert result.get('parsed', {}).get(rule_name) == "2023-01-00111-9090-0000005112"
