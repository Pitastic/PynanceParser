#!/usr/bin/python3 # pylint: disable=invalid-name
"""Datenbankhandler für die Interaktion mit einer TinyDB Datenbankdatei."""

import os
import operator
import logging
import re
from tinydb import TinyDB, Query, where, JSONStorage, middlewares
from flask import current_app
import portalocker

from handler.BaseDb import BaseDb


class FileLockMiddleware(middlewares.Middleware):
    """
    Middleware Klasse für die TinyDB Instanz, die vor jeder Operation ihre Methoden ausführen kann
    (siehe: https://tinydb.readthedocs.io/en/latest/_modules/tinydb/middlewares.html).
    Sie wird hier für ein Datei-Locking benötigt, um parallele (Flask) Requests 
    auf die TindyDB zu ermöglichen.
    """
    def __init__(self, storage_cls):
        super().__init__(storage_cls)
        self.lock_file = os.path.join(current_app.config['DATABASE_URI'], 'db.lock')

    def read(self):
        """Hook into the database read operation with file locking."""
        with portalocker.Lock(self.lock_file, timeout=5):
            return self.storage.read()

    def write(self, data):
        """Hook into the database write operation with file locking."""
        with portalocker.Lock(self.lock_file, timeout=5):
            self.storage.write(data)


