import os, sys
import cherrypy
import pytest

# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from reader.Generic import Reader as Generic


def setup_module():
    """Server start (wie originale App)"""



class TestClass():

    def setup_class(self):
        """Vorbereitung der Testklasse"""

        # Config
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'config.conf'
        )
        cherrypy.config.update(config_path)
        cherrypy.config.update({
            'server.socket_host': '127.0.0.1',
            'server.socket_port': 54583,
        })
        assert cherrypy.config.get('database.backend'), \
            "Unable to read Test Config"

        # Instanz von Reader
        self.Reader = Generic()
        assert self.Reader, "Reader Klasse konnte nicht instanziiert werden"


    def test_read_from_csv(self):
        """Testet das Einlesen einer CSV Datei mit Kontoumsätzen"""
        uri = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'commerzbank.csv'
        )
        transaction_list = self.Reader.from_csv(uri)
        # Check Reader Ergebnisse
        checkTransaktionList(transaction_list)

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_read_from_pdf(self):
        """Testet das Einlesen einer PDF Datei mit Kontoumsätzen"""
        return None

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_read_from_http(self):
        """Testet das Einlesen Kontoumsätzen aus einer Online-Quelle"""
        return None


def checkTransaktionList(tx_list):
    for i in range(len(tx_list)):
        entry = tx_list[i]

        # Dict Struktur
        required_keys = [
            'date_tx', 'text_tx', 'betrag', 'iban',
            'parsed', # Leer aber vorhanden
            'date_wert', 'art', 'currency' # optional aber vorhanden
        ]
        for r_key in required_keys:
            assert r_key in entry.keys(), \
                f'Der Schlüssel {r_key} ist nicht im Element zur Zeile {i} vorhanden'

        # Buchungsdatum
        assert type(entry.get('date_tx')) == float, (
            f"'date_tx' bei Zeile {i} nicht als Zeit in Sekunden (float) eingelesen: "
            f"{entry.get('date_tx')}")
        # Betrag
        assert type(entry.get('betrag')) == float, (
            f"'betrag' bei Zeile {i} nicht als Kommazahl eingelesen: "
            f"{entry.get('betrag')}")
        # Buchungstext
        text_tx = entry.get('text_tx')
        assert type(text_tx) == str and len(text_tx), \
            f"'text_tx' wurde nicht oder falsch erkannt: {text_tx}"
        # IBAN
        iban = entry.get('iban')
        assert type(iban) == str and len(iban), \
            f"'iban' wurde nicht oder falsch erkannt: {iban}"
        # Wertstellung (optional, aber bei Generic mit dabei)
        assert type(entry.get('date_wert')) == float, (
            f"'date_wert' bei Zeile {i} nicht als Zeit in Sekunden (float) eingelesen: "
            f"{entry.get('date_wert')}")
        # Buchungsart (optional, aber bei Generic mit dabei)
        buchungs_art = entry.get('art')
        assert type(buchungs_art) == str and len(buchungs_art), \
            f"'art' wurde nicht oder falsch erkannt: {iban}"
        # Währung (optional, aber bei Generic mit dabei)
        currency = entry.get('currency')
        assert type(currency) == str and len(currency) == 3, \
            f"'currency' wurde nicht oder falsch erkannt: {currency}"