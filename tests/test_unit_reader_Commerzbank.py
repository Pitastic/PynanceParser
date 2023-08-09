import os
import sys
import cherrypy
import pytest

# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from reader.Commerzbank import Reader as Generic


class TestReaderGeneric():

    def setup_class(self):
        """Vorbereitung der Testklasse"""

        # Config
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'config.conf'
        )
        cherrypy.config.update(config_path)
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
        check_transaktion_list(transaction_list)

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_read_from_pdf(self):
        """Testet das Einlesen einer PDF Datei mit Kontoumsätzen"""
        return None

    @pytest.mark.skip(reason="Currently not implemented yet")
    def test_read_from_http(self):
        """Testet das Einlesen Kontoumsätzen aus einer Online-Quelle"""
        return None


def check_transaktion_list(tx_list):
    """Helper zum Prüfen der Parsingergebnisse"""

    for i, entry in enumerate(tx_list):

        # Dict Struktur
        required_keys = [
            'date_tx', 'text_tx', 'betrag', 'iban',
            'parsed', 'primary_tag', 'secondary_tag', # Leer aber vorhanden
            'date_wert', 'art', 'currency' # optional aber vorhanden
        ]
        for r_key in required_keys:
            assert r_key in entry.keys(), \
                f'Der Schlüssel {r_key} ist nicht im Element zur Zeile {i} vorhanden'

        # Buchungsdatum
        assert isinstance(entry.get('date_tx'), float), (
            f"'date_tx' bei Zeile {i} nicht als Zeit in Sekunden (float) eingelesen: "
            f"{entry.get('date_tx')}")
        # Betrag
        assert isinstance(entry.get('betrag'), float), (
            f"'betrag' bei Zeile {i} nicht als Kommazahl eingelesen: "
            f"{entry.get('betrag')}")
        # Buchungstext
        text_tx = entry.get('text_tx')
        assert isinstance(text_tx, str) and len(text_tx), \
            f"'text_tx' wurde nicht oder falsch erkannt: {text_tx}"
        # IBAN
        iban = entry.get('iban')
        assert isinstance(iban, str) and len(iban), \
            f"'iban' wurde nicht oder falsch erkannt: {iban}"
        # Wertstellung (optional, aber bei Commerzbank mit dabei)
        assert isinstance(entry.get('date_wert'), float), (
            f"'date_wert' bei Zeile {i} nicht als Zeit in Sekunden (float) eingelesen: "
            f"{entry.get('date_wert')}")
        # Buchungsart (optional, aber bei Commerzbank mit dabei)
        buchungs_art = entry.get('art')
        assert isinstance(buchungs_art, str) and len(buchungs_art), \
            f"'art' wurde nicht oder falsch erkannt: {iban}"
        # Währung (optional, aber bei Commerzbank mit dabei)
        currency = entry.get('currency')
        assert isinstance(currency, str) and len(currency) == 3, \
            f"'currency' wurde nicht oder falsch erkannt: {currency}"
