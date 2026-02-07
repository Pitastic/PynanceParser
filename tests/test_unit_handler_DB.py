#!/usr/bin/python3 # pylint: disable=invalid-name
"""Testmodul für die Interaktion mit der Datenbank"""

import os
import sys

# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper import generate_fake_data, check_entry


def test_add_and_get_group(test_app):
    """
    Testet das Hinzufügen einer Gruppe in der Instanz.
    """
    with test_app.app_context():

        result = test_app.host.db_handler.add_iban_group("testgroup", ["DE89370400440532013000"])
        assert result == {'inserted': 1}, 'Die Gruppe wurde nicht hinzugefügt.'

        # No Doublettes
        result = test_app.host.db_handler.add_iban_group("testgroup",
                                    ["DE89370400440532013000", "DE89370400440532011111"])
        assert result == {'inserted': 1}, \
            'Die Gruppe wurde nicht geupdated.'

        result = test_app.host.db_handler.get_group_ibans("testgroup")
        assert isinstance(result, list), 'Die IBANs wurden nicht als Liste zurückgegeben.'
        assert len(result) == 2, 'Die Gruppe enthält nicht die erwartete Anzahl an IBANs.'
        assert "DE89370400440532013000" in result, 'Die erste IBAN wurde nicht zurückgegeben.'
        assert 'DE89370400440532011111' in result, 'Die zweite IBAN wurde nicht zurückgegeben.'

def test_insert(test_app):
    """Testet das Einfügen von Datensätzen"""
    with test_app.app_context():
        # Einzelner Datensatz
        data = generate_fake_data(1)[0]
        inserted_db = test_app.host.db_handler.insert(data,
                                        collection="DE89370400440532013000")
        id_count = inserted_db.get('inserted')
        assert id_count == 1, \
            f"Es wurde nicht die erwartete Anzahl an Datensätzen eingefügt: {id_count}"

        # Zwischendurch leeren
        deleted_db = test_app.host.db_handler.truncate('DE89370400440532013000')
        delete_count = deleted_db.get('deleted')
        assert delete_count > 0, "Die Datenbank konnte während des Tests nicht geleert werden"

        # Liste von Datensätzen
        data = generate_fake_data(4)
        inserted_db = test_app.host.db_handler.insert(data, collection="DE89370400440532013000")
        id_count = inserted_db.get('inserted')
        assert id_count == 4, \
            f"Es wurde nicht die erwartete Anzahl an Datensätzen eingefügt: {id_count}"

        # Keine Duplikate
        data = generate_fake_data(5)
        inserted_db = test_app.host.db_handler.insert(data, collection="DE89370400440532013000")
        id_count = inserted_db.get('inserted')
        assert id_count == 1, \
            f"Es wurden doppelte Datensätze eingefügt: {id_count}"

        # Zweite IBAN in der gleichen Gruppe
        data = generate_fake_data(2, json_path='input_commerzbank2.json')
        inserted_db = test_app.host.db_handler.insert(data, collection='DE89370400440532011111')
        id_count = inserted_db.get('inserted')
        assert id_count == 2, \
            f"Es konnten keine Datensätze zu einer weiteren IBAN eingefügt werden: {id_count}"

def test_select_all(test_app):
    """Testet das Auslesen von allen Datensätzen"""
    with test_app.app_context():
        # Liste von Datensätzen einfügen
        test_app.host.db_handler.truncate('DE89370400440532013000')
        data = generate_fake_data(5)
        test_app.host.db_handler.insert(data, collection="DE89370400440532013000")

        # Alles selektieren
        result_all = test_app.host.db_handler.select("DE89370400440532013000")
        assert len(result_all) == 5, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_all)}"
        for entry in result_all:
            check_entry(entry)


def test_select_filter(test_app):
    """Testet das Auslesen von einzelnen und mehreren Datensätzen mit Filter"""
    with test_app.app_context():
        # Selektieren mit Filter (by Hash)
        query = {'key': 'uuid', 'value': '13d505688ab3b940dbed47117ffddf95'}
        result_filtered = test_app.host.db_handler.select("DE89370400440532013000",
                                                condition=query)
        assert len(result_filtered) == 1, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry, key_vals={'date_tx': '02.01.2023', 'amount': -118.94})

        # Selektieren mit Filter (by Art)
        query = {'key': 'art', 'value': 'Lastschrift'}
        result_filtered = test_app.host.db_handler.select("DE89370400440532013000", condition=query)
        assert len(result_filtered) == 5, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)


