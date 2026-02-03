#!/usr/bin/python3 # pylint: disable=invalid-name
"""
Testing rules on optional data (own data) not from this repo.

Put (multiple) testfiles in /tmp/pynance-*.csv which will be imported with the Generic importer.
(See tests/input_generic.csv for an example file format)

Fill in the result dict which tags or categories should be found for which uuid.
You need to know the tx_ids/uuids beforehand.

The 'uuid' from the dict and from the will then be used to check, if the expected results match with this transaction.

This Test will also pass if no testfiles are found.
"""

import os
import sys
import glob

# Add Parent for importing from 'app.py'
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper import check_transaktion_list
from reader.Generic import Reader as Generic


EXPECTED_RESULTS = {
    '786e1d4e16832aa321a0176c854fe087': {
        'tags': ["Stadt", "Tag2"],
        'category': ''
    },
}

def test_rules_with_custom_input(test_app):

    for csv_file in glob.glob(os.path.join('/tmp', 'pynance-*.csv')):

        with test_app.app_context():
            transaction_list = Generic().from_csv(csv_file)
            assert transaction_list, f"No transactions found in CSV file {csv_file}"

            # Check Reader Ergebnisse
            check_transaktion_list(transaction_list)
            print(10*'+', transaction_list)

            # Find the transaction by its ID
            for tx in transaction_list:
                tx_id = tx.get('uuid')
                print(f"Checking tx_id {tx_id}...")

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
