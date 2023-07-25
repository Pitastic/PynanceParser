#!/usr/bin/python3 # pylint: disable=invalid-name
"""Datenbankhandler für die Interaktion mit einer TinyDB Datenbankdatei."""

import os
import cherrypy
from tinydb import TinyDB, Query, where
import re

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

    def select(self, table=None, condition=None):
        """
        Selektiert Datensätze aus der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            table (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
            condition (dict): Bedingung als Dictionary
                - 'key', str    : Spalten- oder Schlüsselname,
                - 'value', any  : Wert der bei 'key' verglichen werden soll
                - 'compare', str: (optional, default '==')
                    - '[==, !=, <, >, <=, >=]': Wert asu DB [compare] value
                    - 'like'    : Wert aus DB == *value* (case insensitive)
                    - 'regex'   : value wird als RegEx behandelt
        Returns:
            list: Liste der ausgewählten Datensätze
        """
        if table is None:
            table = cherrypy.config['iban']
        table = self.connection.table(table)

        if condition is None:
            return table.all()

        #TODO: Mehr als einen Query Parameter
        condition_method = condition.get('compare', '==')
        if condition_method == 'regex':
            # RegEx Suche
            return table.search(
                where(condition.get('key')) \
                .search(condition.get('value'))
            )

        if condition_method == 'like':
            # Like Suche
            test_contains = lambda value, search: search.lower() in value.lower()
            return table.search(
                where(condition.get('key')) \
                .test(test_contains, condition.get('value'))
            )

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
        
        return table.search(where_statement)

    def insert(self, data, collection=None):
        """
        Fügt einen oder mehrere Datensätze in die Datenbank ein.

        Args:
            data (dict or list): Einzelner Datensatz oder eine Liste von Datensätzen
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                        Default: IBAN aus der Config.
        Returns:
            list: Liste mit den neu eingefügten IDs
        """
        if collection is None:
            collection = cherrypy.config['iban']
        table = self.connection.table(collection)

        # Add generated IDs
        data = self.generate_unique(data)

        if isinstance(data, list):
            result = table.insert_multiple(data)
            return result

        result = table.insert(data)
        return [result]

    def update(self, data, condition=None, table=None):
        """
        Aktualisiert Datensätze in der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            data (dict): Aktualisierte Daten für die passenden Datensätze
            condition (dict, optional): Beding als Dictionary {'key': Schlüssel, 'value': Wert}
            table (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
        Returns:
            int: Anzahl der aktualisierten Datensätze
        """
        if table is None:
            table = cherrypy.config['iban']
        table = self.connection.table(table)
        if condition is not None:
            condition = Query()[condition['key']] == condition['value']
        else:
            condition = Query().noop()
        return self.connection.update(data, condition)

    def delete(self, condition, collection=None):
        """
        Löscht Datensätze in der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            condition (dict, optional): Bedingung als Dictionary {'key': Schlüssel, 'value': Wert}
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
        Returns:
            int: Anzahl der gelöschten Datensätze
        """
        if collection is None:
            collection = cherrypy.config['iban']
        collection = self.connection.table(collection)
        condition = Query()[condition['key']] == condition['value']
        deleted_ids = self.connection.remove(condition)
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
        return len(table.remove(lambda x: True))