def test_select_like(test_app):
    """Testet das Auslesen von Datensätzen mit Textfiltern (like)"""
    with test_app.app_context():
        # Selektieren mit Filter (by LIKE Text-Content)
        query = {'key': 'text_tx', 'compare': 'like', 'value': 'Garten'}
        result_filtered = test_app.host.db_handler.select("DE89370400440532013000",
                                                condition=query)
        assert len(result_filtered) == 1, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)


def test_select_lt(test_app):
    """Testet das Auslesen von Datensätzen mit 'kleiner als'"""
    with test_app.app_context():
        query = {'key': 'amount', 'compare': '<', 'value': -100}
        result_filtered = test_app.host.db_handler.select("DE89370400440532013000",
                                                condition=query)
        assert len(result_filtered) == 2, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)


def test_select_lt_eq(test_app):
    """Testet das Auslesen von Datensätzen mit 'kleiner als, gleich'"""
    with test_app.app_context():
        query = {'key': 'amount', 'compare': '<=', 'value': -71.35}
        result_filtered = test_app.host.db_handler.select("DE89370400440532013000", condition=query)
        assert len(result_filtered) == 4, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)


def test_select_not_eq(test_app):
    """Testet das Auslesen von Datensätzen mit 'ungleich'"""
    with test_app.app_context():
        query = {'key': 'valuta', 'compare': '!=', 'value': 1684108800}
        result_filtered = test_app.host.db_handler.select("DE89370400440532013000",
                                                condition=query)
        assert len(result_filtered) == 1, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)

def test_select_list_filters(test_app):
    """Testet das Auslesen von Datensätzen mit 'in' und 'not in'"""
    with test_app.app_context():
        # IN
        query = {'key': 'tags', 'compare': 'in', 'value': ['TestTag1', 'TestTag3']}
        result_filtered = test_app.host.db_handler.select("DE89370400440532013000",
                                                condition=query)
        assert len(result_filtered) == 2, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)
            assert entry.get('amount') in [-221.98, -99.58], \
                f"Es wurde der falsche Eintrag zurückgegeben: {entry.get('amount')}"

        # NOT IN
        query = {'key': 'tags', 'compare': 'notin', 'value': ['TestTag1']}
        result_filtered = test_app.host.db_handler.select("DE89370400440532013000",
                                                condition=query)
        assert len(result_filtered) == 4, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)
            assert entry.get('amount') != -221.98, \
                f"Es wurde der falsche Eintrag zurückgegeben: {entry.get('amount')}"

        # all
        query = {'key': 'tags', 'compare': 'all', 'value': ['TestTag1', 'TestTag2']}
        result_filtered = test_app.host.db_handler.select("DE89370400440532013000",
                                                condition=query)
        assert len(result_filtered) == 1, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        entry = result_filtered[0]
        check_entry(entry)
        assert entry.get('amount') == -221.98, \
            f"Es wurde der falsche Eintrag zurückgegeben: {entry.get('amount')}"

def test_select_regex(test_app):
    """Testet das Auslesen von Datensätzen mit Textfiltern (regex)"""
    with test_app.app_context():
        query = {'key': 'text_tx', 'compare': 'regex', 'value': r'KFN\s[0-9]\s[A-Z]{2}\s[0-9]{3,4}'}
        result_filtered = test_app.host.db_handler.select("DE89370400440532013000", condition=query)
        assert len(result_filtered) == 4, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)


def test_select_multi(test_app):
    """Testet das Auslesen von Datensätzen mit mehreren Filterargumenten"""
    with test_app.app_context():
        # Selektieren mit Filter (mehrere Bedingungen - AND)
        query = [
            {'key': 'text_tx', 'compare': 'like', 'value': 'Kartenzahlung'},
            {'key': 'amount', 'compare': '>', 'value': -100},
            {'key': 'amount', 'compare': '<', 'value': -50},
        ]
        result_filtered = test_app.host.db_handler.select("DE89370400440532013000",
                                                condition=query,
                                                multi='AND')
        assert len(result_filtered) == 2, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)

        # Selektieren mit Filter (mehrere Bedingungen - OR)
        query = [
            {'key': 'text_tx', 'compare': 'like', 'value': 'München'},
            {'key': 'text_tx', 'compare': 'like', 'value': 'Frankfurt'},
            {'key': 'text_tx', 'compare': 'like', 'value': 'FooBar not exists'},
        ]
        result_filtered = test_app.host.db_handler.select("DE89370400440532013000",
                                                condition=query,
                                                multi='OR')
        assert len(result_filtered) == 2, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)


