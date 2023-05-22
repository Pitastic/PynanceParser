#!/usr/bin/python3 # pylint: disable=invalid-name
"""Datenbankhandler für die Interaktion mit einer MongoDB."""

import pymongo


class MongoDbHandler:
    """
    Handler für die Interaktion mit einer TinyDB Datenbank.
    """
    def __init__(self, config, logger):
        """
        Initialisiert den MongoDB-Handler und Verbinden zum Datenbankserver.

        Args:
            config (object): Config Objekt der Hauptinstanz
            logger (object): Logger Objekt der Hauptinstanz
        """
        self.config = config
        self.logger = logger
        self.client = pymongo.MongoClient(self.config['DB']['uri'])
        self.connection = self.client[self.config['DB']['name']]

    def select(self, collection=None, condition=None):
        """
        Selektiert Datensätze aus der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
            condition (dict): Beding als Dictionary {'key': Schlüssel, 'value': Wert}
        Returns:
            list: Liste der ausgewählten Datensätze
        """
        if collection is None:
            collection = self.config['DEFAULT']['iban']
        collection = self.connection[collection]
        if condition is None:
            query = {}
        else:
            query = { condition['key']: condition['value'] }
        return collection.find(query)

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
            list: Liste mit den neu eingefügten IDs
        """
        if collection is None:
            collection = self.config['DEFAULT']['iban']
        collection = self.connection[collection]

        if isinstance(data, list):
            result = collection.insert_many(data)
            return result.inserted_ids

        result = collection.insert_one(data)
        return [result.inserted_id]

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
            collection = self.config['DEFAULT']['iban']
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
            collection = self.config['DEFAULT']['iban']
        collection = self.connection[collection]
        if condition is None:
            query = {}
        else:
            query = { condition['key']: condition['value'] }
        collection.delete_many(query)
