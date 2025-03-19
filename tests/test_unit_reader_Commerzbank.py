#!/usr/bin/python3 # pylint: disable=invalid-name
"""Testmodul für das Einlesen von Daten mit Hilfe des Commerzbank Readers"""

import os
import sys
import pytest

# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper import check_transaktion_list
from reader.Commerzbank import Reader as Commerzbank


def test_read_from_csv(test_app):
    """Testet das Einlesen einer CSV Datei mit Kontoumsätzen"""
    with test_app.app_context():
        uri = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'commerzbank.csv'
        )
        transaction_list = Commerzbank().from_csv(uri)

        # Check Reader Ergebnisse
        check_transaktion_list(transaction_list)


@pytest.mark.skip(reason="Currently not implemented yet")
def test_read_from_pdf(test_app):
    """Testet das Einlesen einer PDF Datei mit Kontoumsätzen"""
    return None


@pytest.mark.skip(reason="Currently not implemented yet")
def test_read_from_http(test_app):
    """Testet das Einlesen Kontoumsätzen aus einer Online-Quelle"""
    return None

