#!/usr/bin/python3 # pylint: disable=invalid-name
"""Datenbankhandler für die Interaktion mit einer TinyDB Datenbankdatei."""

import os
import operator
import cherrypy
from tinydb import TinyDB, Query, where

from handler.BaseDb import BaseDb


class TinyDbHandler(BaseDb):
    """
    Handler für die Interaktion mit einer TinyDB Datenbank.
    """
    def __init__(self):
        """
        Initialisiert den TinyDB-Handler und öffnet die Datenbank.
        """
        cherrypy.log("Starting TinyDB Handler...")
        try:
            self.connection = TinyDB(os.path.join(
                cherrypy.config['database.uri'],
                cherrypy.config['database.name']
            ))
            if not hasattr(self, 'connection'):
                raise IOError('Es konnte kein Connection Objekt erstellt werden')
        except IOError as ex:
            cherrypy.log.error(f"Fehler beim Verbindungsaufbau zur Datenbank: {ex}")
        self.create()

    def create(self):
        """
        Erstellt einen Table je Konto und legt Indexes/Constraints fest
        """
        # Touch Table
        self.connection.table(cherrypy.config['iban'])

    def select(self, collection=None, condition=None, multi='AND'):
        """
        Selektiert Datensätze aus der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
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
            list: Liste der ausgewählten Datensätze
        """
        if collection is None:
            collection = cherrypy.config['iban']
        collection = self.connection.table(collection)

        # Form condition into a query
        query = self._form_complete_query(condition, multi)

        if query is None:
            return collection.all()

        return collection.search(query)

    def insert(self, data, collection=None):
        """
        Fügt einen oder mehrere Datensätze in die Datenbank ein.

        Args:
            data (dict or list): Einzelner Datensatz oder eine Liste von Datensätzen
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                        Default: IBAN aus der Config.
        Returns:
            int: Zahl der neu eingefügten IDs
        """
        if collection is None:
            collection = cherrypy.config['iban']

        # Add generated IDs
        data = self._generate_unique(data)

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
            if not data:
                return 0

            # Insert remaining data
            result = self.connection.table(collection).insert_multiple(unique_data)
            return len(result)

        # INSERT One
        if data.get('uuid') in duplicates:
            # Don't insert duplicate
            cherrypy.log(f'Not inserting Duplicate \'{data.get("uuid")}\'')
            return 0

        result = self.connection.table(collection).insert(data)
        return 1

    def update(self, data, collection=None, condition=None, multi='AND'):
        """
        Aktualisiert Datensätze in der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            data (dict): Aktualisierte Daten für die passenden Datensätze
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
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
            int: Anzahl der aktualisierten Datensätze
        """
        if collection is None:
            collection = cherrypy.config['iban']
        collection = self.connection.table(collection)

        # Form condition into a query and run
        if condition is None:
            query = Query().noop()
        else:
            query = self._form_complete_query(condition, multi)

        # run update
        update_result = collection.update(data, query)
        return len(update_result)

    def delete(self, collection=None, condition=None, multi='AND'):
        """
        Löscht Datensätze in der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
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
            int: Anzahl der gelöschten Datensätze
        """
        if collection is None:
            collection = cherrypy.config['iban']
        collection = self.connection.table(collection)

        # Form condition into a query
        if condition is None:
            query = Query().noop()
        else:
            query = self._form_complete_query(condition, multi)

        deleted_ids = collection.remove(query)
        return len(deleted_ids)

    def truncate(self, collection=None):
        """Löscht alle Datensätze aus einer Tabelle/Collection

        Args:
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
        Returns:
            int: Anzahl der gelöschten Datensätze                        
        """
        if collection is None:
            collection = cherrypy.config['iban']
        table = self.connection.table(collection)
        r = table.remove(lambda x: True)
        return len(r)

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

        where_statement = None
        condition_method = condition.get('compare', '==')

        if condition_method == 'regex':
            # RegEx Suche
            return where(condition.get('key')) \
                   .search(condition.get('value'))

        if condition_method == 'like':
            # Like Suche
            def test_contains(value, search):
                return search.lower() in value.lower()
            return where(condition.get('key')) \
                   .test(test_contains, condition.get('value'))

        # Standard Query
        if condition_method == '==':
            where_statement = where(condition.get('key')) == condition.get('value')
        if condition_method == '!=':
            where_statement = where(condition.get('key')) != condition.get('value')
        if condition_method == '>=':
            where_statement = where(condition.get('key')) >= condition.get('value')
        if condition_method == '<=':
            where_statement = where(condition.get('key')) <= condition.get('value')
        if condition_method == '>':
            where_statement = where(condition.get('key')) > condition.get('value')
        if condition_method == '<':
            where_statement = where(condition.get('key')) < condition.get('value')

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
        # Multi condition
        if isinstance(condition, list):

            # Create every where_statement from condition
            query = None
            where_statements = []
            for c in condition:
                where_statements.append(self._form_where(c))

            if multi.upper() == 'OR':
                # Concat all where_statements with OR later
                logical_concat = operator.or_

            else:
                # Concat all where_statements with AND later
                logical_concat = operator.and_

            # Concat conditions logical
            for w in where_statements:
                if query is None:
                    query = w
                    continue
                query = logical_concat(query, w)

        else:
            # Single condition
            query = self._form_where(condition)

        return query

    def _double_check(self, collection, data):
        """
        Prüft anhand der unique IDs einer Transaktion,
        ob diese schon in der Datenbank vorhanden ist

        Args:
            collection (str, optional): Name der Collection, in der die Werte geprüft werden sollen.
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
