#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisc Module for easy Imports and Methods"""

import os, sys
import cherrypy
from bs4 import BeautifulSoup
import requests
import pytest
import cherrypy.test.helper as cphelper

# Add Parent for importing from 'app.py'
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import Server Startup
from app.app import UserInterface


@pytest.fixture(scope='function', autouse=True)
def between_tests_cleaner(request):
    def do_truncate():
        r = requests.get('http://127.0.0.1:54583/truncateDatabase')
        print("Truncating DB...", r.text, r.status_code)
    request.addfinalizer(do_truncate)



class TestClass(cphelper.CPWebCase):
    """Testen der Endpunkte und Basisfunktionen"""

    def setUp(self):
        # Pass GC Test from CherryPy (will fail otherwise)
        self.do_gc_test = False
        self.uri = f"{self.scheme}://{self.interface()}:{self.PORT}"

    @staticmethod
    def setup_server():
        """Server start (wie originale App)"""
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'config.conf'
        )
        cherrypy.config.update(config_path)
        cherrypy.config.update({
            'server.socket_host': '127.0.0.1',
            'server.socket_port': 54583,
        })
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
        # Cleared DB ?
        response0 = requests.get(f"{self.uri}/view?iban={cherrypy.config['iban']}")
        assert "<td class=" not in response0.text, "Die Datenbank war zum Start des Tests nicht leer"

        # Visit Form
        self.getPage("/")
        self.assertStatus(200)
        self.assertInBody('type="submit')

        # Prepare File
        content = getTestFileContents('commerzbank.csv', binary=True)
        files = {'tx_file': ('commerzbank.csv', content)}
        # Post File
        response = requests.post(f"{self.uri}/upload", files=files)

        # Check Response
        assert response.status_code == 201, \
            "Die Seite hat den Upload nicht wie erwartet verarbeitet"
        assert 'tx_file filename: commerzbank.csv' in response.text, \
            "Angaben zum Upload wurden nicht gefunden"
        
        # Aufruf der Transaktionen auf verschiedene Weisen
        response1 = requests.get(f"{self.uri}/view", params={})
        response2 = requests.get(f"{self.uri}/view?iban={cherrypy.config['iban']}")
        assert response1.status_code == response2.status_code == 200, \
            "Die Ergebnisseite mit den Transaktionen ist nicht (richtig) erreichbar"
        result = response2.text
        assert result == response1.text, \
            "Der Aufruf des DEFAULT Kontos aus der Konfig ist nicht richtig"

        # -- Check Parsing --
        soup = BeautifulSoup(result, features="html.parser")

        # 1. Example
        hash = 'cf1fb4e6c131570e4f3b2ac857dead40'
        row1 = soup.css.select(f'#tr-{hash}')
        assert len(row1) == 1, \
            f"Es wurden {len(row1)} rows für das erste Beispiel gefunden"

        content = row1[0].css.filter('.td-betrag')[0].contents[0]
        assert content == '-11.63 EUR', \
            f"Der Content von {hash} ist anders als erwartet: '{content}'"

        # 2. Example
        hash = '786e1d4e16832aa321a0176c854fe087'
        row2 = soup.css.select(f'#tr-{hash}')
        assert len(row2) == 1, \
            f"Es wurden {len(row2)} rows für das zweite Beispiel gefunden"

        content = row2[0].css.filter('.td-betrag')[0].contents[0]
        assert content == '-221.98 EUR', \
            f"Der Content von {hash} / 'betrag' ist anders als erwartet: '{content}'"

        content = [child.contents[0] for child in row2[0].select('.td-parsed p')]
        assert 'Mandatsreferenz' in content, \
            f"Der Content von {hash} / 'parsed' ist anders als erwartet: '{content}'"

    def test_double_upload(self):
        """Lädt zwei Dateien hoch und prüft die unterschiedlichen HTTP Stati"""
        # Cleared DB ?
        response0 = requests.get(f"{self.uri}/view?iban={cherrypy.config['iban']}")
        assert "<td class=" not in response0.text, "Die Datenbank war zum Start des Tests nicht leer"

        # Prepare File 1
        content = getTestFileContents('commerzbank.csv', binary=True)
        files = {'tx_file': ('commerzbank.csv', content)}

        # Post File 1
        response1 = requests.post(f"{self.uri}/upload", files=files)
        status_code_1 = response1.status_code
        assert status_code_1 == 200

        # Post File 2
        response2 = requests.post(f"{self.uri}/upload", files=files)
        status_code_2 = response2.status_code
        # Same TX: Keine neuen Einträge angelegt:
        assert status_code_2 == 200, \
            "Beim zweiten Upload der gleichen Transaktionen dürfen keine neuen Datensätze angelegt werden"

        # Double-Check: Anzahl der Einträge
        response3 = requests.get(f"{self.uri}/view?iban={cherrypy.config['iban']}")
        result = response3.text
        soup = BeautifulSoup(result,features="html.parser")
        rows = soup.css.select(f'table .td-hash')

        assert len(rows) == 5, f"Es wurden zu viele Einträge ({len(rows)}) angelegt"


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
        relative_path
    )
    flag = 'r'
    if binary:
        flag = f'{flag}b'
    with open(path, flag) as test_data:
        content = test_data.read()
    return content