#!/usr/bin/python3 # pylint: disable=invalid-name
"""
Testing rules on optional data (own data) not from this repo.

Put (multiple) testfiles in /tmp/pynance-*.csv which will be imported with
the Generic importer (see tests/input_generic.csv for an example file format).

Fill in the result dict which tags or categories should be found for which uuid.
You need to know the tx_ids/uuids beforehand.

The 'uuid' from the dict and from the will then be used to check,
if the expected results match with this transaction.

The example in this code shows Transaction with uuid '524a0184ca2ba4a5e438f362da95cffc'
from the 'tests/input_generic.csv'' file.

This Test will also pass if no testfiles are found.
"""

import os
import sys
import glob

# Add Parent for importing from 'app.py'
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper import check_transaktion_list


EXPECTED_RESULTS = {
    '524a0184ca2ba4a5e438f362da95cffc': {
        'tags': ["Lebensmittel"],
        'category': None
    },
}

def test_rules_with_custom_input(test_app):
    """Generic Tester for all transactions in CSV files as described above"""

    for csv_file in glob.glob(os.path.join('/tmp', 'pynance-*.csv')):

        with test_app.app_context():
            fake_iban = 'DE89370400440532013000'
            transaction_list = test_app.host.read_input(csv_file, bank='Generic', data_format='csv')

            # Check Reader Ergebnisse
            assert transaction_list, f"No transactions found in CSV file {csv_file}"
            check_transaktion_list(transaction_list)
            assert test_app.host.db_handler.insert(transaction_list, fake_iban), \
                "Inserting transactions from CSV failed"
            assert test_app.host.tagger.tag_and_cat(fake_iban), \
                "Tagging and Categorizing transactions from CSV failed"

            # Re-Select all transactions for this IBAN
            transaction_list = test_app.host.db_handler.select(fake_iban)

            # Find the transaction by its ID
            for tx in transaction_list:
                tx_id = tx.get('uuid')

                if tx_id not in EXPECTED_RESULTS:
                    print(f"Skipping tx_id {tx_id} as it is not in EXPECTED_RESULTS")
                    continue

                # Check the right tags
                assert len(EXPECTED_RESULTS[tx_id]['tags']) == len(tx.get('tags', [])), \
                    f"Tags length mismatch for tx_id {tx_id}"
                assert set(EXPECTED_RESULTS[tx_id]['tags']) == set(tx.get('tags', [])), \
                    f"Tags mismatch for tx_id {tx_id}"

                # Check the right category
                assert EXPECTED_RESULTS[tx_id]['category'] == tx.get('category'), \
                    f"Category mismatch for tx_id {tx_id}"
