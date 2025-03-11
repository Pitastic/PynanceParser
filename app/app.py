#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisklasse mit Methoden für den Programmablauf."""

import os
import sys
import inspect
import json
from logging.config import dictConfig
from functools import wraps
from flask import Flask, request, jsonify, render_template_string, current_app

# Add Parent for importing Classes
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from handler.TinyDb import TinyDbHandler
from handler.MongoDb import MongoDbHandler
from handler.Tags import Tagger

from reader.Generic import Reader as Generic
from reader.Commerzbank import Reader as Commerzbank


def user_input_type_converter(original_func):
    """Converts function args in simple types as annotated"""

    @wraps(original_func)
    def wrapper(*args, **kwargs):

        converter = {
            'bool': lambda x: False if x is None else bool(json.loads(x.lower())),
            'int': int,
            'float': float,
            'str': str
        }

        parameters = inspect.signature(original_func).parameters

        # Positional Args
        positional_args = []
        for i, arg in enumerate(args):
            param_name = list(parameters.keys())[i]
            param_type = parameters[param_name].annotation

            # Type defined and Input is wrong
            if not isinstance(arg, param_type) and param_type.__name__ != '_empty':
                conv = converter.get(param_type.__name__)
                try:
                    arg = conv(arg)
                except (TypeError, ValueError) as ex:
                    msg = (
                        f'Parameter "{param_name}" is not '
                        f'of type "{param_type.__name__}" '
                        'and could not be converted into this type! - '
                        f'{str(ex)}')
                    current_app.logger.error(msg)
                    return jsonify({'error': msg}), 400

            positional_args.append(arg)

        # Keyword Args
        keyword_args = {}
        for param_name, arg in kwargs.items():
            param_type = parameters[param_name].annotation

            # Type defined and Input is wrong
            if not isinstance(arg, param_type) and param_type.__name__ != '_empty':
                conv = converter.get(param_type.__name__)
                try:
                    arg = conv(arg)
                except (TypeError, ValueError) as ex:
                    msg = (
                        f'Parameter "{param_name}" is not '
                        f'of type "{param_type.__name__}" '
                        'and could not be converted into this type! - '
                        f'{str(ex)}')
                    current_app.logger.error(msg)
                    return jsonify({'error': msg}), 400

            keyword_args[param_name] = arg

        return original_func(*positional_args, **keyword_args)

    return wrapper


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
        self.tagger = Tagger()

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

    def _flush_to_db(self):
        """
        Speichert die eingelesenen Kontodaten in der Datenbank und bereinigt den Objektspeicher.

        Returns:
            int: Die Anzahl der eingefügten Datensätze
        """
        inserted_rows = self.db_handler.insert(self.data)
        self.data = None
        return inserted_rows.get('inserted')

    def _load_ruleset(self, rule_name=None, namespace='both'):
        """
        Load Rules from the Settings of for the requesting User.

        Args:
            rule_name (str, optional): Lädt die Regel mit diesem Namen.
                                       Default: Es werden alle Regeln geladen.
            namespace (str, system|user|both): Unterscheidung aus weclhem Set Regeln
                                               geladen oder gesucht werden soll.
                                               - system: nur allgemeine Regeln
                                               - user: nur private Regeln
                                               - both (default): alle Regeln
        Returns:
            list(dict): Liste von Filterregeln
        """
        #TODO: Fake Funktion
        system_rules = {
            'Supermarkets': {
                'primary': 'Lebenserhaltungskosten',
                'secondary': 'Lebensmittel',
                'regex': r"(EDEKA|Wucherpfennig|Penny|Aldi|Kaufland|netto)",
            },
        }
        user_rules = {
            'City Tax': {
                'primary': 'Haus und Grund',
                'secondary': 'Stadtabgaben',
                'parsed': {
                    'Gläubiger-ID': r'DE7000100000077777'
                },
            }
        }

        if rule_name:

            # Bestimmte Regel laden
            if namespace in ['system', 'both']:
                # Allgemein
                rule = system_rules.get(rule_name)
            if namespace == 'both':
                # oder speziell (falls vorhanden)
                rule = user_rules.get(rule_name, rule)
            if namespace == 'user':
                # Nur User
                rule = user_rules.get(rule_name)

            return {rule_name: rule}

        # Alle Regeln einzelner namespaces
        if namespace == 'system':
            return system_rules
        if namespace == 'user':
            return user_rules

        # Alle Regeln aller namespaces
        system_rules.update(user_rules)
        return system_rules

    @current_app.route('/')
    @user_input_type_converter
    def index(self):
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

    @user_input_type_converter
    @current_app.route('/upload', methods=['POST'])
    def upload(self, tx_file):
        """
        Endpunkt für das Annehmen hochgeladener Kontoumsatzdateien.
        Im Anschluss wird automatisch die Untersuchung der Inhalte angestoßen.

        Args:
            tx_file (binary): Dateiupload aus Formular-Submit
        Returns:
            html: Informationen zur Datei und Ergebnis der Untersuchung.
        """
        tx_file = request.files['tx_file']
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
        self._read_input(path)
        self._parse()

        # Eingelesene Umsätze kategorisieren
        self.tag()

        # Verarbeitete Kontiumsätze in die DB speichern und vom Objekt und Dateisystem löschen
        inserted = self._flush_to_db()
        os.remove(path)

        if inserted:
            return out.format(size=size, filename=tx_file.filename, content_type=tx_file.content_type), 201
        else:
            return out.format(size=size, filename=tx_file.filename, content_type=tx_file.content_type), 304

    @current_app.route('/view', methods=['GET'])
    @user_input_type_converter
    def view(self, iban: str = None):
        """
        Anzeige aller Umsätze zu einer IBAN

        Args:
            iban (str): IBAN, zu der die Umsätze angezeigt werden sollen (default: aus Config)
        Returns:
            html: Tabelle mit den Umsätzen
        """
        rows = self.db_handler.select(iban)
        out = """<table style="border: 1px solid black;"><thead><tr>
            <th>Datum</th> <th>Betrag</th> <th>Tag (pri)</th> <th>Tag (sec.)</th> <th>Parsed</th> <th>Hash</th>
        </tr></thead><tbody>"""
        for r in rows:
            out += f"""<tr id="tr-{r['uuid']}">
            <td class="td-date">{r['date_tx']}</td> <td class="td-betrag">{r['betrag']} {r['currency']}</td>
            <td class="td-tag1">{r['primary_tag']}</td> <td class="td-tag2">{r['secondary_tag']}</td>
            <td class="td-parsed">"""
            for parse_element in r['parsed']:
                out += f"<p>{parse_element}</p>"
            out += f"</td><td class='td-uuid'>{r['uuid']}</td>"
            out += "</tr>"
        out += """</tbody></table>"""
        return out

    @current_app.route('/tag', methods=['POST'])
    @user_input_type_converter
    def tag(self):
        """
        Kategorisiert die Kontoumsätze und aktualisiert die Daten in der Instanz.

        Args:
            rule_name:      Name der anzuwendenden Taggingregel.
                            Reserviertes Keyword 'ai' führt nur das AI Tagging aus.
                            Default: Es werden alle Regeln des Benutzers ohne das
                            AI Tagging angewendet.
            rule_primary:   Name der zu setzenden Primärkategory.
                            Default: Standardname
            rule_primary:   Name der zu setzenden Sekundärkategory.
                            Default: Standardname
            rule_regex:     Regulärer Ausdrück für die Suche im Transaktionstext.
                            Default: Wildcard
            rule_parsed_keys:   Liste mit Keys zur Prüfung in geparsten Daten.
            rule_parsed_vals:   Liste mit Values zur Prüfung in geparsten Daten.
            prio:           Value of priority for this tagging run
                            in comparison with already tagged transactions
                            This value will be set as the new priority in DB.
                            Default: 1
            prio_set:       Compare with priority but set this value instead.
                            Default: prio.
            dry_run:        Switch to show, which TX would be updated. Do not update.
                            Default: False
        Returns:
            - tagged (int): Summe aller erfolgreichen Taggings (0 bei dry_run)
            - Regelname (dict):
                - tagged (int): Anzahl der getaggten Datensätze (0 bei dry_run)
                - entries (list): UUIDs die selektiert wurden (auch bei dry_run)
        """
        data = request.json
        rule_name = data.get('rule_name')
        rule_primary = data.get('rule_primary')
        rule_secondary = data.get('rule_secondary')
        rule_regex = data.get('rule_regex')
        rule_parsed_keys = data.get('rule_parsed_keys', [])
        rule_parsed_vals = data.get('rule_parsed_vals', [])
        prio = data.get('prio', 1)
        prio_set = data.get('prio_set')
        dry_run = data.get('dry_run', False)

        # Tagging Methoden Argumente
        args = {
            'dry_run': dry_run
        }
        if prio is not None:
            args['prio'] = prio
        if prio_set is not None:
            args['prio_set'] = prio_set

        # RegEx Tagging (specific rule or all)
        if rule_regex is not None or rule_parsed_keys:

            # Custom Rule
            rule = {
                'primary': rule_primary,
                'secondary': rule_secondary,
                'regex': rule_regex
            }

            if len(rule_parsed_keys) != len(rule_parsed_vals):
                msg = 'Parse-Keys and -Vals were submitted in unequal length !'
                current_app.logger.error(msg)
                return jsonify({'error': msg}), 400

            for i, parse_key in enumerate(rule_parsed_keys):
                rule['parsed'][parse_key] = rule_parsed_vals[i]

            if rule_name is None:
                rule_name = 'Custom Rule'

            rules = {rule_name: rule}

            return jsonify(self.tagger.tag_regex(self.db_handler,
                                                 rules, prio=prio, prio_set=prio_set, dry_run=dry_run))

        if rule_name == 'ai':
            # AI only
            return jsonify(self.tagger.tag_ai(self.db_handler,
                                              rules, prio=prio, prio_set=prio_set, dry_run=dry_run))

        # Benutzer Regeln laden
        rules = self._load_ruleset(rule_name)
        if not rules:
            if rule_name:
                raise KeyError((f'Eine Regel mit dem Namen {rule_name} '
                                'konnte für den User nicht gefunden werden.'))

            raise ValueError('Es existieren noch keine Regeln für den Benutzer')

        # Benutzer Regeln anwenden
        return jsonify(self.tagger.tag_regex(self.db_handler,
                                             rules, prio=prio, prio_set=prio_set, dry_run=dry_run))

    @current_app.route('/setManualTag', methods=['POST'])
    @user_input_type_converter
    def setManualTag(self):
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

    @current_app.route('/truncateDatabase', methods=['POST'])
    @user_input_type_converter
    def truncateDatabase(self):
        """Leert die Datenbank"""
        data = request.json
        iban = data.get('iban')
        deleted_entries = self.db_handler.truncate(iban)
        return jsonify({'deleted': deleted_entries})


def create_app() -> current_app:
    """Creating an instance from Flask with the UserInterface as Host

    Returns: FlaskApp
    """
    # Logging
    loglevel = 'INFO'
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '%(levelname)s (%(module)s): %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'root': {
            'level': loglevel,
            'handlers': ['wsgi']
        }
    })

    app = Flask(__name__)

    # Global Config
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'config.json'
    )
    app.config.from_json(config_path)
    if app.config.get('DATABASE_BACKEND') is None:
        raise IOError(f"Config Pfad '{config_path}' konnte nicht geladen werden !")


    return app

if __name__ == '__main__':
    application = create_app()
    application.run(host='0.0.0.0', port=8080)
