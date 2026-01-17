#!/usr/bin/python3 # pylint: disable=invalid-name
"""Testmodul für das Einlesen von Daten mit Hilfe des Comdirect Readers"""

import os
import sys
import pytest

# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper import check_transaktion_list
from reader.Comdirect import Reader as Comdirect


def test_read_from_csv(test_app):
    """Testet das Einlesen einer CSV Datei mit Kontoumsätzen"""
    test_file_csv = os.path.join('/tmp', 'comdirect.csv')
    if not os.path.isfile(test_file_csv):
        # Test file not provided (sensitive data is not part of git repo)
        pytest.skip("Testfile /tmp/comdirect.csv not found....skipping")

    with test_app.app_context():
        transaction_list = Comdirect().from_csv(test_file_csv)

        # Check Reader Ergebnisse
        check_transaktion_list(transaction_list)


# Look for test files and create a tuple list
test_folder = os.path.join('/tmp', 'Comdirect')
test_files = []
if not os.path.isdir(test_folder):
    test_files = [()]
else:
    for file in os.listdir(test_folder):
        test_files.append(
            (os.path.join(test_folder, file))
        )

# Using every test file in its own test
@pytest.mark.parametrize("full_path", test_files)
def test_read_from_pdf(test_app, full_path):
    """Testet das Einlesen einer PDF Datei mit Kontoumsätzen"""
    if not full_path:
        # Test files not provided (sensitive data is not part of git repo)
        pytest.skip("Testfile not provided....skipping")

    with test_app.app_context():
        transaction_list = Comdirect().from_pdf(full_path)
        assert transaction_list, "No transactions found in PDF file"

        # Check Reader Ergebnisse
        check_transaktion_list(transaction_list)


@pytest.mark.skip(reason="Currently not implemented yet")
def test_read_from_http(test_app):
    """Testet das Einlesen Kontoumsätzen aus einer Online-Quelle"""
    return None
