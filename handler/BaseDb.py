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
        """
        Selektiert Datensätze aus der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                        Default: IBAN aus der Config.
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
                - result, list: Liste der ausgewählten Datensätze
        """
        raise NotImplementedError()

    def insert(self, data, collection):
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
        raise NotImplementedError()

    def update(self, data, collection, condition, multi):
        """
        Aktualisiert Datensätze in der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            data (dict): Aktualisierte Daten für die passenden Datensätze
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
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
                - updated, int: Anzahl der aktualisierten Datensätze
        """
        raise NotImplementedError()

    def delete(self, collection, condition):
        """
        Löscht Datensätze in der Datenbank, die die angegebene Bedingung erfüllen.

        Args:
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
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
        raise NotImplementedError()

    def truncate(self, collection):
        """Löscht alle Datensätze aus einer Tabelle/Collection

        Args:
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
        Returns:
            dict:
                - deleted, int: Anzahl der gelöschten Datensätze
        """
        raise NotImplementedError()

    def _generate_unique(self, tx_entries, salt=""):
        """
        Erstellt einen einmaligen ID für jede Transaktion.

        Args:
            tx_entries (dict | list(dict)): Liste mit Transaktionsobjekten
            salt (str): Optionaler String, der zur Erstellung der ID verwendet wird.
        Returns:
            dict | list(dict): Die um die IDs ('uuid') erweiterte Eingabeliste
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
                              tx_text + \
                              salt
            md5_hash.update(combined_string.encode('utf-8'))

            # Store UUID
            transaction['uuid'] = md5_hash.hexdigest()

            # Set start Tagging priority
            transaction['prio'] = 0

        # Input List or single Dict
        if not isinstance(tx_entries, list):
            return tx_list[0]

        return tx_list

    def _generate_unique_meta(self, entry):
        """
        Generiert eine eindeutige UUID für Metadaten basierend auf dem Eintrag.
        Args:
            entry (dict): Eintrag für den die UUID generiert werden soll.
        Returns:
            dict: Das um die ID ('uuid') erweiterte Dict mit den Metadaten.
        """
        no_special_chars = re.compile("[^A-Za-z0-9]")

        # Calculate Hash
        md5_hash = hashlib.md5()
        uuid_text = f"{entry.get('type', '')}-{entry.get('name', '')}"
        uuid_text = no_special_chars.sub('', uuid_text)
        md5_hash.update(uuid_text.encode('utf-8'))

        # Store UUID
        entry['uuid'] = md5_hash.hexdigest()

        return entry

    def get_metadata(self, uuid):
        """
        Ruft Metadaten aus der Datenbank ab.

        Args:
            uuid (str): Unique ID (key).
        Returns:
            dict: Die abgerufenen Metadaten.
        """
        raise NotImplementedError()

    def filter_metadata(self, condition, multi):
        """
        Ruft Metadaten aus der Datenbank anhand von Kriterien ab.

        Args:
            condition (dict): key-value-Paare für die Filterung der Metadaten.
            multi (str) : ['AND' | 'OR'] Wenn 'condition' eine Liste mit conditions ist,
                          werden diese logisch wie hier angegeben verknüpft. Default: 'AND'
        Returns:
            dict: Die abgerufenen Metadaten.
        """
        raise NotImplementedError()

    def set_metadata(self, entry):
        """
        Speichert oder ersetzt Metadaten in der Datenbank.

        Args:
            entry (dict): Der Eintrag, der gespeichert werden soll.
        Returns:
            dict: Informationen über den Speichervorgang.
        """
        raise NotImplementedError()
