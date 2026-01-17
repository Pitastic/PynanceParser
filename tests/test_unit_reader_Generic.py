#!/usr/bin/python3 # pylint: disable=invalid-name
"""Testmodul für das Einlesen von Daten mit Hilfe des generischen Readers"""

import os
import sys
import pytest

# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper import check_transaktion_list
from reader.Generic import Reader as Generic


def test_read_from_csv(test_app):
    """Testet das Einlesen einer CSV Datei mit Kontoumsätzen"""
    with test_app.app_context():
        uri = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'input_generic.csv'
        )
        transaction_list = Generic().from_csv(uri)

        # Check Reader Ergebnisse
        check_transaktion_list(transaction_list)


@pytest.mark.skip(reason="Currently not implemented yet")
def test_read_from_pdf():
    """Testet das Einlesen einer PDF Datei mit Kontoumsätzen"""
    return None


@pytest.mark.skip(reason="Currently not implemented yet")
def test_read_from_http():
    """Testet das Einlesen Kontoumsätzen aus einer Online-Quelle"""
    return None

def test_strftime_parser(test_app):
    """Testet den strftime Parser des Generic Readers"""
    with test_app.app_context():
        reader = Generic()

        # Teste verschiedene Datumsformate
        date_formats = [
            ("%d.%m.%Y", "25.12.2023", 1703462400.0),
            ("%Y-%m-%d", "2023-12-25", 1703462400.0),
            ("%m/%d/%Y", "12/25/2023", 1703462400.0),
        ]

        for fmt, date_str, expected_timestamp in date_formats:
            ts = reader._parse_from_strftime(date_str, fmt) # pylint: disable=protected-access
            assert ts == expected_timestamp, f"Failed for format {fmt}"

        # Teste automatische Korrektur (31.11. / 30.02. etc.)
        date_formats = [
            ("%d.%m.%Y", "31.11.2023", 1701302400.0),  # Korrigiert zu 30.11.2023
            ("%d.%m.%Y", "30.02.2024", 1709164800.0),  # Korrigiert zu 28.02.2024
        ]

        for fmt, date_str, expected_timestamp in date_formats:
            ts = reader._parse_from_strftime(date_str, fmt) # pylint: disable=protected-access
            assert ts == expected_timestamp, f"Failed for format {fmt}"
