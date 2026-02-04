#!/usr/bin/python3 # pylint: disable=invalid-name
"""Datenbankhandler für die Interaktion mit einer MongoDB."""

import re
import logging
from flask import current_app
import pymongo

from handler.BaseDb import BaseDb


class MongoDbHandler(BaseDb):
    """
    Handler für die Interaktion mit einer TinyDB Datenbank.
    """
    def __init__(self):
        """
        Initialisiert den MongoDB-Handler und Verbinden zum Datenbankserver.
        """
        logging.info("Starting MongoDB Handler...")
        self.client = pymongo.MongoClient(current_app.config['DATABASE_URI'])
        self.connection = self.client[current_app.config['DATABASE_NAME']]
        if self.connection is None:
            raise IOError(f"Store {current_app.config['DATABASE_NAME']} not found !")

        super().__init__()

    def create(self):
        """
        Erstellt eine Collection je Konto und legt Indexes/Constraints fest.
        Außerdem wird die Collection für Metadaten erstellt, falls sie noch nicht existiert.
        """
        # Collection für Metadaten
        if 'metadata' not in self.connection.list_collection_names():
            self.connection.create_collection('metadata')
            self.connection['metadata'].create_index(
                [("uuid", pymongo.TEXT)], unique=True
            )

    def _select(self, collection: list, condition=None, multi='AND'):
        """
        Selektiert Datensätze aus der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            collection, list:               Name der Collection oder Liste von Collections,
                                            deren Werte selecktiert werden sollen.
                                            Default: IBAN aus der Config.
            condition (dict | list(dict)):  Bedingung als Dictionary
                - 'key', str:               Spalten- oder Schlüsselname,
                - 'value', str|int|list:    Wert der bei 'key' verglichen werden soll
                - 'compare', str:           (optional, default '==')
                    - '[==, !=, <, >, <=, >=, in, notin, all]':
                                            Wert aus DB [compare] value (Operatoren, s. Models.md)
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
            col = self.connection[col]
            db_result = list(col.find(query))

            if db_result:
                # Remove the internal ObjectId
                for row in db_result:
                    del row['_id']
                    result.append(row)

        return result

    def _insert(self, data: dict|list[dict], collection: str):
        """
        Fügt einen oder mehrere Datensätze in die Datenbank ein.

        Args:
            data (dict or list): Einzelner Datensatz oder eine Liste von Datensätzen
            collection (str): Name der Collection, in die Werte eingefügt werden sollen.
        Returns:
            dict:
                - inserted, int: Zahl der neu eingefügten IDs
        """
        # Da eine collection mit dem ersten Insert erstellt wird,
        # muss ggf. direkt der Index zunächst gesetzt werden.
        if collection not in self._get_collections():
            self.connection[collection].create_index(
                [("uuid", pymongo.TEXT)], unique=True
            )

        if isinstance(data, list):
            # Insert Many (INSERT IGNORE)
            try:
                result = self.connection[collection].insert_many(data, ordered=False)
                return {'inserted': len(result.inserted_ids)}

            except pymongo.errors.BulkWriteError as e:
                inserted = e.details.get('nInserted')
                logging.info(f"Dropping Duplicates, just INSERT {inserted}")
                return {'inserted': inserted}

        # INSERT One
        try:
            result = self.connection[collection].insert_one(data)
            return {'inserted': 1}

        except pymongo.errors.BulkWriteError:
            return {'inserted': 0}

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
        collection = self.connection[collection]

        # Form condition into a query
        query = self._form_complete_query(condition, multi)

        # Handle Tag-Lists
        new_tags = data.get('tags')
        if new_tags and merge:
            # care about the right format
            if not isinstance(new_tags, list):
                data['tags'] = [new_tags]

            # Clean $set data from tags
            del data['tags']

            # Define Operation
            update_op = {
                '$set': data,
                '$addToSet': {'tags': {'$each': new_tags}}
            }

        else:
            update_op = {'$set': data}

        update_result = collection.update_many(query, update_op)
        return {'updated': update_result.modified_count}

    def _delete(self, collection, condition=None, multi='AND'):
        """
        Löscht Datensätze in der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            collection (str): Name der Collection, in die Werte eingefügt werden sollen.
            condition (dict | list of dicts): Bedingung als Dictionary
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
        collection = self.connection[collection]

        # Form condition into a query
        query = self._form_complete_query(condition, multi)

        delete_result = collection.delete_many(query)
        return {'deleted': delete_result.deleted_count}

    def _truncate(self, collection):
        """
        Löscht eine Tabelle/Collection

        Args:
            collection (str):   Name der Collection, in die Werte eingefügt werden sollen.
        Returns:
            dict:
                - deleted, int: Anzahl der gelöschten Datensätze
        """
        return self.delete(collection=collection)

    def get_metadata(self, uuid):
        collection = self.connection['metadata']
        result = collection.find_one({'uuid': uuid})
        if result:
            # Remove the internal ObjectId
            del result['_id']

        return result

    def filter_metadata(self, condition, multi='AND'):
        collection = self.connection['metadata']
        query = self._form_complete_query(condition, multi)
        result = list(collection.find(query))

        if result:
            # Remove the internal ObjectId
            for r in result:
                del r['_id']

        return result

    def set_metadata(self, entry, overwrite=True):
        # Set uuid if not present
        if not entry.get('uuid'):
            entry = self._generate_unique_meta(entry)

        collection = self.connection['metadata']

        if overwrite:
            # Remove Entry if exists
            result = collection.delete_one({'uuid': entry.get('uuid')})

            # Insert new Entry
            result = collection.insert_one(entry)
            return {'inserted': (1 if result else 0)}

        # Only insert if not exists
        if not collection.find_one({'uuid': entry.get('uuid')}):
            result = collection.insert_one(entry)
            return {'inserted': (1 if result else 0)}

        return {'inserted': 0}

    def _form_condition(self, condition):
        """
        Erstellt aus einem Condition-Dict eine entsprechende Query

        Args:
            condition (dict): Query Dictionary ( siehe .select() )
        Returns:
            dict: Query-Dict für die Querymethode
        """
        query = {}
        if condition is None:
            return query

        # Standard Query
        stmt = condition.get('value') # default method '=='
        condition_method = condition.get('compare', '==')

        # Regex Suche
        if condition_method.lower() == 'regex':
            stmt = re.compile(str(condition.get('value')))

        # Like Suche
        if condition_method.lower() == 'like':
            escaped_condition = re.escape(condition.get('value'))
            stmt = re.compile(f".*{escaped_condition}.*", re.IGNORECASE)

        if condition_method == '!=':
            stmt = {'$not': {'$eq': condition.get('value')}}
        if condition_method == '>=':
            stmt = {'$gte': condition.get('value')}
        if condition_method == '<=':
            stmt = {'$lte': condition.get('value')}
        if condition_method == '>':
            stmt = {'$gt': condition.get('value')}
        if condition_method == '<':
            stmt = {'$lt': condition.get('value')}
        if condition_method == 'in':
            stmt = {'$in': condition.get('value')}
        if condition_method == 'notin':
            stmt = {'$nin': condition.get('value')}
        if condition_method == 'all':
            stmt = {'$all': condition.get('value')}

        # Nested or Plain Key
        condition_key = condition.get('key')
        if isinstance(condition_key, dict):
            for key, val in condition_key.items():
                query = { f'{key}.{val}' : stmt }
                break
        else:
            query = { condition_key: stmt }

        return query

    def _form_complete_query(self, condition, multi='AND'):
        """
        Erstellt ein Query Objekt aus ein oder mehreren Conditions.

        Args:
            condition (dict | list of dicts): Bedingung als Dictionary
            multi (str) : ['AND' | 'OR'] Wenn 'condition' eine Liste mit conditions ist,
                          werden diese logisch wie hier angegeben verknüpft. Default: 'AND'
        Returns:
            dict: MongoDB Query dict
        """
        operator = '$or' if multi.upper() == 'OR' else '$and'
        if isinstance(condition, list) and len(condition) == 1:
            # single filter in list
            condition = condition[0]

        # Single or Multi Conditions
        if isinstance(condition, list):
            formed_conditions = []
            prio_query = None

            for c in condition:
                if c.get('key') == 'prio':
                    # Special handle prio (seek and save here)
                    prio_query = self._form_condition(c)
                    continue

                formed_conditions.append(self._form_condition(c))

            if len(formed_conditions) == 1:
                # prio + just one other filter (was len(2) before)
                query = {
                    '$and': [
                        prio_query,
                        formed_conditions[0]
                    ]
                }

            else:

                if prio_query is None:
                    # multiple filters without prio
                    query = {operator: formed_conditions}

                else:
                    # prio + more than one other filter
                    query = {
                        '$and': [
                            prio_query,
                            {operator: formed_conditions}
                        ]
                    }

        else:
            # single filter
            query = self._form_condition(condition)

        return query

    def _get_collections(self):
        """
        Liste alle collections der Datenbank.

        Returns:
            list: A list of collection names.
        """
        return self.connection.list_collection_names()

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
        col = self.connection[collection]

        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'minValue': {'$min': f'${key}'},
                    'maxValue': {'$max': f'${key}'},
                    'count': {'$sum': 1}
                }
            }
        ]

        result = list(col.aggregate(pipeline)) or [{}]

        return {
            'min': result[0].get('minValue'),
            'max': result[0].get('maxValue'),
            'count': result[0].get('count', 0)
        }
