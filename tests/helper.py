"""Hilfsfunktionen für die Tests"""

import os
import json


def check_transaktion_list(tx_list):
    """Helper zum prüfen der Parsingergebnisse"""

    for i, entry in enumerate(tx_list):

        # Dict Struktur
        required_keys = [
            'date_tx', 'text_tx', 'betrag', 'iban',
            'parsed', 'category', 'tags', # Leer aber vorhanden
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

        # Wertstellung (optional, aber bei Generic mit dabei)
        assert isinstance(entry.get('date_wert'), float), (
            f"'date_wert' bei Zeile {i} nicht als Zeit in Sekunden (float) eingelesen: "
            f"{entry.get('date_wert')}")

        # Buchungsart (optional, aber bei Generic mit dabei)
        buchungs_art = entry.get('art')
        assert isinstance(buchungs_art, str) and len(buchungs_art), \
            f"'art' wurde nicht oder falsch erkannt: {iban}"

        # Währung (optional, aber bei Generic mit dabei)
        currency = entry.get('currency')
        assert isinstance(currency, str) and len(currency) == 3, \
            f"'currency' wurde nicht oder falsch erkannt: {currency}"


def generate_fake_data(count, json_path='commerzbank.json'):
    """
    Erstellt ausgedachte Transaktionen in gewünschter Anzahl.
    Zunächst auf Grundlage einer Beispieldatei.

    Args:
        count, int: Anzahl an zu generierender Transaktionsobjekte
    Returns:
        list of dicts mit den Transaktionsobjekten
    """
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        json_path
    )
    with open(path, 'rb') as test_data:
        object_list = json.load(test_data)

    return object_list[0:count]


def check_entry(tx_entry, key_vals=None):
    """
    Prüft die STRUKTUR eines Datenbankeintrags

    Args:
        entry, dict: Einzelner Datenbankeintrag
        key_vals, dict: key:value-Pairs die so vorkommen müssen
    """
    required_keys = [
        'uuid',
        'date_tx', 'text_tx', 'betrag', 'iban',
        'parsed', 'date_wert', 'art', 'currency',
        'category', 'tags'
    ]
    for r_key in required_keys:
        assert r_key in tx_entry.keys(), \
            f'Der Schlüssel {r_key} ist nicht im Element vorhanden'

    if key_vals is None:
        return None

    for key, val in key_vals.items():
        if tx_entry.get(key) is None:
            continue
        assert tx_entry[key] == val, f"Der Schlüssel {key} hat den falschen Wert"

    return True


def get_testfile_contents(relative_path, binary=True):
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


