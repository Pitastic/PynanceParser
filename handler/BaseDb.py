#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisklasse für die Vererbung an Datenbankhandler mit allgemeinen Funktionen"""

import hashlib
import re


class BaseDb():
    """Basisklasse für die Vererbung an Datenbankhandler mit allgemeinen Funktionen"""

    def create(self):
        """Erstellen des Datenbankspeichers"""
        raise NotImplementedError()

    def select(self, collection, condition, multi):
        """Abfrage nach Werten aus der Datenbank"""
        raise NotImplementedError()

    def insert(self, data, collection):
        """Einfügen von Werten in die Datenbank"""
        raise NotImplementedError()

    def update(self, data, collection, condition, multi):
        """Aktualisieren von Werten in der Datenbank"""
        raise NotImplementedError()

    def delete(self, collection, condition):
        """Löschen von Werten aus der Datenbank"""
        raise NotImplementedError()

    def truncate(self, collection):
        """Löschen aller Werten aus der Datenbank"""
        raise NotImplementedError()

    def _generate_unique(self, tx_entries):
        """
        Erstellt einen einmaligen ID für jede Transaktion.

        Args:
            tx_entries (dict | list of dicts): Liste mit Transaktionsobjekten
        Returns:
            dict | list of dicts: Die um die IDs ('hash') erweiterte Eingabeliste
        """
        no_special_chars = re.compile("[^A-Za-z0-9]")

        # Input List or single Dict
        if not isinstance(tx_entries, list):
            tx_list = [tx_entries]
        else:
            tx_list = tx_entries

        for transaction in tx_list:
            md5_hash = hashlib.md5()
            tx_text = no_special_chars.sub('', transaction.get('text_tx', ''))
            combined_string = str(transaction.get('date_tx', '')) + \
                              str(transaction.get('betrag', '')) + \
                              tx_text
            md5_hash.update(combined_string.encode('utf-8'))
            transaction['hash'] = md5_hash.hexdigest()

        # Input List or single Dict
        if not isinstance(tx_entries, list):
            return tx_list[0]

        return tx_list