def test_list_ibans(test_app):
    """Testet das Auslesen aller IBANs"""
    with test_app.app_context():
        ibans = test_app.host.db_handler.list_ibans()
        assert isinstance(ibans, list), "Die IBANs wurden nicht als Liste zurückgegeben"
        assert len(ibans) >= 2, "Es wurden nicht alle IBANs zurückgegeben"
        assert "DE89370400440532013000" in ibans, "Die Test-IBAN wurde nicht zurückgegeben"
        assert 'DE89370400440532011111' in ibans, "Die zweite Test-IBAN wurde nicht zurückgegeben"

def test_update(test_app):
    """Testet das Aktualisieren von Datensätzen"""
    with test_app.app_context():
        # Update some records and multiple fields
        data = {'currency': 'USD', 'category': 'Updated'}
        query = [
            {'key': 'uuid', 'value': '13d505688ab3b940dbed47117ffddf95'},
            {'key': 'text_tx', 'value': 'Wucherpfennig', 'compare': 'like'}
        ]
        updated_db = test_app.host.db_handler.update(data, 'DE89370400440532013000',
                                                     query, multi='OR')
        update_two = updated_db.get('updated')
        assert update_two == 2, \
            f'Es wurde nicht die richtige Anzahl geupdated (update_two): {update_two}'

        result_one = test_app.host.db_handler.select("DE89370400440532013000", condition=query)
        for entry in result_one:
            check_entry(entry, data)

        # Update all with one field
        data = {'art': 'Überweisung'}
        updated_db = test_app.host.db_handler.update(data, 'DE89370400440532013000', merge=False)
        update_all = updated_db.get('updated')
        assert update_all == 5, \
            f'Es wurde nicht die richtige Anzahl geupdated (update_all): {update_all}'

        result_all = test_app.host.db_handler.select("DE89370400440532013000")
        for entry in result_all:
            check_entry(entry, data)

        # Update one set nested field
        data = {'parsed': {'Mandatsreferenz': 'M1111111'}}
        query = {'key': 'uuid', 'value': 'ba9e5795e4029213ae67ac052d378d84'}
        updated_db = test_app.host.db_handler.update(data, 'DE89370400440532013000', query)
        update_nested = updated_db.get('updated')
        assert update_nested == 1, \
            f'Es wurde nicht die richtige Anzahl geupdated (update_nested): {update_nested}'

        result_nested = test_app.host.db_handler.select("DE89370400440532013000", condition=query)
        data['uuid'] = 'ba9e5795e4029213ae67ac052d378d84'
        for entry in result_nested:
            check_entry(entry, data)


def test_select_nested(test_app):
    """Testet das Auslesen von verschachtelten Datenätzen"""
    with test_app.app_context():
        query = {'key': {'parsed': 'Mandatsreferenz'}, 'value': 'M1111111'}
        result_filtered = test_app.host.db_handler.select("DE89370400440532013000", condition=query)
        assert len(result_filtered) == 1, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry, {'uuid': 'ba9e5795e4029213ae67ac052d378d84'})


