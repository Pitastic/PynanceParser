#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisklasse für die Vererbung an Datenbankhandler mit allgemeinen Funktionen"""

import hashlib
import re
import os
import logging
import glob
import json
from natsort import natsorted


class BaseDb():
    """Basisklasse für die Vererbung an Datenbankhandler mit allgemeinen Funktionen"""
    def __init__(self):
        self.create()
        self._import_metadata()

    def create(self):
        """Erstellen des Datenbankspeichers"""
        raise NotImplementedError()

    def select(self, collection: str, condition: dict|list[dict], multi: str):
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

    def insert(self, data: dict|list[dict], collection: str):
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

    def update(self, data: dict, collection: str, condition: dict|list[dict], multi:str):
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

    def delete(self, collection: str, condition: dict | list[dict]):
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

    def truncate(self, collection: str):
        """Löscht alle Datensätze aus einer Tabelle/Collection

        Args:
            collection (str, optional): Name der Collection, in die Werte eingefügt werden sollen.
                                   Default: IBAN aus der Config.
        Returns:
            dict:
                - deleted, int: Anzahl der gelöschten Datensätze
        """
        raise NotImplementedError()

    def get_metadata(self, uuid: str):
        """
        Ruft Metadaten aus der Datenbank ab.

        Args:
            uuid (str): Unique ID (key).
        Returns:
            dict: Die abgerufenen Metadaten.
        """
        raise NotImplementedError()

    def filter_metadata(self, condition: dict, multi: str):
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

    def set_metadata(self, entry: dict, overwrite: bool=True):
        """
        Speichert oder ersetzt Metadaten in der Datenbank.

        Args:
            entry (dict): Der Eintrag, der gespeichert werden soll.
            overwrite (bool): Overwrite existing metadata with same uuid
                              if present (default: True)
        Returns:
            dict: Informationen über den Speichervorgang.
        """
        raise NotImplementedError()

    def _generate_unique(self, tx_entries: dict | list[dict]):
        """
        Erstellt einen einmaligen ID für jede Transaktion.

        Args:
            tx_entries (dict | list(dict)): Liste mit Transaktionsobjekten
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
                              tx_text
            md5_hash.update(combined_string.encode('utf-8'))

            # Store UUID
            transaction['uuid'] = md5_hash.hexdigest()

            # Set start Tagging priority
            transaction['prio'] = 0

        # Input List or single Dict
        if not isinstance(tx_entries, list):
            return tx_list[0]

        return tx_list

    def _generate_unique_meta(self, entry: dict):
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

    def _import_metadata(self):
        """Load content from json configs
        (config, rules, parsers) into DB"""
        settings_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ), 'settings'
        )

        # Load given rules & parsers (do not overwrite)
        for metatype in ['config', 'parser', 'rule']:
            json_path = os.path.join(settings_path, metatype)
            json_glob = os.path.join(json_path, '*.json')
            json_files = glob.glob(json_glob)
            json_files = natsorted(json_files)

            # Load from found metadata files
            for json_file in json_files:

                if not os.path.isfile(json_file):
                    # dead link
                    continue

                # Parse JSON
                logging.info(f"Loading {metatype} from {json_file}")
                with open(json_file, 'r', encoding='utf-8') as j:
                    try:
                        parsed_data = json.load(j)

                    except json.JSONDecodeError as e:
                        logging.warning(f"Failed to parse JSON file: {e}")

                # Add metadata type and format as list
                if isinstance(parsed_data, list):

                    for i, _ in enumerate(parsed_data):
                        parsed_data[i]['metatype'] = metatype

                else:
                    parsed_data['metatype'] = metatype
                    parsed_data = [parsed_data]

                # Store in DB (do not overwrite)
                inserted = 0
                for data in parsed_data:
                    inserted += self.set_metadata(data, overwrite=False).get('inserted')

                logging.info(f"Stored {inserted} {metatype} from {json_file}")
