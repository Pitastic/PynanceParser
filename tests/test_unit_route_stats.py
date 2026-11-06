#!/usr/bin/python3 # pylint: disable=invalid-name
"""Testmodul das abfragen der Route für die Statistiken"""

import io
import os
import sys
import pprint

# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper import get_testfile_contents


EXAMPLE_CSV = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'input_generic2.csv'
)

def test_upload_file_route(test_app):
    """Upload Testdata for further testing"""

    with test_app.app_context():

        with test_app.test_client() as client:
            iban = "DE89370400440532013000"

            # Clear Database
            result = client.delete(f"/api/deleteDatabase/{iban}")
            assert result.status_code == 200, "Fehler beim Leeren der Datenbank"

            # Prepare File
            content = get_testfile_contents(EXAMPLE_CSV, binary=True)
            files = {
                'file-batch': (io.BytesIO(content), 'input_generic2.csv'),
                'bank': 'Generic'
            }

            # Post File
            result = client.post(
                f"/api/upload/{iban}",
                data=files, content_type='multipart/form-data'
            )

            # Check Response
            # (If other test run already, data is til present and duplicates won't be inserted)
            assert result.status_code in (200, 201), \
                f"Die Seite hat den Upload nicht wie erwartet verarbeitet: {result.text}"
            assert result.json.get('filename') == 'input_generic2.csv', \
                "Angaben zum Upload wurden nicht gefunden"

            # Taggen
            result = client.put(f"/api/tag/{iban}", json={})
            assert result.status_code == 200, \
                "Die Seite hat die Tagging Anfrage nicht wie erwartet verarbeitet"

            tx_id ="5197f4774271512f252acfb3c4f63237"
            r = test_app.host.set_manual_tag_and_cat( # pylint: disable=protected-access
                iban, tx_id, tags= ['Gehalt'], category='Einkommen'
            )
            assert r.get('updated') == 1, 'Es wurde kein Eintrag aktualisiert. '

            tx_id ="6884802db5e07ee68a68e2c64f9c0cdd"
            r = test_app.host.set_manual_tag_and_cat( # pylint: disable=protected-access
                iban, tx_id, tags= ['Garten'], category='Hauskosten'
            )
            assert r.get('updated') == 1, 'Es wurde kein Eintrag aktualisiert. '

            tx_id ="fdd4649484137572ac642e2c0f34f9af"
            r = test_app.host.set_manual_tag_and_cat( # pylint: disable=protected-access
                iban, tx_id, tags= ['Drogerie']
            )
            assert r.get('updated') == 1, 'Es wurde kein Eintrag aktualisiert. '

            # Kategorisieren
            result = client.put(f"/api/cat/{iban}", json={})
            assert result.status_code == 200, \
                "Die Seite hat die Kategorisierung Anfrage nicht wie erwartet verarbeitet"


def test_route_stats(test_app):
    """Test the route for the statistics"""

    with test_app.app_context():

        with test_app.test_client() as client:

            # Get Stats
            result = client.get("/api/stats/DE89370400440532013000?type=top")

            # Check Response
            assert result.status_code == 200, \
                "Die Seite hat die Anfrage nicht wie erwartet verarbeitet"

            result = result.json
            pprint.pprint(result)
            assert 'top' in result, "Die erwarteten Daten wurden nicht gefunden"
            top_result = result['top']



            # Prüfe die Struktur für cat_top_in
            assert 'cat_top_in' in top_result, "cat_top_in muss vorhanden sein"
            assert isinstance(top_result['cat_top_in'], list), "cat_top_in muss eine Liste sein"
            for item in top_result['cat_top_in']:
                assert isinstance(item, str), "Jedes Element in cat_top_in muss ein String sein"

            # Prüfe die Struktur für cat_top_out
            assert 'cat_top_out' in top_result, "cat_top_out muss vorhanden sein"
            assert isinstance(top_result['cat_top_out'], list), "cat_top_out muss eine Liste sein"
            for item in top_result['cat_top_out']:
                assert isinstance(item, str), "Jedes Element in cat_top_out muss ein String sein"

            # Prüfe die Struktur für tag_top_in
            assert 'tag_top_in' in top_result, "tag_top_in muss vorhanden sein"
            assert isinstance(top_result['tag_top_in'], list), "tag_top_in muss eine Liste sein"
            for item in top_result['tag_top_in']:
                assert isinstance(item, str), "Jedes Element in tag_top_in muss ein String sein"

            # Prüfe die Struktur für tag_top_out
            assert 'tag_top_out' in top_result, "tag_top_out muss vorhanden sein"
            assert isinstance(top_result['tag_top_out'], list), "tag_top_out muss eine Liste sein"
            for item in top_result['tag_top_out']:
                assert isinstance(item, str), "Jedes Element in tag_top_out muss ein String sein"

            # Prüfe die Struktur für categories
            assert 'categories' in top_result, "categories muss vorhanden sein"
            assert isinstance(top_result['categories'], dict), "categories muss ein Dictionary sein"
            for _, cat in top_result['categories'].items():
                assert isinstance(cat, dict), "Jedes Element in categories muss ein Dictionary sein"
                assert 'category' in cat, "category muss in jedem categories-Dict vorhanden sein"
                assert isinstance(cat['category'], str), "category muss ein String sein"
                assert 'count' in cat, "count muss in jedem categories-Dict vorhanden sein"
                assert isinstance(cat['count'], int), "count muss ein Integer sein"
                assert 'sum' in cat, "sum muss in jedem categories-Dict vorhanden sein"
                assert isinstance(cat['sum'], (int, float)), "sum muss ein Integer oder Float sein"
                assert 'abs_in' in cat, "abs_in muss in jedem categories-Dict vorhanden sein"
                assert isinstance(cat['abs_in'], (int, float)), \
                    "abs_in muss ein Integer oder Float sein"
                assert 'abs_out' in cat, "abs_out muss in jedem categories-Dict vorhanden sein"
                assert isinstance(cat['abs_out'], (int, float)), \
                    "abs_out muss ein Integer oder Float sein"

            # Prüfe die Struktur für tags
            assert 'tags' in top_result, "tags muss vorhanden sein"
            assert isinstance(top_result['tags'], dict), "tags muss ein Dictionary sein"
            for _, tag in top_result['tags'].items():
                assert isinstance(tag, dict), "Jedes Element in tags muss ein Dictionary sein"
                assert 'tag' in tag, "tag muss in jedem tags-Dict vorhanden sein"
                assert isinstance(tag['tag'], str), "tag muss ein String sein"
                assert 'count' in tag, "count muss in jedem tags-Dict vorhanden sein"
                assert isinstance(tag['count'], int), "count muss ein Integer sein"
                assert 'sum' in tag, "sum muss in jedem tags-Dict vorhanden sein"
                assert isinstance(tag['sum'], (int, float)), "sum muss ein Integer oder Float sein"
                assert 'abs_in' in tag, "abs_in muss in jedem tags-Dict vorhanden sein"
                assert isinstance(tag['abs_in'], (int, float)), \
                    "abs_in muss ein Integer oder Float sein"
                assert 'abs_out' in tag, "abs_out muss in jedem tags-Dict vorhanden sein"
                assert isinstance(tag['abs_out'], (int, float)), \
                    "abs_out muss ein Integer oder Float sein"
