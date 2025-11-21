#!/usr/bin/python3 # pylint: disable=invalid-name
"""Testing other routes from the app with some requests"""

import io
import os
import sys


# Add Parent for importing from 'app.py'
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper import get_testfile_contents

EXAMPLE_CSV = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'commerzbank.csv'
)


def test_upload_file_route(test_app):
    """Upload Testdata for further testing"""

    with test_app.app_context():

        with test_app.test_client() as client:

            # Prepare File
            content = get_testfile_contents(EXAMPLE_CSV, binary=True)
            files = {
                'file-input': (io.BytesIO(content), 'commerzbank.csv'),
                'bank': 'Commerzbank'
            }

            # Post File
            result = client.post(
                "/api/upload/DE89370400440532013000",
                data=files, content_type='multipart/form-data'
            )

            # Check Response
            assert result.status_code == 201, \
                f"Die Seite hat den Upload nicht wie erwartet verarbeitet: {result.text}"
            assert result.json.get('filename') == 'commerzbank.csv', \
                "Angaben zum Upload wurden nicht gefunden"


def test_get_error_messages(test_app):
    """
    Testet das Auslesen der Fehlermeldungen,
    wenn es zu einem Fehler beim Handling des Requests kommt.
    """
    with test_app.app_context():

        with test_app.test_client() as client:
            # Make faulty Request
            result = client.get("/api/non_existing_route")

            # Check Response
            assert result.status_code == 404, \
                "Die Seite hat den fehlerhaften Request nicht wie erwartet verarbeitet."

            # Faulty Upload
            # - Prepare faulty File
            content = get_testfile_contents(EXAMPLE_CSV, binary=True)
            files = {
                'file-input': (io.BytesIO(content), 'commerzbank.csv')
            }

            # Post faulty File (missing 'bank' field for Generic importer)
            result = client.post(
                "/api/upload/DE89370400440532013000",
                data=files, content_type='multipart/form-data'
            )

            # Check Response
            assert result.status_code == 406, \
                "Die Seite hat den fehlerhaften Upload nicht wie erwartet verarbeitet."
            assert 'error' in result.json, \
                "Fehlermeldung wurde nicht im Response gefunden."
