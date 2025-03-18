#!/usr/bin/python3 # pylint: disable=invalid-name
"""Routen und Funktionen für das User Interface."""

import sys
import os
import logging
from flask import request, jsonify, current_app

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

            @current_app.route('/')
            def index() -> str:
                """
                Startseite mit Navigation und Uploadformular.

                Returns:
                    html: Startseite mit Navigation
                """
                return """<html><body>
                    <h2>Upload a file</h2>
                    <form action="/upload" method="post" enctype="multipart/form-data">
                    filename: <input type="file" name="tx_file" /><br />
                    <input type="submit" />
                    </form>
                </body></html>
                """

            @current_app.route('/upload', methods=['POST'])
            def upload():
                """
                Endpunkt für das Annehmen hochgeladener Kontoumsatzdateien.
                Im Anschluss wird automatisch die Untersuchung der Inhalte angestoßen.

                Args:
                    tx_file (binary): Dateiupload aus Formular-Submit
                Returns:
                    html: Informationen zur Datei und Ergebnis der Untersuchung.
                """
                tx_file = request.files['tx_file']
                content_type = tx_file.content_type
                out = """<html>
                <body>
                    tx_file length: {size}<br />
                    tx_file filename: {filename}<br />
                    tx_file mime-type: {content_type}
                </body>
                </html>"""
                size = 0
                path = '/tmp/test.file'
                with open(path, 'wb') as f:

                    while True:
                        data = tx_file.read(8192)

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

                # Eingelesene Umsätze kategorisieren
                tagging_result_stats = self.tagger.tag()
                logging.info(f"Tagging Result: {tagging_result_stats}")

                # Verarbeitete Kontiumsätze in die DB speichern
                # und vom Objekt und Dateisystem löschen
                inserted = self._flush_to_db()
                os.remove(path)

                if inserted:
                    return out.format(size=size, filename=tx_file.filename,
                                      content_type=content_type), 201

                return out.format(size=size, filename=tx_file.filename,
                                    content_type=content_type), 304

            @current_app.route('/view/', defaults={'iban': None}, methods=['GET'])
            @current_app.route('/view/<iban>', methods=['GET'])
            def view(iban):
                """
                Anzeige aller Umsätze zu einer IBAN

                Args:
                    iban (str): IBAN, zu der die Umsätze angezeigt werden sollen
                                (default: aus Config)
                Returns:
                    html: Tabelle mit den Umsätzen
                """
                rows = self.db_handler.select(iban)
                out = """<table style="border: 1px solid black;"><thead><tr>
                    <th>Datum</th> <th>Betrag</th> <th>Tag (pri)</th> <th>Tag (sec.)</th> <th>Parsed</th> <th>Hash</th>
                </tr></thead><tbody>"""
                for r in rows:
                    out += f"""<tr id="tr-{r['uuid']}">
                    <td class="td-date">{r['date_tx']}</td>
                    <td class="td-betrag">{r['betrag']} {r['currency']}</td>
                    <td class="td-tag1">{r['primary_tag']}</td>
                    <td class="td-tag2">{r['secondary_tag']}</td>
                    <td class="td-parsed">"""
                    for parse_element in r['parsed']:
                        out += f"<p>{parse_element}</p>"
                    out += f"</td><td class='td-uuid'>{r['uuid']}</td>"
                    out += "</tr>"
                out += """</tbody></table>"""
                return out, 200

            @current_app.route('/truncateDatabase/', defaults={'iban': None}, methods=['GET'])
            @current_app.route('/truncateDatabase/<iban>', methods=['GET'])
            def truncateDatabase(iban):
                """Leert die Datenbank"""
                deleted_entries = self.db_handler.truncate(iban)
                return jsonify({'deleted': deleted_entries}), 200

            @current_app.route('/tag', methods=['POST'])
            def tag() -> dict:
                """
                Kategorisiert die Kontoumsätze und aktualisiert die Daten in der Instanz.
                """
                #TODO: Check *args, **kwargs provided
                data = request.get_json(force=True)
                result = self.tagger.tag(**data)
                return jsonify(result)

            @current_app.route('/setManualTag', methods=['POST'])
            def setManualTag(self, t_id, primary_tag, secondary_tag=None):
                """
                Setzt manuell eine Kategorie für einen bestimmten Eintrag.

                Args:
                    t_id, int: Datenbank ID der Transaktion, die getaggt werden soll
                    primary_tag, str: Bezeichnung der primären Kategorie
                    secondary_tag, str: Bezeichnung der sekundären Kategorie
                Returns:
                    Anzahl der gespeicherten Datensätzen
                """
                data = request.json
                t_id = data['t_id']
                primary_tag = data['primary_tag']
                secondary_tag = data.get('secondary_tag')

                updated_entries = self.db_handler.update(
                    {
                        'main_category': primary_tag,
                        'second_category': secondary_tag,
                    },
                    f'WHERE id = {t_id}')
                return jsonify({'updated': updated_entries})

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
