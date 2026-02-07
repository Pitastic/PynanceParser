#!/usr/bin/python3 # pylint: disable=invalid-name
"""Funktionen für das User Interface."""

import sys
import os
import logging
from datetime import datetime
from flask import current_app, redirect


# Add Parent for importing Classes
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from app.routes import Routes

from handler.TinyDb import TinyDbHandler
from handler.MongoDb import MongoDbHandler
from handler.Tags import Tagger

from reader.Generic import Reader as Generic
from reader.Comdirect import Reader as Comdirect
from reader.Commerzbank import Reader as Commerzbank
from reader.Volksbank_Mittelhessen import Reader as Volksbank_Mittelhessen


class UserInterface():
    """Basisklasse mit Methoden für den Programmablauf"""

    def __init__(self):
        """
        Initialisiert eine Instanz der Basisklasse und lädt die Konfiguration sowie die Logunktion.
        """
        # Datenbankhandler
        if current_app.config['DATABASE_BACKEND'] == 'tiny':
            self.db_handler = TinyDbHandler()

        elif current_app.config['DATABASE_BACKEND'] == 'mongo':
            self.db_handler = MongoDbHandler()

        else:
            raise NotImplementedError(("The configure database engine ",
                                     f"{current_app.config['DATABASE_BACKEND']} ",
                                      "is not supported !"))
        assert self.db_handler, \
            (f"DbHandler {current_app.config['DATABASE_BACKEND']} Klasse konnte nicht ",
             "instanziiert werden")

        # Reader
        self.readers = {
            'Generic': Generic,
            'Commerzbank': Commerzbank,
            'Comdirect': Comdirect,
            'Volksbank Mittelhessen': Volksbank_Mittelhessen,
        }

        # Tagger
        self.tagger = Tagger(self.db_handler)

        # Weitere Attribute
        self.reader = None

        #TODO: Usermanagement, #7
        # Jeder User soll seine eigene Collection haben.
        # Die Collection beinhaltet Dokumente als Settings, Regeln
        # oder Transaktionen zu verschiedenen Konten des Benutzers.
        # Im Init und/oder als Decorator jeder Funktion muss der User
        # aus der Session ermittelt werden. Fallback ist der in der Config
        # hinterlegte Deafult-User, sofern Authentification noch nicht
        # implementiert ist.

        # Define Routes
        self.routes = Routes(self)

    def filter_to_condition(self, get_args: dict) -> list:
        """
        Liest vorhandene GET Argumente und wandelt diese in einen Filter um.
        Args:
            filter_data, dict: Dictionary mit den GET Argumenten
        Returns:
            list(dict): DB Handler kompatible Filterbedingungen
            dict: Filterbedingungen zur Anzeige im Frontend
        """
        condition = []
        frontend_filters = {}

        # - Filter for Start Date
        date_patterns = ['%Y-%m-%d', '%d.%m.%Y']
        start_date = get_args.get('startDate')
        if start_date and isinstance(start_date, str):
            for pattern in date_patterns:
                try:
                    start_date = int(datetime.strptime(start_date, pattern).timestamp())
                    condition.append({
                        'key': 'date_tx',
                        'value': start_date,
                        'compare': '>='
                    })
                    frontend_filters['startDate'] = start_date
                    break

                except ValueError:
                    continue

        # - Filter for End Date
        end_date = get_args.get('endDate')
        if end_date and isinstance(end_date, str):
            for pattern in date_patterns:
                try:
                    end_date = int(datetime.strptime(end_date, pattern).timestamp())
                    end_date = end_date + 86399  # Add 23:59:59 to include whole day
                    condition.append({
                        'key': 'date_tx',
                        'value': end_date,
                        'compare': '<='
                    })
                    frontend_filters['endDate'] = end_date
                    break

                except ValueError:
                    continue

        # - Sort direction
        sort_desc = get_args.get('descending')
        if sort_desc is not None:
            frontend_filters['descending'] = sort_desc

        # - Filter for Category
        cat_filter = get_args.get('category')
        if cat_filter is not None:
            condition.append({
                'key': 'category',
                'value': cat_filter,
                'compare': '=='
            })

            frontend_filters['category'] = cat_filter

        # Filter for Tags
        tag_filter = get_args.get('tags')
        if tag_filter is not None:
            tag_filter = [t.strip() for t in tag_filter.split(',') if t]
            condition.append({
                'key': 'tags',
                'value': tag_filter,
                'compare': get_args.get('tag_mode', 'in')
            })

            frontend_filters['tags'] = " ,".join(tag_filter)
            frontend_filters['tag_mode'] = get_args.get('tag_mode', 'in')

        # Filter for Betrag (min)
        amount_filter_min = get_args.get('amount_min')
        if amount_filter_min is not None:
            try:
                amount_filter_min = float(amount_filter_min)
                condition.append({
                    'key': 'amount',
                    'value': amount_filter_min,
                    'compare': '>='
                })

                frontend_filters['amount_min'] = amount_filter_min

            except (ValueError, TypeError) as e:
                logging.warning(f"Invalid amount format '{e}' will be ignored")

        # Filter for Betrag (max)
        amount_filter_max = get_args.get('amount_max')
        if amount_filter_max is not None:
            try:
                amount_filter_max = float(amount_filter_max)
                condition.append({
                    'key': 'amount',
                    'value': amount_filter_max,
                    'compare': '<='
                })

                frontend_filters['amount_max'] = amount_filter_max

            except (ValueError, TypeError) as e:
                logging.warning(f"Invalid amount format '{e}' will be ignored")

        # Filter for Text Search
        text_search = get_args.get('text')
        if text_search is not None:
            condition.append({
                'key': 'text_tx',
                'value': text_search,
                'compare': 'regex'
            })

            frontend_filters['text'] = text_search

        # Filter Gegenkonto Search
        konto_search = get_args.get('peer')
        if konto_search is not None:
            condition.append({
                'key': 'peer',
                'value': konto_search,
                'compare': 'regex'
            })

            frontend_filters['peer'] = konto_search

        return condition, frontend_filters

    def check_requested_iban(self, iban):
        """
        Prüft, ob die angeforderte IBAN oder Gruppenname gültig ist.
        Args:
            iban, str:  IBAN zu der die Einträge angezeigt werden sollen.
        Raises:
            ValueError: Wenn die IBAN oder Gruppenname ungültig ist.
        """
        if iban is None:
            # No IBAN provided, redirect to welcome
            redirect('/')

        if not self.db_handler.get_group_ibans(iban, True):
            # It's not an IBAN or valid Groupname
            return False

        return True

    def set_manual_tag_and_cat(self, iban, t_id, tags: list=None,
                                category: str=None, overwrite: bool=False) -> dict:
        """
        Setzt manuell eine Kategorie und/oder Tags für einen bestimmten Eintrag.

        Args:
            iban, str: IBAN
            t_id, int: Datenbank ID der Transaktion, die getaggt werden soll
            tags, list[str]: Bezeichnung der zu setzenden Tags
            category, str: Bezeichnung der zu setzenden Kategorie
            overwrite, bool: Wenn True, werden die bestehenden Tags überschrieben.
        Returns:
            dict: updated, int: Anzahl der gespeicherten Datensätzen
        """
        assert tags is not None or category is not None, 'No tags or category provided'
        new_tag_data = {}

        if tags is not None:
            if not isinstance(tags, list):
                tags = [tags]

            new_tag_data['tags'] = tags

        if category is not None:
            new_tag_data['category'] = category
            new_tag_data['prio'] = 99  # Manuell gesetzte Tags haben immer hohe Prio

        condition = {
            'key': 'uuid',
            'value': t_id,
            'compare': '=='
        }

        merge = not overwrite
        updated_entries = self.db_handler.update(new_tag_data, iban, condition, merge=merge)
        return updated_entries

    def remove_tags(self, iban, t_id):
        """
        Entfernt ein gesetztes Tag für einen Eintrag.

        Args:
            iban, str: IBAN
            t_id, str: Datenbank ID der Transaktion,
                       die bereinigt werden soll.
        Returns:
            dict: updated, int: Anzahl der gespeicherten Datensätzen
        """
        new_data = {
            'tags': []
        }
        condition = [{
            'key': 'uuid',
            'value': t_id,
            'compare': '=='
        }]

        updated_entries = self.db_handler.update(new_data, iban, condition, merge=False)
        return updated_entries

    def remove_cat(self, iban, t_id):
        """
        Entfernt eine Kategorie von einen Eintrag.

        Args:
            iban, str: IBAN
            t_id, str: Datenbank ID der Transaktion,
                       die bereinigt werden soll.
        Returns:
            dict: updated, int: Anzahl der gespeicherten Datensätzen
        """
        new_data = {
            'prio': 0,
            'category': None,
        }
        condition = [{
            'key': 'uuid',
            'value': t_id,
            'compare': '=='
        }]

        updated_entries = self.db_handler.update(new_data, iban, condition)
        return updated_entries

    def mv_fileupload(self, input_file, path):
        """
        Verschiebt die hochgeladene Datei in ein temporäres Verzeichnis.

        Args:
            input_file (binary): Dateiupload aus Formular-Submit
            path (str): Pfad zur temporären Datei
        Returns:
            str: Content-Type der Datei
        """
        content_type = input_file.content_type
        size = 0
        with open(path, 'wb') as f:

            while True:
                data = input_file.read(8192)

                if not data:
                    break

                size += len(data)
                f.write(data)

        return content_type, size

    def read_input(self, uri, bank='Generic', data_format=None):
        """
        Liest Kontoumsätze aus der Ressource ein. Wenn das Format nicht angegeben ist,
        wird es versucht zu erraten. Speichert dann eine Liste mit Dictonaries,
        als Standard-Objekt mit den Kontoumsätzen in der Instanz.

        Args:
            uri (str): Pfad zur Ressource mit den Kontoumsätzen.
            bank (str): Bezeichnung der Bank bzw. des einzusetzenden Readers.
            format (str, optional): Bezeichnung des Ressourcenformats (http, csv, pdf).
        Returns:
            list(dict): Geparste und getaggte Kontoumsätze
        """
        # Format
        if data_format is None:
            # Fallback to CSV text
            data_format = 'csv'

        # Reader
        self.reader = self.readers.get(
            bank, self.readers.get('Generic')
        )()

        parsing_method = {
            'pdf': self.reader.from_pdf,
            'csv': self.reader.from_csv,
            'http': self.reader.from_http
        }.get(data_format)

        data = parsing_method(uri)
        if data is None:
            return []

        return self.tagger.parse(data)
