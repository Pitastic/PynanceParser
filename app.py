#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisklasse mit Methoden für den Programmablauf."""

import hashlib
import os, sys
import re
import cherrypy

#parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#sys.path.append(parent_dir)

from handler.TinyDb import TinyDbHandler
from handler.MongoDb import MongoDbHandler
from handler.Tags import Tagger

from parsers.Generic import Parser as Generic
from parsers.Commerzbank import Parser as Commerzbank


class UserInterface(object):
    """
    Basisklasse mit Methoden für den Programmablauf.
    """
    def __init__(self):
        """
        Initialisiert eine Instanz der Basisklasse und lädt die Konfiguration sowie die Logunktion.
        """
        #TODO: Mehr als eine IBAN unterstützen
        # Handler
        # Datenbankhandler
        self.database = {
            'tiny': TinyDbHandler,
            'mongo': MongoDbHandler
        }.get(cherrypy.config['database.backend'])
        self.database = self.database()
        # Parser
        self.parsers = {
            'Generic': Generic,
            'Commerzbank': Commerzbank,
        }
        # Tagger
        self.tagger = Tagger()
        #TODO: DB Interface und evtl. auch Tagger in BUS einbauen

        # Weitere Attribute
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
            bank, self.parsers.get('Generic')
        )()

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
        #TODO: Datei wieder löschen
        path = '/tmp/test.file'
        with open(path, 'wb') as f:
            while True:
                data = tx_file.file.read(8192)
                if not data:
                    break
                size += len(data)
                f.write(data)

        # Daten einlesen und in Object speichern (Bank und Format default bzw. wird geraten)
        self.read_input(path)
        self.parse()

        # Eingelesene Umsätze kategorisieren
        self.tag()

        # Verarbeitete Kontiumsätze in die DB speichern und vom Objekt löschen
        self.flush_to_db()

        #TODO: Wenn Daten geschrieben wurden, sollte die Response 201 sein
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
        rows = self.database.select(iban)
        out = """<table style="border: 1px solid black;"><thead><tr>
            <th>Datum</th> <th>Betrag</th> <th>Tag (pri)</th> <th>Tag (sec.)</th> <th>Parsed</th> <th>Hash</th>
        </tr></thead><tbody>"""
        for r in rows:
            out += f"""<tr>
            <td>{r['date_tx']}</td> <td>{r['betrag']} {r['currency']}</td>
            <td>{r['primary_tag']}</td> <td>{r['secondary_tag']}</td>
            <td>"""
            for parse_element in r['parsed']:
                out += f"<p>{parse_element}</p>"
            out += f"</td><td>{r['hash']}</td>"
            out += "</tr>"
        out += """</tbody></table>"""
        return out

    @cherrypy.expose
    def tag(self):
        """
        Kategorisiert die Kontoumsätze und aktualisiert die Daten in der Instanz.

        Args:
            data (str): Kontoumsätze, die kategorisiert werden sollen
        Returns:
            int: Anzahl der kategorisierten Daten.
        """
        #TODO: tag (Fake Methode)
        #TODO: 'data' aus 'self' , 'session' oder von anderer Funktion übergeben lassen?
        # 1. RegEx Tagging
        count = self.tagger.tag_regex(data=self.data)
        # 2. AI Tagging
        count = count + self.tagger.tag_ai(data=self.data)
        return count

    @cherrypy.expose
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
        return self.database.update(
            {
                'main_category': primary_tag,
                'second_category': secondary_tag,
            },
            f'WHERE id = {t_id}')

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
