#!/usr/bin/python3 # pylint: disable=invalid-name
"""Testing more rules and specific tagging situations"""

import io
import os
import sys


# Add Parent for importing from 'app.py'
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper import get_testfile_contents

EXAMPLE_CSV = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'input_commerzbank.csv'
)


def test_upload_file_route(test_app):
    """Upload Testdata for further testing"""

    with test_app.app_context():

        with test_app.test_client() as client:

            # Clear Database
            result = client.delete("/api/deleteDatabase/DE89370400440532013000")
            assert result.status_code == 200, "Fehler beim Leeren der Datenbank"

            # Prepare File
            content = get_testfile_contents(EXAMPLE_CSV, binary=True)
            files = {
                'file-batch': (io.BytesIO(content), 'input_commerzbank.csv'),
                'bank': 'Commerzbank'
            }

            # Post File
            result = client.post(
                "/api/upload/DE89370400440532013000",
                data=files, content_type='multipart/form-data'
            )

            # Check Response
            # (If other test run already, data is til present and duplicates won't be inserted)
            assert result.status_code in (200, 201), \
                f"Die Seite hat den Upload nicht wie erwartet verarbeitet: {result.text}"
            assert result.json.get('filename') == 'input_commerzbank.csv', \
                "Angaben zum Upload wurden nicht gefunden"


def test_add_or_update_tags(test_app):
    """Test adding and updating tag for a transaction"""

    with test_app.app_context():

        iban = "DE89370400440532013000"
        tid = "6884802db5e07ee68a68e2c64f9c0cdd"

        # Add first tag
        r = test_app.host.set_manual_tag_and_cat(iban, tid, ['Bäckerei'])
        assert r == {'updated': 1}, \
            "Es wurde keine Transaktion geändert (set_manual_tag_and_cat), first Tag"

        # Update tag (add one more)
        r = test_app.host.set_manual_tag_and_cat(iban, tid, ['Markt'], overwrite=False)
        assert r == {'updated': 1}, \
            "Es wurde keine Transaktion geändert (set_manual_tag_and_cat), add Tag"

        # Update tag (remove one)
        r = test_app.host.set_manual_tag_and_cat(iban, tid, ['Bäckerei'], overwrite=True)
        assert r == {'updated': 1}, \
            "Es wurde keine Transaktion geändert (set_manual_tag_and_cat), remove one Tag"

        # Update tag (remove all)
        assert test_app.host.remove_tags(iban, tid) == {'updated': 1}, \
            "Es wurde keine Transaktion geändert (remove_tags)"
