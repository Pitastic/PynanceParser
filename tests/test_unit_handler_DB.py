import os
import sys
import json
import cherrypy

# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from handler.TinyDb import TinyDbHandler
from handler.MongoDb import MongoDbHandler


class TestDbHandler():

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
        assert cherrypy.config.get('database.backend') != "" and \
               cherrypy.config.get('database.name') != "" and \
               cherrypy.config.get('database.uri') != "", \
            "DB Handler is not set properly in Config"
        print('[', 16*'-', f"> ]  Testing {cherrypy.config.get('database.backend')}",
              "(change Config for another Handler)")

        assert cherrypy.config['iban'] != "", "IBAN not set in Config"

        # Starten von DbHandler
        self.db_engine = cherrypy.config['database.backend']
        self.db_handler = {
            'tiny': TinyDbHandler,
            'mongo': MongoDbHandler
        }.get(self.db_engine)()
        assert self.db_handler, "TinyDbHandler Klasse konnte nicht instanziiert werden"
        self.db_handler.truncate()


    def test_insert(self):
        """Testet das Einfügen von Datensätzen"""
        # Einzelner Datensatz
        data = generate_fake_data(1)[0]
        id_count = self.db_handler.insert(data,
                                        collection=cherrypy.config['iban'])
        assert id_count == 1, \
            f"Es wurde nicht die erwartete Anzahl an Datensätzen eingefügt: {id_count}"

        # Zwischendurch leeren
        delete_count = self.db_handler.truncate()
        assert delete_count == 1, "Die Datenbank konnte während des Tests nicht geleert werden"

        # Liste von Datensätzen
        data = generate_fake_data(4)
        id_count = self.db_handler.insert(data, collection=cherrypy.config['iban'])
        assert id_count == 4, \
            f"Es wurde nicht die erwartete Anzahl an Datensätzen eingefügt: {id_count}"

        # Keine Duplikate
        data = generate_fake_data(5)
        id_count = self.db_handler.insert(data, collection=cherrypy.config['iban'])
        assert id_count == 1, \
            f"Es wurden doppelte Datensätze eingefügt: {id_count}"

    def test_select_all(self):
        """Testet das Auslesen von allen Datensätzen"""
        # Liste von Datensätzen einfügen
        self.db_handler.truncate()
        data = generate_fake_data(5)
        self.db_handler.insert(data, collection=cherrypy.config['iban'])

        # Alles selektieren
        result_all = self.db_handler.select(cherrypy.config['iban'])
        assert len(result_all) == 5, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_all)}"
        for entry in result_all:
            check_entry(entry)

    def test_select_filter(self):
        """Testet das Auslesen von einzelnen und mehreren Datensätzen mit Filter"""
        # Selektieren mit Filter (by Hash)
        query = {'key': 'hash', 'value': '13d505688ab3b940dbed47117ffddf95'}
        result_filtered = self.db_handler.select(cherrypy.config['iban'],
                                                condition=query)
        assert len(result_filtered) == 1, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry, key_vals={'date_tx': 1672617600, 'betrag': -118.94})

        # Selektieren mit Filter (by Art)
        query = {'key': 'art', 'value': 'Lastschrift'}
        result_filtered = self.db_handler.select(cherrypy.config['iban'], condition=query)
        assert len(result_filtered) == 5, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)

    def test_select_like(self):
        """Testet das Auslesen von Datensätzen mit Textfiltern (like)"""
        # Selektieren mit Filter (by LIKE Text-Content)
        query = {'key': 'text_tx', 'compare': 'like', 'value': 'Garten'}
        result_filtered = self.db_handler.select(cherrypy.config['iban'],
                                                condition=query)
        assert len(result_filtered) == 1, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)

    def test_select_lt(self):
        """Testet das Auslesen von Datensätzen mit 'kleiner als'"""
        query = {'key': 'betrag', 'compare': '<', 'value': -100}
        result_filtered = self.db_handler.select(cherrypy.config['iban'],
                                                condition=query)
        assert len(result_filtered) == 2, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)

    def test_select_lt_eq(self):
        """Testet das Auslesen von Datensätzen mit 'kleiner als, gleich'"""
        query = {'key': 'betrag', 'compare': '<=', 'value': -71.35}
        result_filtered = self.db_handler.select(cherrypy.config['iban'], condition=query)
        assert len(result_filtered) == 4, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)

    def test_select_not_eq(self):
        """Testet das Auslesen von Datensätzen mit 'ungleich'"""
        query = {'key': 'date_wert', 'compare': '!=', 'value': 1684108800}
        result_filtered = self.db_handler.select(cherrypy.config['iban'],
                                                condition=query)
        assert len(result_filtered) == 1, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)

    def test_select_regex(self):
        """Testet das Auslesen von Datensätzen mit Textfiltern (regex)"""
        query = {'key': 'text_tx', 'compare': 'regex', 'value': r'KFN\s[0-9]\s[A-Z]{2}\s[0-9]{3,4}'}
        result_filtered = self.db_handler.select(cherrypy.config['iban'], condition=query)
        assert len(result_filtered) == 4, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)

    def test_select_multi(self):
        """Testet das Auslesen von Datensätzen mit mehreren Filterargumenten"""
        # Selektieren mit Filter (mehrere Bedingungen - AND)
        query = [
            {'key': 'text_tx', 'compare': 'like', 'value': 'Kartenzahlung'},
            {'key': 'betrag', 'compare': '>', 'value': -100},
            {'key': 'betrag', 'compare': '<', 'value': -50},
        ]
        result_filtered = self.db_handler.select(cherrypy.config['iban'],
                                                condition=query,
                                                multi='AND')
        assert len(result_filtered) == 2, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)

        # Selektieren mit Filter (mehrere Bedingungen - OR)
        query = [
            {'key': 'text_tx', 'compare': 'like', 'value': 'München'},
            {'key': 'text_tx', 'compare': 'like', 'value': 'Frankfurt'},
            {'key': 'text_tx', 'compare': 'like', 'value': 'FooBar not exists'},
        ]
        result_filtered = self.db_handler.select(cherrypy.config['iban'],
                                                condition=query,
                                                multi='OR')
        assert len(result_filtered) == 2, \
            f"Es wurde die falsche Zahl an Datensätzenzurückgegeben: {len(result_filtered)}"
        for entry in result_filtered:
            check_entry(entry)

    def test_update(self):
        """Testet das Aktualisieren von Datensätzen"""
        # Update some records and multiple fields
        data = {'currency': 'USD', 'primary_tag': 'Updated'}
        query = [
            {'key': 'hash', 'value': '13d505688ab3b940dbed47117ffddf95'},
            {'key': 'text_tx', 'value': 'Wucherpfennig', 'compare': 'like'}
        ]
        update_two = self.db_handler.update(data, condition=query, multi='OR')
        assert update_two == 2, \
            f'Es wurde nicht die richtige Anzahl geupdated (update_two): {update_two}'

        result_one = self.db_handler.select(cherrypy.config['iban'], condition=query)
        for entry in result_one:
            check_entry(entry, data)

        # Update all with one field
        data = {'art': 'Überweisung'}
        update_all = self.db_handler.update(data)
        assert update_all == 5, \
            f'Es wurde nicht die richtige Anzahl geupdated (update_all): {update_all}'

        result_all = self.db_handler.select(cherrypy.config['iban'])
        for entry in result_all:
            check_entry(entry, data)

    def test_delete(self):
        """Testet das Löschen von Datensätzen"""
        # Einzelnen Datensatz löschen
        query = {'key': 'hash', 'value': '13d505688ab3b940dbed47117ffddf95'}
        delete_one = self.db_handler.delete(condition=query)
        assert delete_one == 1, \
            f'Es wurde nicht die richtige Anzahl an Datensätzen gelöscht: {delete_one}'

        # Mehrere Datensätze löschen
        query = [
            {'key': 'currency', 'value': 'EUR'},
            {'key': 'currency', 'value': 'USD'}
        ]
        delete_one = self.db_handler.delete(condition=query, multi='OR')
        assert delete_one == 4, \
            f'Es wurde nicht die richtige Anzahl an Datensätzen gelöscht: {delete_one}'


def generate_fake_data(count):
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
        'commerzbank.json'
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
        'hash',
        'date_tx', 'text_tx', 'betrag', 'iban',
        'parsed', 'date_wert', 'art', 'currency',
        'primary_tag', 'secondary_tag'
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
