#!/usr/bin/python3 # pylint: disable=invalid-name
"""Routen und Funktionen für das User Interface."""

import sys
import os
import logging
from datetime import datetime
from flask import request, current_app, render_template

# Add Parent for importing Classes
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from handler.TinyDb import TinyDbHandler
from handler.MongoDb import MongoDbHandler
from handler.Tags import Tagger

from reader.Generic import Reader as Generic
from reader.Commerzbank import Reader as Commerzbank


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
        }

        # Tagger
        self.tagger = Tagger(self.db_handler)

        # Weitere Attribute
        self.data = None
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
        with current_app.app_context():

            @current_app.route('/', defaults={'iban':None}, methods=['GET'])
            @current_app.route('/<iban>', methods=['GET'])
            def index(iban) -> str:
                """
                Startseite mit Navigation und Uploadformular.

                Args (uri):
                    iban, str:  (optional) IBAN zu der die Einträge angezeigt werden sollen.
                                (Default: Primäre IBAN aus der Config)
                    startDate, str (query): Startdatum (Y-m-d) für die Anzeige der Einträge
                    endDate, str (query):   Enddatum (Y-m-d) für die Anzeige der Einträge
                Returns:
                    html: Startseite mit Navigation
                """
                # Check filter args
                condition = []

                if iban is None:
                    iban = current_app.config['IBAN']

                start_date = request.args.get('startDate')
                if start_date is not None:
                    # Convert to valid date format
                    try:
                        start_date = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
                        condition.append({
                            'key': 'date_tx',
                            'value': start_date,
                            'compare': '>='
                        })

                    except (ValueError, TypeError) as e:
                        logging.warning(f"Invalid startDate format '{e}' will be ignored")

                end_date = request.args.get('endDate')
                if end_date is not None:
                    # Convert to valid date format
                    try:
                        end_date = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
                        condition.append({
                            'key': 'date_tx',
                            'value': end_date,
                            'compare': '<='
                        })

                    except (ValueError, TypeError) as e:
                        logging.warning(f"Invalid endDate format '{e}' will be ignored")

                # Table with Transactions
                rows = self.db_handler.select(iban, condition)
                table_header = ['date_tx', 'betrag', 'currency',
                                'primary_tag', 'secondary_tag',
                                'prio', 'parsed']

                return render_template('index.html', iban=iban,
                                       table_header=table_header,
                                       table_data=rows)


            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            # - API Endpoints - - - - - - - - - - - - - - - - - - - -
            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -

            @current_app.route('/api/upload', methods=['POST'])
            def upload():
                """
                Endpunkt für das Annehmen hochgeladener Kontoumsatzdateien.
                Im Anschluss wird automatisch die Untersuchung der Inhalte angestoßen.

                Args (multipart/form-data):
                    input_file (binary): Dateiupload aus Formular-Submit
                Returns:
                    json: Informationen zur Datei und Ergebnis der Untersuchung.
                """
                input_file = request.files.get('input_file')
                if not input_file:
                    return {'error': 'No file provided'}, 400

                content_type = input_file.content_type
                size = 0
                path = '/tmp/upload.file'
                with open(path, 'wb') as f:

                    while True:
                        data = input_file.read(8192)

                        if not data:
                            break

                        size += len(data)
                        f.write(data)

                # Daten einlesen und in Object speichern (Bank und Format default bzw. wird geraten)
                content_formats = {
                    'application/json': 'json',
                    'text/csv': 'csv',
                    'application/pdf': 'pdf',
                    'text/plain': 'text',
                }

                # Read Input and Parse the contents
                self._read_input(path, data_format=content_formats.get(content_type))

                # Verarbeitete Kontiumsätze in die DB speichern
                # und vom Objekt und Dateisystem löschen
                inserted = self._flush_to_db()
                os.remove(path)

                return_code = 201 if inserted else 200
                return {
                    'size': size,
                    'filename': input_file.filename,
                    'content_type': content_type,
                    'inserted': inserted
                }, return_code

            @current_app.route('/api/<iban>/<t_id>', methods=['GET'])
            def getTx(iban, t_id):
                """
                Gibt alle Details zu einer bestimmten Transaktion zurück.
                Args (uri):
                    iban, str: IBAN
                    t_id, int: Datenbank ID der Transaktion
                Returns:
                    json: Details zu einer bestimmten Transaktion
                """
                tx_details = self.db_handler.select(
                    iban, {
                        'key': 'uuid',
                        'value': t_id,
                        'compare': '=='
                    }
                )
                return tx_details[0], 200

            @current_app.route('/api/truncateDatabase/', defaults={'iban':None}, methods=['DELETE'])
            @current_app.route('/api/truncateDatabase/<iban>', methods=['DELETE'])
            def truncateDatabase(iban):
                """
                Leert die Datenbank zu einer IBAN
                Args (uri):
                    iban, str:  (optional) IBAN zu der die Datenbank geleert werden soll.
                                (Default: Primäre IBAN aus der Config)
                Returns:
                    json: Informationen zum Ergebnis des Löschauftrags.
                """
                deleted_entries = self.db_handler.truncate(iban)
                return {'deleted': deleted_entries}, 200

            @current_app.route('/api/tag', methods=['PUT'])
            def tag() -> dict:
                """
                Kategorisiert die Kontoumsätze und aktualisiert die Daten in der Instanz.
                Die Argumente werden nach Prüfung an die Tagger-Klasse weitergegeben.

                Args (json):
                    siehe Tagger.tag()
                Returns:
                    json: Informationen zum Ergebnis des Taggings.
                """
                return self.tagger.tag(**request.json)

            @current_app.route('/api/setManualTag/<iban>/<t_id>', methods=['PUT'])
            def setManualTag(iban, t_id, data=None):
                """
                Handler für _set_manual_tag() für einzelne Einträge.

                Args (uri/json):
                    iban, str: IBAN
                    t_id, int: Datenbank ID der Transaktion, die getaggt werden soll
                    data, dict: Daten für die Aktualisierung (default: request.json)
                        - primary_tag, str: Bezeichnung der primären Kategorie
                        - secondary_tag, str: Bezeichnung der sekundären Kategorie
                Returns:
                    dict: updated, int: Anzahl der gespeicherten Datensätzen
                """
                if data is None:
                    data = request.json
                return self._set_manual_tag(iban, t_id, data)

            @current_app.route('/api/setManualTags/<iban>', methods=['PUT'])
            def setManualTags(iban):
                """
                Handler für _set_manual_tag() für mehrere Einträge.

                Args (uri/json):
                    iban, str: IBAN
                    t_ids, list[str]: Liste mit Datenbank IDs der Transaktionen,
                                      die getaggt werden sollen
                    primary_tag, str: Bezeichnung der primären Kategorie
                    secondary_tag, str: Bezeichnung der sekundären Kategorie
                Returns:
                    dict: updated, int: Anzahl der gespeicherten Datensätzen
                """
                data = request.json
                updated_entries = {'updated': 0}

                for tx in data.get('t_ids'):

                    updated = self._set_manual_tag(iban, tx, data)
                    updated_entries['updated'] += updated.get('updated')

                return updated_entries

            @current_app.route('/api/saveRule/', defaults={'rule_type':'rule'}, methods=['POST'])
            @current_app.route('/api/saveRule/<rule_type>', methods=['POST'])
            def saveRule(rule_type):
                """
                Einfügen oder updaten einer Regel in der Datenbank.
                Args (json):
                    rule_type, str: Typ der Regel (rule | parser)
                    rule, dict: Regel-Objekt
                        - name, str: Name der Regel
                        - rule, dict: Regel-Objekt
                """
                #TODO: Beide Arten in einer DB speichern, anhand eines Key aber unterscheiden.
                # - Das Dict muss hier noch richtig verpackt werden.
                # - Das Select muss dafür optimiert werden.
                # - Es müssen für alles mit metadata noch tests geschrieben werden.
                raise NotImplementedError()

    def _set_manual_tag(self, iban, t_id, data):
        """
        Setzt manuell eine Kategorie für einen bestimmten Eintrag.

        Args:
            iban, str: IBAN
            t_id, int: Datenbank ID der Transaktion, die getaggt werden soll
            data, dict: Daten für die Aktualisierung (default: request.json)
                - primary_tag, str: Bezeichnung der primären Kategorie
                - secondary_tag, str: Bezeichnung der sekundären Kategorie
        Returns:
            dict: updated, int: Anzahl der gespeicherten Datensätzen
        """
        new_tag_data = {
            'prio': 99
        }

        primary_tag = data['primary_tag']
        if primary_tag:
            new_tag_data['primary_tag'] = primary_tag

        secondary_tag = data.get('secondary_tag')
        if secondary_tag:
            new_tag_data['secondary_tag'] = secondary_tag

        condition = {
            'key': 'uuid',
            'value': t_id,
            'compare': '=='
        }

        updated_entries = self.db_handler.update(new_tag_data, iban, condition)
        return updated_entries

    def _read_input(self, uri, bank='Generic', data_format=None):
        """
        Liest Kontoumsätze aus der Ressource ein. Wenn das Format nicht angegeben ist,
        wird es versucht zu erraten. Speichert dann eine Liste mit Dictonaries,
        als Standard-Objekt mit den Kontoumsätzen in der Instanz.

        Args:
            uri (str): Pfad zur Ressource mit den Kontoumsätzen.
            bank (str): Bezeichnung der Bank bzw. des einzusetzenden Readers.
            format (str, optional): Bezeichnung des Ressourcenformats (http, csv, pdf).
        Returns:
            int: Anzahl an geparsten Einträgen
        """
        # Format
        if data_format is None:
            #TODO: Logik zum Erraten des Datentyps, #10
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

        self.data = parsing_method(uri)
        if self.data is not None:
            self.data = self._parse(self.data)
            return len(self.data)

        return 0

    def _parse(self, input_data=None):
        """Hanlder für den gleichnamigen Methodenaufruf beim Taggers"""
        # Parsing Data
        #TODO: Daten nicht aus self.data, sondern DB nach Signal, #8
        if input_data is None:
            input_data = self.data
        return self.tagger.parse(input_data)

    def _flush_to_db(self) -> int:
        """
        Speichert die eingelesenen Kontodaten in der Datenbank und bereinigt den Objektspeicher.

        Returns:
            int: Die Anzahl der eingefügten Datensätze
        """
        inserted_rows = self.db_handler.insert(self.data)
        self.data = None
        return inserted_rows.get('inserted')
