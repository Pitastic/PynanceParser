#!/usr/bin/python3
"""Basisklasse für die Vererbung allgemeiner Attribute und Methoden, die für den Programmablauf wichtig sind."""


import sys
import logging
import configparser
import random

from handler.SqliteDb import SQLiteHandler
from parsers.Generic import Parser as Generic
from parsers.Commerzbank import Parser as Commerzbank


class BaseClass():
    """
    Hauptfunktionen für den Programmablauf
    """
    def __init__(self, configpath):
        """
        Initialisiert eine Instanz der Basisklasse und lädt die Konfiguration sowie die Logunktion.

        Args:
            configpath (str): Pfad zur Configdatei
        """
        # Logging
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler('pynanceparser.log', 'w', 'utf-8')
        handler.setFormatter(
            logging.Formatter('[%(asctime)s] %(levelname)s (%(module)s): %(message)s'))
        self.logger.addHandler(handler)

        # Config
        try:
            self.config = configparser.ConfigParser()
            self.config.read(configpath)
        except IOError as ex:
            self.logger.critical(f"Config Pfad '{configpath}' konnte nicht heladen werden ! - {ex}")
            sys.exit()

        # Weitere Attribute
        #TODO: Mehr als eine IBAN unterstützen
        self.db = SQLiteHandler(self.config, self.logger)
        self.parsers = {
            'Generic': Generic,
            'Commerzbank': Commerzbank,
        }
        self.data = None
        self.parser = None

    def parse(self, uri, bank='Generic', data_format=None):
        """
        Liest Kontoumsätze aus der Ressource ein. Wenn das Format nicht angegeben ist, wird versucht, es zu erraten.
        Speichert Liste mit Dictonaries, als Standard-Objekt mit den Kontoumsätzen in der Instanz.

        Args:
            uri (str): Pfad zur Ressource mit den Kontoumsätzen.
            bank (str): Bezeichnung der Bank bzw. des einzusetzenden Parsers.
            format (str, optional): Bezeichnung des Ressourcenformats (http, csv, pdf).
        Returns:
            int: Anzahl an geparsten Einträgen
        """
        # Format
        if data_format is None:
            #TODO: Logik zum Erraten des Datentyps
            data_format = 'csv'

        # Parser
        self.parser = self.parsers.get(bank, self.parsers.get('Generic'))()
        parsing_method = {
            'pdf': self.parser.from_pdf,
            'csv': self.parser.from_csv,
            'http': self.parser.from_http
        }.get(data_format)

        self.data = parsing_method(uri)
        return len(self.data) if self.data is not None else 0

    def tag(self):
        """
        Kategorisiert die Kontoumsätze und aktualisiert die Daten in der Instanz.

        Args:
            data (str): Kontoumsätze, die kategorisiert werden sollen
        Returns:
            int: Anzahl der kategorisierten Daten.
        """
        #TODO: tag (Fake Methode)
        # 1. RegEx Tagging
        count = self.tag_regex()
        # 2. AI Tagging
        count = count + self.tag_ai()

    def tag_manual(self, t_id, primary_tag, secondary_tag=None):
        """
        Setzt manuell eine Kategorie für einen bestimmten Eintrag.

        Args:
            t_id, int: Datenbank ID der Transaktion, die getaggt werden soll
            primary_tag, str: Bezeichnung der primären Kategorie
            secondary_tag, str: Bezeichnung der sekundären Kategorie
        Returns:
            Anzahl der gespeicherten Datensätzen
        """
        return self.db.update(
            self.config['DEFAULT']['iban'],
            {
                'main_category': primary_tag,
                'second_category': secondary_tag,
            },
            f'WHERE id = {t_id}')

    def tag_regex(self, take_all=False):
        """
        Automatische Kategorisierung anhand von hinterlegten RegExes je Kategorie.

        Args:
            take_all, bool(False): Switch um nur ungetaggte oder alle Datensätze zu untersuchen.
        Returns:
            Anzahl der getaggten Datensätze
        """
        #TODO: Fake Funktion
        count = 0
        for transaction in self.data:
            if transaction.get('primary_tag') is None or take_all:
                # Komplette Untersuchung
                # Setzt 'primary' und 'secondary' (ggf. None) soweit erkannt
                count = count + 1
        return random.randint(0, count)

    def tag_ai(self, take_all=False):
        """
        Automatische Kategorisierung anhand eines Neuronalen Netzes.
        Trainingsdaten sind die zum Zeitpunkt des taggings bereits
        getaggten Datensätze aus der Datenbank. Für neue Tags werden die
        ungetaggten (default) oder alle Datensätze des aktuellen Imports berücksichtigt.

        Args:
            take_all, bool(False): Switch um nur ungetaggte oder alle Datensätze zu untersuchen.
        Returns:
            Anzahl der getaggten Datensätze
        """
        #TODO: Fake Funktion
        list_of_categories = ['Vergnügen', 'Versicherung', 'KFZ', 'Kredite', 'Haushalt und Lebensmittel', 'Anschaffung']
        count = 0
        for transaction in self.data:
            if transaction.get('primary_tag') is None or take_all:
                # Komplette Untersuchung
                # Setzt 'primary' und 'secondary' (ggf. None) soweit erkannt
                transaction['primary_tag'] = random.choice(list_of_categories)
                transaction['secondary_tag'] = None
                count = count + 1
        return random.randint(0, count)

    def flush_to_db(self):
        """
        Speichert die eingelesenen Kontodaten in der Datenbank und bereinigt den Objektspeicher.

        Returns:
            int: Die Anzahl der eingefügten Datensätze
        """
        normalized_data = self.data     # TODO: Liste der Dicts zurechtschneiden, damit sie dem DB Schema entsprechen.
        inserted_rows = self.db.insert(self.config['DEFAULT']['iban'], normalized_data)
        self.data = None
        return inserted_rows
