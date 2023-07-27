#!/usr/bin/python3 # pylint: disable=invalid-name
"""Datenbankhandler für die Interaktion mit einer MongoDB."""

import re
import cherrypy
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
        cherrypy.log("Starting MongoDB Handler...")
        self.client = pymongo.MongoClient(cherrypy.config['database.uri'])
        self.connection = self.client[cherrypy.config['database.name']]
        if self.connection is None:
            raise IOError(f"Store {cherrypy.config['database.name']} not found !")
        self.create()

    def create(self):
        """
        Erstellt eine Collection je Konto und legt Indexes/Constraints fest
        """
        self.connection[cherrypy.config['iban']].create_index(
            [("hash", pymongo.TEXT)], unique=True
        )

    def select(self, collection=None, condition=None, multi='AND'):
        """
        Selektiert Datensätze aus der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                        Default: IBAN aus der Config.
            condition (dict): Bedingung als Dictionary
                - 'key', str    : Spalten- oder Schlüsselname,
                - 'value', any  : Wert der bei 'key' verglichen werden soll
                - 'compare', str: (optional, default '==')
                    - '[==, !=, <, >, <=, >=]': Wert asu DB [compare] value
                    - 'like'    : Wert aus DB == *value* (case insensitive)
                    - 'regex'   : value wird als RegEx behandelt
            multi (str) : ['AND' | 'OR'] Wenn 'condition' eine Liste mit conditions ist,
                          werden diese logisch wie hier angegeben verknüpft. Default: 'AND'
        Returns:
            list: Liste der ausgewählten Datensätze
        """
        if collection is None:
            collection = cherrypy.config['iban']
        collection = self.connection[collection]

        # Single or Multi Conditions
        if isinstance(condition, list):
            operator = '$or' if multi.upper() == 'OR' else '$and'
            query = {operator: []}
            for c in condition:
                query[operator].append(self._form_query(c))

        else:
            query = self._form_query(condition)

        return list(collection.find(query))

    def insert(self, data, collection=None):
        """
        Fügt einen oder mehrere Datensätze in die Datenbank ein.

        Args:
            data (dict or list): Einzelner Datensatz oder eine Liste von Datensätzen
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                        Default: IBAN aus der Config.
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
        Returns:
            int: Zahl der neu eingefügten IDs
        """
        if collection is None:
            collection = cherrypy.config['iban']
        collection = self.connection[collection]

        # Add generated IDs
        data = self.generate_unique(data)

        if isinstance(data, list):
            # Insert Many (INSERT IGNORE)
            try:
                result = collection.insert_many(data, ordered=False)
                return len(result.inserted_ids)
            except pymongo.errors.BulkWriteError as e:
                inserted = e.details.get('nInserted')
                cherrypy.log(f"Dropping Duplicates, just INSERT {inserted}")
                return inserted

        # INSERT One
        try:
            result = collection.insert_one(data)
            return 1
        except pymongo.errors.BulkWriteError:
            return 0

    def update(self, data, condition=None, collection=None):
        """
        Aktualisiert Datensätze in der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            data (dict): Aktualisierte Daten für die passenden Datensätze
            condition (dict, optional): Beding als Dictionary {'key': Schlüssel, 'value': Wert}
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
        Returns:
            int: Anzahl der aktualisierten Datensätze
        """
        if collection is None:
            collection = cherrypy.config['iban']
        collection = self.connection[collection]
        if condition is None:
            query = {}
        else:
            query = { condition['key']: condition['value'] }
        return collection.update_many(query, {'$set': data})

    def delete(self, condition=None, collection=None):
        """
        Löscht Datensätze in der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            condition (dict): Beding als Dictionary {'key': Schlüssel, 'value': Wert}
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
        Returns:
            int: Anzahl der gelöschten Datensätze
        """
        if collection is None:
            collection = cherrypy.config['iban']
        collection = self.connection[collection]
        if not condition:
            query = {}
        else:
            query = { condition['key']: condition['value'] }
        return collection.delete_many(query).deleted_count

    def truncate(self, collection=None):
        """
        Löscht alle Datensätze aus einer Tabelle/Collection

        Args:
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: None -> Default der delete Methode
        Returns:
            int: Anzahl der gelöschten Datensätze                        
        """
        return self.delete(condition={}, collection=collection)

    def _form_query(self, condition):
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

        condition_method = condition.get('compare', '==')

        if condition_method.lower() == 'regex':
            # Regex Suche
            rx = re.compile(condition.get('value'))
            query[condition.get('key')] = rx

        if condition_method.lower() == 'like':
            # Like Suche
            escaped_condition = re.escape(condition.get('value'))
            rx = re.compile(f".*{escaped_condition}.*", re.IGNORECASE)
            query[condition.get('key')] = rx

        # Standard Query
        if condition_method == '==':
            query[condition.get('key')] = condition.get('value')
        if condition_method == '!=':
            query[condition.get('key')] = {'$not': {'$eq': condition.get('value')}}
        if condition_method == '>=':
            query[condition.get('key')] = {'$gte': condition.get('value')}
        if condition_method == '<=':
            query[condition.get('key')] = {'$lte': condition.get('value')}
        if condition_method == '>':
            query[condition.get('key')] = {'$gt': condition.get('value')}
        if condition_method == '<':
            query[condition.get('key')] = {'$lt': condition.get('value')}

        return query
