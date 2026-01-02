#!/usr/bin/python3 # pylint: disable=invalid-name
"""
Testmodul für das sortierte ausgeben von Einträgen nach Datum.
Weitere Sortiermöglichkeiten werden clientseitig umgesetzt.
"""

import os


def test_create_test_dataset(test_app):
    """
    Testet den Handler für das Einlesen übermittelter Daten im CSV Format.
    Die Methode wird bei gerade hochgeladenen Daten genutzt und findet
    sich auch in anderen Integraionstests wieder.
    """
    with test_app.app_context():
        # Truncate DB first
        test_app.host.db_handler.truncate("DE89370400440532013000")
        test_app.host.db_handler.truncate("DE89370400440532013001")
        test_app.host.db_handler.truncate("DE89370400440532011111")
        
        # Erster Import
        found_rows = test_app.host.read_input(os.path.join( # pylint: disable=protected-access
            os.path.dirname(os.path.abspath(__file__)),
            'input_generic.csv'
        ), bank='Generic', data_format='csv')

        # Check Return Value
        found_rows_len = len(found_rows)
        assert found_rows_len == 5, (f'Es wurden {found_rows_len} statt der '
                                    'erwarteten 5 Einträge aus der Datei eingelesen.')
        # Savev to DB for next Tests
        r = test_app.host.db_handler.insert(found_rows, "DE89370400440532013000")
        assert r.get('inserted') == 5, \
            "Es wurden nicht alle Einträge in die DB eingefügt."

        # Zweiter Import
        found_rows = test_app.host.read_input(os.path.join( # pylint: disable=protected-access
            os.path.dirname(os.path.abspath(__file__)),
            'input_generic2.csv'
        ), bank='Generic', data_format='csv')

        # Check Return Value
        found_rows_len = len(found_rows)
        assert found_rows_len == 5, (f'Es wurden {found_rows_len} statt der '
                                    'erwarteten 5 Einträge aus der Datei eingelesen.')
        # Savev to DB for next Tests
        r = test_app.host.db_handler.insert(found_rows, "DE89370400440532013001")
        assert r.get('inserted') == 5, \
            "Es wurden nicht alle Einträge in die DB eingefügt."

        # Group IBANs for next Tests
        r = test_app.host.db_handler.add_iban_group(
            "testgroup",
            ["DE89370400440532013000", "DE893704004405320130001"]
        )
        assert r == {'inserted': 1}, \
            "Das Gruppieren der IBANs ist fehlgeschlagen."


def test_sort_entries_date_asc(test_app):
    """
    Testet das sortierte Ausgeben von Einträgen nach Datum aufsteigend.
    """
    with test_app.app_context():
        group_name = "testgroup"

        # Sortieren der Einträge
        sorted_entries = test_app.host.get_sorted_entries( # pylint: disable=protected-access
            group_name, sort_by='date', descending=False
        )

        # Überprüfen der Sortierung
        dates = [entry['date'] for entry in sorted_entries]
        assert dates == sorted(dates), \
            "Die Einträge sind nicht korrekt nach Datum aufsteigend sortiert."


def test_sort_entries_date_desc(test_app):
    """
    Testet das sortierte Ausgeben von Einträgen nach Datum absteigend.
    """
    with test_app.app_context():
        group_name = "testgroup"

        # Sortieren der Einträge
        sorted_entries = test_app.host.get_sorted_entries( # pylint: disable=protected-access
            group_name, sort_by='date', descending=True
        )

        # Überprüfen der Sortierung
        dates = [entry['date'] for entry in sorted_entries]
        assert dates == sorted(dates, reverse=True), \
            "Die Einträge sind nicht korrekt nach Datum absteigend sortiert."