class MockDatabase:
    """
    Mock the Database connection and work with fake entries.
    """

    def __init__(self):
        """Konstruktor hinterlegt Variablen"""
        self.query1 = [
            {
                'key': 'prio', 'value': 1,
                'compare': '<'
            }, {
                'key': 'text_tx', 'value': '(EDEKA|Wucherpfennig|Penny|Aldi|Kaufland|netto)',
                'compare': 'regex'
            }
        ]
        self.query_categorize = [
            {'key': 'prio', 'value': 1, 'compare': '<'},
            {'key': 'tags', 'value': ['Stadt', 'Steuer'], 'compare': 'in'},
            {'key': {'parsed': 'Gläubiger-ID'}, 'value': 'DE7000100000077777', 'compare': '=='}
        ]
        self.query_tag = [
            {'key': 'prio', 'value': 99, 'compare': '<'},
            {'key': 'text_tx', 'value': '(ABGABEN\\sLT\\.\\sBESCHEID)', 'compare': 'regex'}
        ]
        self.query_ai = [
            {'key': 'category', 'value': None, 'compare': '=='},
            {'key': 'tags', 'value': None, 'compare': '=='}
        ]
        self.query_custom_tagging = [
            {'key': 'prio', 'value': 99, 'compare': '<'},
            {'key': 'betrag', 'compare': '<', 'value': -100},
            {'key': {'parsed': 'custom_key1'}, 'value': 'custom_val1', 'compare': 'regex'},
            {'key': {'parsed': 'custom_key2'}, 'value': 'custom_val2', 'compare': 'regex'}
        ]
        self.query_custom_cat = [
            {'key': 'prio', 'value': 22, 'compare': '<'},
            {'key': 'betrag', 'compare': '<', 'value': -999},
            {'key': {'parsed': 'custom_key1'}, 'value': 'custom_val1', 'compare': 'regex'},
            {'key': {'parsed': 'custom_key2'}, 'value': 'custom_val2', 'compare': 'regex'}
        ]
        self.db_all = [

            {
            'date_tx': 1672531200, 'date_wert': 1684195200, 'art': 'Überweisung',
            'text_tx': ('Wucherpfennig sagt Danke 88//HANNOV 2023-01-01T08:59:42 '
                        'KFN 9 VJ 7777 Kartenzahlung'),
            'betrag': -11.63, 'iban': 'DE89370400440532013000', 'currency': 'USD',
            'parsed': {}, 'category': 'Updated', 'tags': [],
            'uuid': 'b5aaffc31fa63a466a8b55962995ebcc', 'prio': 0
            },

            {
            'date_tx': 1672617600, 'date_wert': 1684108800, 'art': 'Überweisung',
            'text_tx': ('MEIN GARTENCENTER//Berlin 2023-01-02T12:57:02 KFN 9 VJ 7777 '
                        'Kartenzahlung'),
            'betrag': -118.94, 'iban': 'DE89370400440532013000', 'currency': 'USD',
            'parsed': {}, 'category': 'Updated', 'tags': [],
            'uuid': '13d505688ab3b940dbed47117ffddf95', 'prio': 0
            },

            {
            'date_tx': 1672704000, 'date_wert': 1684108800, 'art': 'Überweisung',
            'text_tx': ('EDEKA, München//München/ 2023-01-03T14:39:49 KFN 9 VJ '
                        '7777 Kartenzahlung'),
            'betrag': -99.58, 'iban': 'DE89370400440532013000', 'currency': 'EUR',
            'parsed': {}, 'category': None, 'tags': [],
            'uuid': 'a8bd1aa187c952358c474ca4775dbff8', 'prio': 0
            },

            {
            'date_tx': 1672790400, 'date_wert': 1684108800, 'art': 'Überweisung',
            'text_tx': ('DM FIL.2222 F:1111//Frankfurt/DE 2023-01-04T13:22:16 KFN 9 VJ '
                        '7777 Kartenzahlung'),
            'betrag': -71.35, 'iban': 'DE89370400440532013000', 'currency': 'EUR',
            'parsed': {}, 'category': None, 'tags': [],
            'uuid': 'a1eb37e4ed4a22a38bdeef2f34fb76c3', 'prio': 0
            },

            {
            'date_tx': 1672876800, 'date_wert': 1684108800, 'art': 'Überweisung',
            'text_tx': ('Stadt Halle 0000005112 OBJEKT 0001 ABGABEN LT. BESCHEID '
                        'End-to-End-Ref.: 2023-01-00111-9090-0000005112 '
                        'Mandatsref: M1111111 Gläubiger-ID: DE7000100000077777 '
                        'SEPA-BASISLASTSCHRIFT wiederholend'),
            'betrag': -221.98, 'iban': 'DE89370400440532013000', 'currency': 'EUR',
            'parsed': {'Mandatsreferenz': 'M1111111'}, 'category': None, 'tags': [],
            'uuid': 'ba9e5795e4029213ae67ac052d378d84', 'prio': 0
            }

        ]

    def select(self, collection=None, condition=None, multi=None): # pylint: disable=unused-argument
        """
        Nimmt alle Argumente der echten Funktion entgegen und gibt Fake-Daten zurück.
        Condition wird für die Auswahl der Fake-Datensätze geprüft.

        Returns:
            dict:
                - result, list: Liste der ausgewählten Fake-Datensätze
        """
        if condition == self.query1:
            return [self.db_all[0], self.db_all[2]]

        if condition == self.query_categorize:
            return [{'uuid': 'test_categorize'}]

        if condition == self.query_tag:
            return [{'uuid': 'test_tag'}]

        if condition == self.query_ai:
            return [
                {
                'date_tx': 1672531200, 'date_wert': 1684195200, 'art': 'Überweisung',
                'text_tx': ('Wucherpfennig sagt Danke 88//HANNOV 2023-01-01T08:59:42 '
                            'KFN 9 VJ 7777 Kartenzahlung'),
                'betrag': -11.63, 'iban': 'DE89370400440532013000', 'currency': 'EUR',
                'parsed': {}, 'category': None, 'tags': [],
                'uuid': 'b5aaffc31fa63a466a8b55962995ebcc', 'prio': 0
                }
            ]
        if condition == self.query_custom_tagging:
            return [{'uuid': 'custom_tagging_uuid'}]

        if condition == self.query_custom_cat:
            return [{'uuid': 'custom_categorize_uuid'}]

        print(f"!!! Condition not found in Mock: {condition}")

        return []

    def update(self, data, collection=None, condition=None, multi=None): # pylint: disable=unused-argument
        """
        Nimmt alle Argumente der echten Funktion entgegen und gibt Fake-Daten zurück.
        Condition wird für die Auswahl der Fake-Datensätze geprüft.

        Returns:
            dict:
                - updated, int: Anzahl der angeblich aktualisierten Datensätze
        """
        if condition.get('key') == 'uuid':

            if condition.get('value') == 'custom_tagging_uuid':
                # Test Tags to set wih cstom rule here:
                assert data.get('tags') == ['custom_tagging1', 'custom_tagging2'], \
                    "Die Tags der Custom Rule wurden nicht richtig übergeben"

            if condition.get('value') == 'custom_categorize_uuid':
                # Test Category to set wih cstom rule here:
                assert data.get('category') == 'custom_category', \
                    "Die Kategorie der Custom Rule wurde nicht richtig übergeben"
                assert data.get('prio') == 33, \
                    "Die Priorität_set der Custom Rule wurde nicht richtig übergeben"

            return {'updated': 1}

        return {'updated': 0}

    def filter_metadata(self, condition, *args, **kwargs): # pylint: disable=unused-argument
        """Mock der Filtermetadatenabfrage
        Args:
            condition (dict): Filterkriterien
            *args, **kwargs: Weitere Argumente
        Returns:
            list: Liste der Metadaten
        """
        if condition == {"key": "metatype", "value": "parser"}:
            return [
                {
                    "name": "Mandatsreferenz",
                    "metatype": "parser",
                    "regex": "Mandatsref\\:\\s?([A-z0-9]*)"
                },{
                    "name": "Gläubiger-ID",
                    "metatype": "parser",
                    "regex": "([A-Z]{2}[0-9]{2}[0-9A-Z]{3}(?:[0-9]{11}|[0-9]{19}))"
                }
            ]
        if condition == {"key": "metatype", "value": "category"}:
            return [
                {
                    "metatype": "category",
                    "name": "Abgaben",
                    "category": "Öffentliche Ausgaben",
                    "multi": "OR",
                    "filter": [{
                        "key": "tags",
                        "value": ["Stadt", "Steuer"],
                        "compare": "in"
                    }],
                    "parsed": {
                        "Gläubiger-ID": "DE7000100000077777"
                    }
                }
            ]
        if condition == {"key": "metatype", "value": "rule"}:
            return [
                {
                    "metatype": "rule",
                    "name": "City Tax",
                    "tags": ["Stadt"],
                    "filter": [{
                        "key": "text_tx",
                        "value": "(ABGABEN\\sLT\\.\\sBESCHEID)",
                        "compare": "regex"
                    }]
                }
            ]
        return []
