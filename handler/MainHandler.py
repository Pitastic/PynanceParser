#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisklasse mit Methoden für den Programmablauf."""


import random
import hashlib
import os
import logging
import configparser
import re

from handler.TinyDb import TinyDbHandler
from handler.MongoDb import MongoDbHandler
from parsers.Generic import Parser as Generic
from parsers.Commerzbank import Parser as Commerzbank


class MainHandler():
    """
    Basisklasse mit Methoden für den Programmablauf.
    """
    def __init__(self):
        """
        Initialisiert eine Instanz der Basisklasse und lädt die Konfiguration sowie die Logunktion.
        """
        # Logging
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler('pynanceparser.log', 'a', 'utf-8')
        handler.setFormatter(
            logging.Formatter('[%(asctime)s] %(levelname)s (%(module)s): %(message)s'))
        self.logger.addHandler(handler)

        # Config
        config_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ),
            'config.conf')
        try:
            self.config = configparser.ConfigParser()
            self.config.read(config_path)
            if 'DB' not in self.config.sections():
                raise IOError('Die Config scheint leer zu sein.')
        except IOError as ex:
            self.logger.critical(f"Config Pfad '{config_path}' konnte nicht heladen werden !" + \
                                 f" - {ex}")

        # Weitere Attribute
        #TODO: Mehr als eine IBAN unterstützen
        # Datenbankhandler starten
        self.database = {
            'tiny': TinyDbHandler,
            'mongo': MongoDbHandler
        }.get(self.config['DB']['backend'])
        self.database = self.database(self.config, self.logger)
        # Parser hinterlegen
        self.parsers = {
            'Generic': Generic,
            'Commerzbank': Commerzbank,
        }
        self.data = None
        self.parser = None

    def read_input(self, uri, bank='Generic', data_format=None):
        """
        Liest Kontoumsätze aus der Ressource ein. Wenn das Format nicht angegeben ist,
        wird es versucht zu erraten. Speichert dann eine Liste mit Dictonaries,
        als Standard-Objekt mit den Kontoumsätzen in der Instanz.

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
        self.parser = self.parsers.get(
            bank,
            self.parsers.get('Generic')
        )(self.config, self.logger)

        parsing_method = {
            'pdf': self.parser.from_pdf,
            'csv': self.parser.from_csv,
            'http': self.parser.from_http
        }.get(data_format)

        self.data = parsing_method(uri)
        if self.data is not None:
            self.data = self.parse(self.data)
            return len(self.data)

        return 0

    def parse(self, input_data=None):
        """
        Untersucht die Daten eines Standard-Objekts (hauptsächlich den Text)
        und identifiziert spezielle Angaben anhand von Mustern.
        Alle Treffer werden unter dem Schlüssel 'parsed' jedem Eintrag hinzugefügt.
        """
        # RegExes
        # Der Key wird als Bezeichner für das Ergebnis verwendet.
        # Jeder RegEx muss genau eine Gruppe matchen.
        parse_regexes = {
            'Mandatsreferenz': re.compile(r"Mandatsref\:\s?([A-z0-9]*)"),
            'Gläubiger': re.compile(r"([A-Z]{2}[0-9]{2}[A-Z]{3}0[0-9]{10})")
        }

        # Parsing Data
        if input_data is None:
            input_data = self.data

        for d in input_data:
            for name, regex in parse_regexes.items():
                re_match = regex.search(d['text_tx'])
                if re_match:
                    d['parsed'][name] = re_match.group(1)

        return input_data

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
        return self.database.update(
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
        list_of_categories = [
            'Vergnügen', 'Versicherung', 'KFZ', 'Kredite',
            'Haushalt und Lebensmittel', 'Anschaffung'
        ]
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
        self.generate_unique()
        inserted_rows = self.database.insert(self.data)
        self.data = None
        return inserted_rows

    def generate_unique(self):
        """
        Erstellt einen einmaligen ID für jede Transaktion.
        """
        no_special_chars = re.compile("[^A-Za-z0-9]")
        for transaction in self.data:
            md5_hash = hashlib.md5()
            tx_text = no_special_chars.sub('', transaction.get('text_tx', ''))
            combined_string = str(transaction.get('date_tx', '')) + \
                              str(transaction.get('betrag', '')) + \
                              tx_text
            md5_hash.update(combined_string.encode('utf-8'))
            transaction['hash'] = md5_hash.hexdigest()