def test_set_metadata(test_app):
    """Testet das Setzen von Metadaten"""
    with test_app.app_context():
        # Metadaten setzen
        metadata = {
            "uuid": "1234567890",
            "name": "Wild Regex",
            "metatype": "parser",
            "regex": "Mandatsref\\:\\s?([A-z0-9]*)"
        }
        set_metadata = test_app.host.db_handler.set_metadata(metadata)
        assert set_metadata.get('inserted') == 1, "Die Metadaten konnten nicht gesetzt werden"

        # Overwrite with the same entry
        set_metadata = test_app.host.db_handler.set_metadata(metadata)
        assert set_metadata.get('inserted') == 1, "Die Metadaten wurde nicht überschrieben"

        # Do not overwrite equal uuids
        set_metadata = test_app.host.db_handler.set_metadata(metadata, overwrite=False)
        assert set_metadata.get('inserted') == 0, "Die Metadaten wurden überschrieben"

        # Set a group
        metadata = {
            "metatype": "config",
            "name": "group",
            "groupname": "testgroup",
            "ibans": [
                "DE89370400440532013000",
                'DE89370400440532011111'
            ],
            "members": [
                { "user": "anna", "role": "owner" },
                { "user": "bob", "role": "viewer" }
            ]
        }
        set_metadata = test_app.host.db_handler.set_metadata(metadata)
        assert set_metadata.get('inserted') == 1, "Die Gruppe wurd enict gespeichert"


def test_get_metadata(test_app):
    """Testet das Auslesen eines bestimmten Metadatums"""
    with test_app.app_context():
        # Metadaten abfragen
        metadata = test_app.host.db_handler.get_metadata(uuid='1234567890')
        assert metadata is not None, "Es wurden keine Metadaten zurückgegeben"
        assert isinstance(metadata, dict), "Metadaten sind keine LisDictte"
        assert metadata.get('uuid') == '1234567890', "Es wurden der falsche Eintrag geladen"


def test_filter_metadata(test_app):
    """Testet das Filtern von Metadaten"""
    with test_app.app_context():
        # Metadaten abfragen
        metadata = test_app.host.db_handler.filter_metadata({'key': 'name', 'value': 'Wild Regex'})
        assert metadata is not None, "Es wurden keine Metadaten zurückgegeben"
        assert isinstance(metadata, list), "Metadaten sind keine Liste"
        assert len(metadata) == 1, "Es wurden nicht die erwarteten Metadaten zurückgegeben"
        assert metadata[0].get('uuid') == '1234567890', "Es wurden der falsche Eintrag geladen"


def test_select_all_group(test_app):
    """Testet das Auslesen von allen Datensätzen aller IBANs einer Gruppe"""
    with test_app.app_context():
        # Alles selektieren mit Gruppierung
        result_all_group = test_app.host.db_handler.select('testgroup')
        assert len(result_all_group) == 7, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_all_group)}"
        for entry in result_all_group:
            check_entry(entry)


def test_select_group_filter(test_app):
    """Selektiert in allen IBANs einer Gruppe Einträge anhand eines Filters"""
    with test_app.app_context():
        query = {'key': 'amount', 'compare': '<', 'value': -100}
        result_filtered = test_app.host.db_handler.select('testgroup', condition=query)

        # 2 aus IBAN 1 + 1 aus IBAN 2
        assert len(result_filtered) == 3, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)


def test_min_max_count(test_app):
    """Testet die Min-, Max- und Count-Funktionen"""
    with test_app.app_context():
        stats = test_app.host.db_handler.min_max_collection('DE89370400440532013000', 'amount')
        assert stats.get('min') == -221.98, f"Der minimale Betrag ist falsch: {stats.get('min')}"
        assert stats.get('max') == -11.63, f"Der maximale Betrag ist falsch: {stats.get('max')}"
        assert stats.get('count') == 5, f"Die Anzahl der Einträge ist falsch: {stats.get('count')}"


def test_delete(test_app):
    """Testet das Löschen von Datensätzen"""
    with test_app.app_context():
        # Einzelnen Datensatz löschen
        query = {'key': 'uuid', 'value': '13d505688ab3b940dbed47117ffddf95'}
        deleted_db = test_app.host.db_handler.delete('DE89370400440532013000', query)
        delete_one = deleted_db.get('deleted')
        assert delete_one == 1, \
            f'Es wurde nicht die richtige Anzahl an Datensätzen gelöscht: {delete_one}'

        # Mehrere Datensätze löschen
        query = [
            {'key': 'currency', 'value': 'EUR'},
            {'key': 'currency', 'value': 'USD'}
        ]
        deleted_db = test_app.host.db_handler.delete('DE89370400440532013000', query, multi='OR')
        delete_many = deleted_db.get('deleted')
        assert delete_many == 4, \
            f'Es wurde nicht die richtige Anzahl an Datensätzen gelöscht: {delete_many}'
