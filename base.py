#!/usr/bin/python3
"""Basisklasse für die Vererbung allgemeiner Attribute und Methoden, die für den Programmablauf wichtig sind."""


import sys
import logging
import configparser

from handler.SqliteDB import SQLiteHandler
from parsers.Generic import Parser as Generic
from parsers.Commerzbank import Parser as Commerzbank


class BaseClass():
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
        except Exception as e:
            self.logger.critical("Config Pfad '{}' konnte nicht heladen werden !".format(configpath))
            sys.exit()

        # Weitere Attribute
        self.db = SQLiteHandler(self.config['DB']['path'])
        self.parsers = {
            'Generic': Generic,
            'Commerzbank': Commerzbank,
        }
        self.data = None

    def parse(self, uri, bank='Generic', format=None):
        """
        Liest Kontoumsätze aus der Ressource ein. Wenn das Format nicht angegeben ist, wird versucht, es zu erraten.

        Args:
            uri (str): Pfad zur Ressource mit den Kontoumsätzen.
            bank (str): Bezeichnung der Bank bzw. des einzusetzenden Parsers.
            format (str, optional): Bezeichnung des Ressourcenformats (http, csv, pdf).

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit den Kontoumsätzen.
        """
        # Format
        if format is None:
            #TODO: Logik zum Erraten des Datentyps
            format = 'pdf'

        # Parser
        self.parser = self.parsers.get(bank, self.parsers.get('Generic'))()
        if not self.parser.prepare(self.uri):
            return False
        parsing_method = {
            'pdf': self.parser.from_pdf,
            'csv': self.parser.from_csv,
            'http': self.parser.from_http
        }.get(format)

        return parsing_method(uri)

    def categorize(self, data):
        """
        Kategorisiert die Kontoumsätze

        Args:
            data (str): Kontoumsätze, die kategorisiert werden sollen

        Returns:
            Liste mit Dictonaries, als Standard-Objekt, die die übergebenen Daten mitsamt der Kategorisierung enthält.
        """
        raise NotImplemented()

    def flush_to_db(self):
        """
        Speichert die eingelesenen Kontodaten in der Datenbank und bereinigt den Objektspeicher.

        Returns:
            Die Anzahl der eingefügten Datensätze
        """
        normalized_data = self.data     # TODO: Liste der Dicts zurechtschneiden, damit sie dem DB Schema entsprechen.
        inserted_rows = self.db.insert(normalized_data)
        self.data = None
        return inserted_rows
