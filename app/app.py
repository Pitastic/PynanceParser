#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisklasse mit Methoden für den Programmablauf."""

import os
import sys
import re
import cherrypy

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
        if cherrypy.config['database.backend'] == 'tiny':
            self.db_handler = TinyDbHandler()
        elif cherrypy.config['database.backend'] == 'mongo':
            self.db_handler = MongoDbHandler()
        else:
            raise NotImplementedError(("The configure database engine ",
                                     f"{cherrypy.config['database.backend']} ",
                                      "is not supported !"))
        assert self.db_handler, \
            (f"DbHandler {cherrypy.config['database.backend']} Klasse konnte nicht ",
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

    def _load_ruleset(self, rule_name=None):
        """
        Load Rules from the Settings of for the requesting User.

        Args:
            rule_name (str, optional): Lädt die Regel mit diesem Namen.
                                       Default: Es werden alle Regeln geladen.

        Returns:
            list(dict): Liste von Filterregeln
        """
        #TODO: Fake Funktion
        test_rules = {
            'Supermarkets': {
                'primary': 'Lebenserhaltungskosten',
                'secondary': 'Lebensmittel',
                'regex': r"(EDEKA|Wucherpfennig|Penny|Aldi|Kaufland|netto)",
            },
            'City Tax': {
                'primary': 'Haus und Grund',
                'secondary': 'Stadtabgaben',
                'parsed': {
                    'Gläubiger-ID': r'DE7000100000077777'
                },
            }
        }

        if rule_name:
            return [test_rules.get(rule_name)]

        return test_rules

    @cherrypy.expose
    def index(self):
        """
        Startseite mit Navigation und Uploadformular.

        Returns:
            html: Startseite mit Navigation
        """
        return """<html><body>
            <h2>Upload a file</h2>
            <form action="upload" method="post" enctype="multipart/form-data">
            filename: <input type="file" name="tx_file" /><br />
            <input type="submit" />
            </form>
        </body></html>
        """

    @cherrypy.expose
    def upload(self, tx_file):
        """
        Endpunkt für das Annehmen hochgeladener Kontoumsatzdateien.
        Im Anschluss wird automatisch die Untersuchung der Inhalte angestoßen.

        Args:
            tx_file (binary): Dateiupload aus Formular-Submit
        Returns:
            html: Informationen zur Datei und Ergebnis der Untersuchung.
        """
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
                data = tx_file.file.read(8192)
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
            cherrypy.response.status = 201 # created
        else:
            cherrypy.response.status = 304 # not modified

        return out.format(size=size, filename=tx_file.filename, content_type=tx_file.content_type)

    @cherrypy.expose
    def view(self, iban=None):
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

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def tag(self, rule_name=None, rule=None, prio=None, prio_set=None, dry_run=True):
        """
        Kategorisiert die Kontoumsätze und aktualisiert die Daten in der Instanz.

        Args:
            rule_name (str | ai, optional): Name der anzuwendenden Taggingregel.
                                            Reserviertes Keyword 'ai' führt nur
                                            das AI Tagging aus. Default: Es werden
                                            alle Regeln des Benutzers ohne das AI
                                            Tagging angewendet.
            rule (dict, optional): Regel mit der getaggt werden soll.
                                   Default: Ist rule_name ohne rule angegeben, wird
                                   eine Regel mit diesem Namen aus der Benutzerdatenbank
                                   geladen. Ein Fehlen dieser Regel wirft eine Exception.
        Returns:
            json dict:
                - tagged (int): Summe aller erfolgreichen Taggings (0 bei dry_run)
                - Regelname (dict):
                    - tagged (int): Anzahl der getaggten Datensätze (0 bei dry_run)
                    - entries (list): UUIDs die selektiert wurden (auch bei dry_run)
        """
        # Tagging Methoden Argumente
        args = {
            'dry_run': dry_run
        }
        if prio is not None:
            args['prior'] = prio
        if prio_set is not None:
            args['prio_setr'] = prio_set

        # RegEx Tagging (specific rule or all)
        if rule is not None:

            # Custom Rule
            if rule_name is None:
                rule_name = 'Custom Rule'
            rules = [{rule_name: rule}],

            return self.tagger.tag_regex(self.db_handler, rules, **args)

        if rule_name == 'ai':
            # AI only
            return self.tagger.tag_ai(self.db_handler, rules, **args)

        # Benutzer Regeln laden
        rules = self._load_ruleset(rule_name)
        if not rules:
            if rule_name:
                raise KeyError((f'Eine Regel mit dem Namen {rule_name} '
                                'konnte für den User nicht gefunden werden.'))
            else:
                raise ValueError('Es existieren noch keine Regeln für den Benutzer')

        # Benutzer Regeln anwenden
        return self.tagger.tag_regex(self.db_handler, rules, **args)

    @cherrypy.expose
    @cherrypy.tools.json_out()
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
        updated_entries = self.db_handler.update(
            {
                'main_category': primary_tag,
                'second_category': secondary_tag,
            },
            f'WHERE id = {t_id}')
        return {'updated': updated_entries}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def truncateDatabase(self, iban=None):
        """Leert die Datenbank"""
        deleted_entries = self.db_handler.truncate(iban)
        return { 'deleted': deleted_entries }

if __name__ == '__main__':

    # Global Config
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'config.conf'
    )
    cherrypy.config.update(config_path)
    if cherrypy.config.get('database.backend') is None:
        raise IOError(f"Config Pfad '{config_path}' konnte nicht heladen werden !")

    #cherrypy.quickstart(UserInterface(), '/', config_path)
    cherrypy.tree.mount(UserInterface(), "/", config_path)
    cherrypy.engine.start()
    cherrypy.engine.block()
