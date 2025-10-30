#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisklasse für die Vererbung an Datenbankhandler mit allgemeinen Funktionen"""

import hashlib
import re
import os
import logging
import glob
import json
from datetime import datetime
from natsort import natsorted


class BaseDb():
    """Basisklasse für die Vererbung an Datenbankhandler mit allgemeinen Funktionen"""
    def __init__(self):
        self.create()
        self._load_metadata()

    def create(self):
        """Erstellen des Datenbankspeichers"""
        raise NotImplementedError()

    def add_iban_group(self, groupname: str, ibans: list):
        """
        Fügt eine neue Gruppe mit IBANs in die Datenbank ein oder
        ändert eine bestehende Gruppe mit der Zuordnung, die übergeben wurde.

        Args:
            groupname (str): Name der Gruppe.
            ibans (list): Liste der IBANs, die zur Gruppe hinzugefügt werden sollen.
        Returns:
            dict: Informationen über den Speichervorgang.
        """
        for iban in ibans:
            if self.check_collection_is_iban(iban) is False:
                raise ValueError(f"IBAN '{iban}' ist ungültig !")

        new_group = {
            'metatype': 'config',
            'name': 'group',
            'uuid': groupname,
            'groupname': groupname,
            'ibans': ibans,
            'members': []
        }
        return self.set_metadata(new_group, overwrite=True)

    def select(self, collection:str, condition: dict|list[dict]=None, multi: str='AND'):
        """
        Handler für das Vorbereiten der '_select' Methode, welche Datensätze aus der Datenbank
        selektiert, die die angegebene Bedingung erfüllen.

        Args:
            collection (str):   Name der Collection oder Gruppe, aus der selektiert werden
                                soll. Es erfolgt automatisch eine Unterscheidung, ob es
                                sich um eine IBAN oder einen Gruppenname handelt.
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
        if not condition:
            # Catch empty lists
            condition = None

        if not self.check_collection_is_iban(collection):
            # collection is a group
            group_ibans = self.get_group_ibans(collection)
            if not group_ibans:
                logging.error(f"Group {collection} not found or empty")
                return []

            collection = group_ibans

        # Always create a list of collections for group-Loop
        if not isinstance(collection, list):
            collection = [collection]

        result_list = self._select(collection, condition, multi)
        for r in result_list:
            # Format Datestrings
            if isinstance(r.get('date_tx'), int):
                r['date_tx'] = datetime.fromtimestamp(r['date_tx']).strftime('%d.%m.%Y')

            if isinstance(r.get('valuta'), int):
                r['valuta'] = datetime.fromtimestamp(r['valuta']).strftime('%d.%m.%Y')

        return result_list

    def _select(self, collection: str, condition: dict|list[dict], multi: str):
        """
        Private Methode zum Selektieren von Datensätze aus der Datenbank,
        die die angegebene Bedingung erfüllen. Siehe 'select' Methode.

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
        Returns:
            dict:
                - inserted, int: Zahl der neu eingefügten IDs
        """
        if not self.check_collection_is_iban(collection):
            raise ValueError(f"Collection {collection} is not a valid IBAN")

        # Always create a list of transactions for loop
        if not isinstance(data, list):
            tx_list = [data]
        else:
            tx_list = data

        for transaction in tx_list:

            # Add generated IDs
            transaction = self._generate_unique(transaction)

            # Ensure default values
            # - IBAN, Tagging priority, empty Tag list
            transaction['iban'] = collection
            transaction['prio'] = 0
            transaction['category'] = transaction.get('category')
            if not transaction.get('tags'):
                transaction['tags'] = []

        return self._insert(tx_list, collection)

    def _insert(self, data: dict|list[dict], collection: str):
        """
        Private Methode zum Einfügen von Datensätzen in die Datenbank.
        Siehe 'insert' Methode.

        Returns:
            dict:
                - inserted, int: Zahl der neu eingefügten IDs
        """
        raise NotImplementedError()

    def update(self, data: dict, collection: str, condition: dict|list[dict],
               multi:str, merge:bool=True):
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
            merge (bool): Wenn False, werden Listenfelder nicht gemerged, sondern
                          komplett überschrieben. Default: True
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
        """Löscht eine Tabelle/Collection

        Args:
            collection (str):   Name der Collection, in die Werte eingefügt werden sollen.
        Returns:
            dict:
                - deleted, int: Anzahl der gelöschten Datensätze
        """
        if not self.check_collection_is_iban(collection):
            # Delete group config from metadata
            return self.delete('metadata', [
                {
                    'key': 'metatype',
                    'value': 'config'
                },{
                    'key': 'name',
                    'value': 'group'
                },{
                    'key': 'uuid',
                    'value': collection
                }
            ])

        return self._truncate(collection)

    def _truncate(self, collection):
        """
        Private Methode zum Löschen einer Tabelle/Collection.
        Siehe 'truncate' Methode.

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

    def filter_metadata(self, condition: dict|list, multi: str):
        """
        Ruft Metadaten aus der Datenbank anhand von Kriterien ab.

        Args:
            condition (dict|list): key-value-Paare für die Filterung der Metadaten.
            multi (str) : ['AND' | 'OR'] Wenn 'condition' eine Liste mit conditions ist,
                          werden diese logisch wie hier angegeben verknüpft. Default: 'AND'
        Returns:
            list: Die abgerufenen Metadaten.
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

    def get_group_ibans(self, group: str, check_before: bool=False):
        """
        Ruft die Liste von IBANs einer Gruppe aus der Datenbank ab.

        Args:
            group (str): Name der Gruppe.
            check_before (bool):    Wenn True, wird überprüft, ob es
                                    sich um eine Gruppe oder IBAN handelt.
                                    Default: False
        Returns:
            list: Die IBANs der abgerufene Gruppe.
        """
        if check_before and self.check_collection_is_iban(group):
            return [group]

        meta_results = self.filter_metadata([
            {
                'key': 'metatype',
                'value': 'config'
            },{
                'key': 'name',
                'value': 'group'
            },{
                'key': 'uuid',
                'value': group
            }
        ], multi='AND')

        ibans = []
        if meta_results:
            ibans = meta_results[0].get('ibans', [])

        return ibans

    def list_ibans(self):
        """
        Listet alle in der Datenbank vorhandenen IBAN-Collections auf.

        Returns:
            list: Liste der IBAN-Collections.
        """
        all_collections = self._get_collections()
        ibans = [col for col in all_collections if self.check_collection_is_iban(col)]
        return ibans

    def list_groups(self):
        """Listet alle in der Datenbank vorhandenen Gruppen auf.
        
        Returns:
            list: Liste der Gruppen.
        """
        groups = []
        meta_results = self.filter_metadata([
            {
                'key': 'metatype',
                'value': 'config'
            },{
                'key': 'name',
                'value': 'group'
            }
        ], multi='AND')

        for group in meta_results:
            groups.append(group.get('groupname'))

        return groups

    def _get_collections(self):
        """
        Ruft alle Collections in der Datenbank ab.

        Returns:
            list: Liste der Collections.
        """
        raise NotImplementedError()

    def _generate_unique(self, tx_entry: dict | list[dict]):
        """
        Erstellt einen einmaligen ID für jede Transaktion aus den Transaktionsdaten.

        Args:
            tx_entries (dict): Ein Transaktionsobjekt
        Returns:
            dict | list(dict): Die um die IDs ('uuid') erweiterte Eingabeliste
        """

        no_special_chars = re.compile("[^A-Za-z0-9]")
        tx_text = no_special_chars.sub('', tx_entry.get('text_tx', ''))

        md5_hash = hashlib.md5()

        combined_string = str(tx_entry.get('date_tx', '')) + \
                            str(tx_entry.get('betrag', '')) + \
                            tx_text
        md5_hash.update(combined_string.encode('utf-8'))

        # Store UUID
        tx_entry['uuid'] = md5_hash.hexdigest()

        return tx_entry

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

    def _load_metadata(self):
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
        result = {'inserted': 0}
        for metatype in ['config', 'parser', 'rule']:
            json_path = os.path.join(settings_path, metatype)
            json_glob = os.path.join(json_path, '*.json')
            json_files = glob.glob(json_glob)
            json_files = natsorted(json_files)

            # Load from found metadata files
            for json_file in json_files:

                if not os.path.isfile(json_file):
                    logging.warning(f"File {json_file} is not a file")
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
                if not isinstance(parsed_data, list):
                    parsed_data = [parsed_data]

                # Store in DB (do not overwrite)
                inserted = 0
                for data in parsed_data:
                    inserted += self.set_metadata(data, overwrite=False).get('inserted')

                logging.info(f"Stored {inserted} {metatype} from {json_file}")
                result['inserted'] += inserted

        return result

    def import_metadata(self, path: str=None, metatype: str='rule'):
        """Import metadata from given path

        Args:
            path (str): Path to the metadata json file
            metatype (str): Type of metadata (default: 'rule')
        """
        # Check if path exists
        if not os.path.exists(path):
            error_msg = f"Path {path} does not exist"
            logging.error(error_msg)
            return {'error': error_msg}

        # Parse JSON
        with open(path, 'r', encoding='utf-8') as j:
            try:
                parsed_data = json.load(j)

            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON file: {e}"
                logging.warning(error_msg)
                return {'error': error_msg}

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
            inserted += self.set_metadata(data, overwrite=True).get('inserted')

        logging.info(f"Stored {inserted} imported metadata from {path}")
        return {'inserted': inserted}

    def check_collection_is_iban(self, collection: str):
        """
        Überprüft, ob die angegebene Collection eine IBAN ist.

        Args:
            collection (str): Name der Collection.
        Returns:
            bool: True, wenn die Collection eine IBAN ist, sonst False.
        """
        iban_regex = re.compile(r'[A-Z]{2}[0-9]{2}[ ]?([0-9]{4}[ ]?){4,7}[0-9]{1,4}')
        return bool(re.match(iban_regex, collection))