class TinyDbHandler(BaseDb):
    """
    Handler für die Interaktion mit einer TinyDB Datenbank.
    """
    def __init__(self):
        """
        Initialisiert den TinyDB-Handler und öffnet die Datenbank.
        """
        logging.info("Starting TinyDB Handler...")
        try:
            self.connection = TinyDB(os.path.join(
                    current_app.config['DATABASE_URI'],
                    current_app.config['DATABASE_NAME']
                ),
                storage=FileLockMiddleware(JSONStorage)
            )

            if not hasattr(self, 'connection'):
                raise IOError('Es konnte kein Connection Objekt erstellt werden')

        except IOError as ex:
            logging.error(f"Fehler beim Verbindungsaufbau zur Datenbank: {ex}")

        super().__init__()

    def create(self):
        """
        Erstellt einen Table je Konto und legt Indexes/Constraints fest.
        Außerdem wird der Table für Metadaten erstellt, falls er noch nicht existiert.
        """
        # Table für Metadaten
        self.connection.table('metadata')

    def _select(self, collection: list, condition=None, multi='AND'):
        """
        Selektiert Datensätze aus der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            collection, list:               Name der Collection oder Liste von Collections,
                                            deren Werte selecktiert werden sollen.
            condition (dict | list(dicts)): Bedingung als Dictionary
                - 'key', str    :           Spalten- oder Schlüsselname,
                - 'value', str|int|list:    Wert der bei 'key' verglichen werden soll
                - 'compare', str:           (optional, default '==')
                    - '[==, !=, <, >, <=, >=, in, notin, all]':
                                            Wert asu DB [compare] value (Operatoren, s. Models.md)
                    - 'like':               Wert aus DB == *value* (case insensitive)
                    - 'regex':              value wird als RegEx behandelt
            multi, str ['AND' | 'OR']:      Wenn 'condition' eine Liste mit conditions ist,
                                            werden diese logisch wie hier angegeben verknüpft.
                                            Default: 'AND'
        Returns:
            list: Liste der ausgewählten Datensätze
        """
        # Form condition into a query
        query = self._form_complete_query(condition, multi)
        result = []

        for col in collection:
            col = self.connection.table(col)

            if query is None:
                # Get all entries from collection
                result.extend(col.all())
                continue

            # Filter by Query
            result.extend(col.search(query))

        return result

    def _insert(self, data: dict|list[dict], collection: str):
        """
        Fügt einen oder mehrere Datensätze in die Datenbank ein.

        Args:
            data (dict or list): Einzelner Datensatz oder eine Liste von Datensätzen
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                        Default: IBAN aus der Config.
        Returns:
            dict:
                - inserted, int: Zahl der neu eingefügten IDs
        """
        # Da es keine Unique contraints in TinyDB gibt,
        # müssen die Datensätze zuvor vin der DB gesucht
        # und Duplikate anschließend gefiltert werden.
        duplicates = self._double_check(collection, data)

        # Insert Many (INSERT IGNORE)
        if isinstance(data, list):

            # Pop duplicates from list
            unique_data = []
            for d in data:
                if d.get('uuid') not in duplicates:
                    # Add to unique
                    unique_data.append(d)

            # No non-duplicates in data
            if not unique_data:
                return {'inserted': 0}

            # Insert remaining data
            result = self.connection.table(collection).insert_multiple(unique_data)
            return {'inserted': len(result)}

        # INSERT One
        if data.get('uuid') in duplicates:
            # Don't insert duplicate
            logging.info(f'Not inserting Duplicate \'{data.get("uuid")}\'')
            return {'inserted': 0}

        result = self.connection.table(collection).insert(data)
        return {'inserted': (1 if result else 0)}

    def _update(self, data, collection, condition=None, multi='AND', merge=True):
        """
        Aktualisiert Datensätze in der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            data (dict): Aktualisierte Daten für die passenden Datensätze
            collection (str):   Name der Collection, in die Werte eingefügt werden sollen.
            condition (dict | list(dict)): Bedingung als Dictionary
                - 'key', str    : Spalten- oder Schlüsselname,
                - 'value', any  : Wert der bei 'key' verglichen werden soll
                - 'compare', str: (optional, default '==')
                    - '[==, !=, <, >, <=, >=]': Wert asu DB [compare] value
                    - 'like'    : Wert aus DB == *value* (case insensitive)
                    - 'regex'   : value wird als RegEx behandelt
            multi (str) : ['AND' | 'OR'] Wenn 'condition' eine Liste mit conditions ist,
                          werden diese logisch wie hier angegeben verknüpft. Default: 'AND'
            merge (bool): Wenn False, werden Listenfelder nicht gemerged, sondern
                          komplett überschrieben. Default: True
        Returns:
            dict:
                - updated, int: Anzahl der aktualisierten Datensätze
        """
        # run update
        docs_to_update = self.select(collection, condition, multi)
        if not docs_to_update:
            # No match, no update
            return { 'updated': 0 }

        collection = self.connection.table(collection)

        # care about the right format
        if data.get('tags') is not None and not isinstance(data.get('tags'), list):
            data['tags'] = [data.get('tags')]

        # Result store for updated uuids
        update_result = []

        # Form condition into a query
        if condition is None and merge:
            logging.error('Using "merge" without a query is not possible')
            return { 'error': 'Using "merge" without a query is not possible', 'updated': 0 }

        elif condition is None:
            query = Query().noop()

        else:
            query = self._form_complete_query(condition, multi)

        if not merge:
            # Update all at once (no merging)
            update_result += collection.update(data, query)
            return { 'updated': len(update_result) }

        # Update every Entry one-by-one (merge every list item)
        for doc in docs_to_update:


            # Look for lists to merge with this entry
            for d in data.keys():

                if isinstance(doc.get(d), list) and merge:
                    data[d] = list(set(doc.get(d) + data[d])) 
                    continue

            # Update this uuid
            update_result += collection.update(
                data,
                self._form_complete_query({
                    'key': 'uuid',
                    'value': doc.get('uuid'),
                    'compare': '=='
                })
            )

        return { 'updated': len(update_result) }

    def _delete(self, collection, condition=None, multi='AND'):
        """
        Löscht Datensätze in der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            collection (str):   Name der Collection, in die Werte eingefügt werden sollen.
            condition (dict | list(dict)): Bedingung als Dictionary
                - 'key', str    : Spalten- oder Schlüsselname,
                - 'value', any  : Wert der bei 'key' verglichen werden soll
                - 'compare', str: (optional, default '==')
                    - '[==, !=, <, >, <=, >=]': Wert asu DB [compare] value
                    - 'like'    : Wert aus DB == *value* (case insensitive)
                    - 'regex'   : value wird als RegEx behandelt
            multi (str) : ['AND' | 'OR'] Wenn 'condition' eine Liste mit conditions ist,
                          werden diese logisch wie hier angegeben verknüpft. Default: 'AND'
        Returns:
            dict:
                - deleted, int: Anzahl der gelöschten Datensätze
        """
        collection = self.connection.table(collection)

        # Form condition into a query
        if condition is None:
            query = Query().noop()
        else:
            query = self._form_complete_query(condition, multi)

        deleted_ids = collection.remove(query)
        return {'deleted': len(deleted_ids)}

    def _truncate(self, collection):
        """Löscht eine Tabelle/Collection

        Args:
            collection (str):   Name der Collection, in die Werte eingefügt werden sollen.
        Returns:
            dict:
                - deleted, int: Anzahl der gelöschten Datensätze
        """
        self.connection.drop_table(collection)
        return {'deleted': 1}

    def get_metadata(self, uuid):
        collection = self.connection.table('metadata')
        result = collection.get(Query().uuid == uuid)
        return result

    def filter_metadata(self, condition, multi='AND'):
        collection = self.connection.table('metadata')
        if condition is None:
            # Return all
            return collection.all()

        # Form condition into a query
        query = self._form_complete_query(condition, multi)
        results = collection.search(query)
        return results

    def set_metadata(self, entry, overwrite=True):
        # Set uuid if not present
        if not entry.get('uuid'):
            entry = self._generate_unique_meta(entry)

        collection = self.connection.table('metadata')

        if overwrite:
            # Remove Entry if exists
            collection.remove(Query().uuid == entry.get('uuid'))

            # Insert new Entry
            result = collection.insert(entry)
            return {'inserted': (1 if result else 0)}

        # Only insert if not exists
        if not collection.search(Query().uuid == entry.get('uuid')):
            result = collection.insert(entry)
            return {'inserted': (1 if result else 0)}

        return {'inserted': 0}

    def _form_where(self, condition):
        """
        Erstellt aus einem Condition-Dict eine entsprechende Query

        Args:
            condition (dict): Query Dictionary ( siehe .select() )
        Returns:
            dict: Query-Dict für die Querymethode
        """
        if condition is None:
            return None

        condition_method = condition.get('compare', '==')
        condition_key = condition.get('key')
        condition_val = condition.get('value')

        if isinstance(condition_val, list):
            # All types in query have to be hashable in TinyDB
            condition_val = tuple(condition_val)

        # Nested or Plain Key
        if isinstance(condition_key, dict):
            for key, val in condition_key.items():
                where_statement = where(key)[val]
                break
        else:
            where_statement = where(condition_key)

        # RegEx Suche
        if condition_method == 'regex':
            condition_val = re.compile(str(condition_val))
            where_statement = where_statement.search(condition_val)
            return where_statement

        # Like Suche
        if condition_method == 'like':
            def test_contains(value, search):
                return search.lower() in value.lower()

            where_statement = where_statement.test(test_contains, condition_val)
            return where_statement

        # List Queries
        if condition_method == 'in':
            where_statement = where_statement.any(condition_val)
        if condition_method == 'notin':
            where_statement = where_statement.test(self._none_of_test, condition_val)
        if condition_method == 'all':
            where_statement = where_statement.all(condition_val)

        # Standard Query
        try:
            # Transfer to a number for comparison
            condition_val = float(condition_val)
        except (TypeError, ValueError):
            pass

        if condition_method == '==':
            where_statement = where_statement == condition_val
        if condition_method == '!=':
            where_statement = where_statement != condition_val
        if condition_method == '>=':
            where_statement = where_statement >= condition_val
        if condition_method == '<=':
            where_statement = where_statement <= condition_val
        if condition_method == '>':
            where_statement = where_statement > condition_val
        if condition_method == '<':
            where_statement = where_statement < condition_val

        return where_statement

    def _form_complete_query(self, condition, multi='AND'):
        """
        Erstellt eine oder mehrere Query Objekte und
        verkettet diese entprechend für eine Abfrage

        Args:
            condition (dict | list of dicts): Bedingung als Dictionary
            multi (str) : ['AND' | 'OR'] Wenn 'condition' eine Liste mit conditions ist,
                          werden diese logisch wie hier angegeben verknüpft. Default: 'AND'
        Returns:
            set: Ein oder mehrere Query Objekte im set
        """
        logical_concat = operator.or_ if multi.upper() == 'OR' else operator.and_
        if isinstance(condition, list) and len(condition) == 1:
            # single filter in list
            condition = condition[0]

        if isinstance(condition, list):
            # Multi condition
            query = None
            where_statements = []
            prio_query = None

            # Create every where_statement from condition
            for c in condition:
                if c.get('key') == 'prio':
                    # Special handle prio (seek and save here)
                    prio_query = self._form_where(c)
                    continue

                where_statements.append(self._form_where(c))

            # Concat conditions logical
            for w in where_statements:
                if query is None:
                    query = w
                    continue

                query = logical_concat(query, w)

            if prio_query:
                # prio + other filter(s)
                query = operator.and_(query, prio_query)

        else:
            # Single condition
            query = self._form_where(condition)

        return query

    def _double_check(self, collection: str, data: list|dict):
        """
        Prüft anhand der unique IDs einer Transaktion,
        ob diese schon in der Datenbank vorhanden ist

        Args:
            collection (str): Name der Collection, in der die Werte geprüft werden sollen.
            data (dict | list of dicts): Zu prüfende Transaktionen (inkl. ID)
        Returns:
            list: Liste der IDs, die sich bereits in der Datenbank befinden
        """
        if isinstance(data, list):
            query = [{'key': 'uuid', 'value': d.get('uuid')} for d in data]
        else:
            query = {'key': 'uuid', 'value': data.get('uuid')}

        results = self.select(collection=collection, condition=query, multi='OR')
        duplicate_ids = [r.get('uuid') for r in results]

        return duplicate_ids

    def _none_of_test(self, value, forbidden_values):
        """Benutzerdefinierter Test: Keines der Elemente ist in einer Liste vorhanden"""
        return not any(item in forbidden_values for item in value)

    def _get_collections(self):
        """
        Liste alle tables der Datenbank.

        Returns:
            list: A list of table names.
        """
        return self.connection.tables()

    def min_max_collection(self, collection: str, key: str):
        """
        Bestimmt den minimalen und maximalen Wert eines Keys in einer Collection
        sowie die Anzahl der Einträge.

        Args:
            collection (str): Name der Collection.
            key (str): Key, für den min/max/count bestimmt werden soll.
        Returns:
            dict:
                - min, any: Minimaler Wert
                - max, any: Maximaler Wert
                - count, int: Anzahl der Einträge
        """
        all_entries = self.select(collection)
        all_values = [entry.get(key) for entry in all_entries if entry.get(key) is not None]
        return {
            'min': min(all_values),
            'max': max(all_values),
            'count': len(all_entries)
        }
