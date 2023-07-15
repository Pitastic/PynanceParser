#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisc Module for easy Imports and Methods"""

import os
import cherrypy
import pytest
import requests
import cherrypy.test.helper as cphelper

# Import Server Startup
from app import UserInterface


class TestClass(cphelper.CPWebCase):
    """Testen der Endpunkte und Basisfunktionen"""

    def setUp(self):
        # Pass GC Test from CherryPy (will fail otherwise)
        self.do_gc_test = False

    @staticmethod
    def setup_server():
        """Server start (wie originale App)"""
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'testdata',
            'config.conf'
        )
        cherrypy.config.update(config_path)
        assert cherrypy.config.get('database.backend')

        cherrypy.tree.mount(UserInterface(), "/", config_path)
        cherrypy.engine.start()
        cherrypy.engine.exit()


    def test_reachable_endpoints(self):
        """
        Geht die Seiten der Ui durch und prüft,
        ob diese generell erreichbar sind.
        """
        # /index
        self.getPage("/")
        self.assertStatus(200)

        #/view
        self.getPage("/view")
        self.assertStatus(200)
        self.getPage(f"/view?iban={cherrypy.config['iban']}")
        self.assertStatus(200)


    def test_upload_csv_commerzbank(self):
        """
        Lädt Beispieldaten über das Formular hoch und überprüft
        ob die Datei angenommen wird und die Serverseitige Verarbeitung durchläuft.
        """
        # Visit Form
        self.getPage("/")
        self.assertStatus(200)
        self.assertInBody('type="submit')
        # Prepare File
        content = getTestFileContents('commerzbank.csv', binary=True)
        files = {'tx_file': ('commerzbank.csv', content)}
        # Post File
        uri = f"{self.scheme}://{self.interface()}:{self.PORT}"
        response = requests.post(f"{uri}/upload", files=files)
        # Check Response
        #TODO: Sollte 201 (created) sein (da es den Record noch nich geben kann)
        assert response.status_code == 200, \
            "Die Seite hat den Upload nicht wie erwartet verarbeitet"
        assert 'tx_file filename: commerzbank.csv' in response.text, \
            "Angaben zum Upload wurden nicht gefunden"

    def test_parsed_commerzbank(self):
        """
        Überprüft die Ergebnisse des Uploads aus 'test_upload_csv_commerzbank'
        in Hinblick auf das Parsing.
        """
        # Hochladen der Testdatei
        self.test_upload_csv_commerzbank()
        # Aufruf der Transaktionen auf verschiedene Weisen
        uri = f"{self.scheme}://{self.interface()}:{self.PORT}"
        response1 = requests.get(f"{uri}/view", params={})
        response2 = requests.get(f"{uri}/view?iban={cherrypy.config['iban']}")
        assert response1.status_code == response2.status_code == 200, \
            "Die Ergebnisseite mit den Transaktionen ist nicht (richtig) erreichbar"
        result = response2.text
        assert result == response1.text, \
            "Der Aufruf des DEFAULT Kontos aus der Konfig ist nicht richtig"
        # Überprüfen des Parsings
        tx_data = [{
            'hash': 'cf1fb4e6c131570e4f3b2ac857dead40',
            'datum': '',
            'betrag': '-11.63',
            'parsed': '',
            'tag1': '',
            'tag2': ''
        }, {
            'hash': '786e1d4e16832aa321a0176c854fe087',
            'datum': '',
            'betrag': '-221.98',
            'parsed': 'Mandatsreferenz',
            'tag1': '',
            'tag2': ''
        }]
        for tx in tx_data:
            hash = tx.get('hash')
            if hash is not None:
                assert hash in result, f"Der Hash '{hash}' konnte nicht gefunden werden: {tx}"
            betrag = tx.get('betrag')
            if betrag is not None:
                assert betrag in result, f"Der betrag '{betrag}' konnte nicht gefunden werden: {tx}"
            parsed = tx.get('parsed')
            if parsed is not None and parsed:
                hash = hash if hash else 'unbekannt'
                for p in parsed:
                    assert parsed in result, f"Die TX '{hash}' hast nicht das Parsing '{p}' erhalten: {tx}"

@pytest.fixture(scope='session', autouse=True)
def cleanup_testfiles():
    """CleaUp"""
    yield
    print("CleanUp: Deleting Testdatabase....")
    os.remove(os.path.join(
            cherrypy.config['database.uri'],
            cherrypy.config['database.name']
    ))

def getTestFileContents(relative_path, binary=True):
    """
    Gibt den Dateiinhalt einer Beispieldatei zurück.

    Args:
        relative_path (str): Pfad oder Dateiname im Ordner 'testdata'
        binary (bool): Content ist binary (default) oder str
    Returns:
        bytes/str: Inhalt der Datei
    """
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'testdata',
        relative_path
    )
    flag = 'r'
    if binary:
        flag = f'{flag}b'
    with open(path, flag) as test_data:
        content = test_data.read()
    return content