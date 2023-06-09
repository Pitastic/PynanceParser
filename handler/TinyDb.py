#!/usr/bin/python3 # pylint: disable=invalid-name
"""Datenbankhandler für die Interaktion mit einer TinyDB Datenbankdatei."""

import os
import cherrypy
from tinydb import TinyDB, Query


class TinyDbHandler():
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
            condition (dict): Beding als Dictionary {'key': Schlüssel, 'value': Wert}
        Returns:
            list: Liste der ausgewählten Datensätze
        """
        if table is None:
            table = cherrypy.request.app.config['account']['iban']
        table = self.connection.table(table)
        if condition is None:
            return table.all()
        condition = Query()[condition['key']] == condition['value']
        return self.connection.search(condition)

    def insert(self, data, table=None):
        """
        Fügt einen oder mehrere Datensätze in die Datenbank ein.

        Args:
            data (dict or list): Einzelner Datensatz oder eine Liste von Datensätzen
            table (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
        Returns:
            list: Liste mit den neu eingefügten IDs
        """
        if table is None:
            table = cherrypy.request.app.config['account']['iban']
        table = self.connection.table(table)

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
            table = cherrypy.request.app.config['account']['iban']
        table = self.connection.table(table)
        if condition is not None:
            condition = Query()[condition['key']] == condition['value']
        else:
            condition = Query().noop()
        return self.connection.update(data, condition)

    def delete(self, condition=None, table=None):
        """
        Löscht Datensätze in der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            condition (dict, optional): Beding als Dictionary {'key': Schlüssel, 'value': Wert}
            table (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
        Returns:
            int: Anzahl der gelöschten Datensätze
        """
        if table is None:
            table = cherrypy.request.app.config['account']['iban']
        table = self.connection.table(table)
        if condition is not None:
            condition = Query()[condition['key']] == condition['value']
        else:
            condition = Query().noop()
        return self.connection.remove(condition)
