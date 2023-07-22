#!/usr/bin/python3 # pylint: disable=invalid-name
"""Reader für das Einlesen von Kontoumsätzen in einem allgemeinen Format"""

import datetime
import csv


class Reader:
    """
    Reader um aus übermittelten Daten Kontoführungsinformationen auszulesen.
    Dieser Reader ist allgemein und nicht speziell auf das Format einer Bank angepasst.
    """
    def __init__(self):
        """
        Initialisiert eine Instanz von Generic-Reader.
        Das Standard-Objekt, was vom Parsing zurückgegeben wird, sollte so aussehen:
        dict({
            'date_tx': int,         # (UTC)
            'text_tx': str,
            'betrag': float,
            'iban': str,
            'parsed': str,
            'primary_tag': str,
            'secondary_tag': str
            'date_wert': int ,      # (optional, UTC)
            'art': str,             # (optional)
            'currency': str,        # (optional)
        })
        """
        return

    def from_csv(self, filepath):
        """
        Liest Kontoumsätze aus einer CSV Datei ein. Das Standardformat wird dabei mit einer
        Semikolon-separierten Liste pro Zeile angenommen, die dem Datenbankschema entspricht.
        Abweichungen werden explizit je Bank / Dienst in spezielleren Modulen berücksichtigt.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen ausgelesenen
            Kontoumsätzen entspricht.
        """
        result = []
        with open(filepath, 'r', encoding='utf-8-sig') as infile:

            reader = csv.DictReader(infile, delimiter=';')
            date_format = "%d.%m.%Y"

            for row in reader:
                betrag = float(row['Betrag'].replace(',', '.'))
                date_tx = datetime.datetime.strptime(
                            row['Buchungstag'], date_format
                        ).replace(tzinfo=datetime.timezone.utc).timestamp()
                date_wert = datetime.datetime.strptime(
                            row['Wertstellung'], date_format
                        ).replace(tzinfo=datetime.timezone.utc).timestamp()
                result.append({
                    'date_tx': date_tx,
                    'date_wert': date_wert,
                    'art': row['Umsatzart'],
                    'text_tx': row['Buchungstext'],
                    'betrag': betrag,
                    'iban': row['IBAN Auftraggeberkonto'],
                    'currency': row['Währung'],
                    'parsed': {}
                })

        return result

    def from_pdf(self, filepath):
        """
        Liest Kontoumsätze von Kontoauszügen im PDF Format ein.
        Das Standardformat wird dem der CSV Datei bei .from_csv angenommmen.
        Abweichungen werden explizit je Bank / Dienst in spezielleren Modulen berücksichtigt.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen
            ausgelesenen Kontoumsätzen entspricht.
        """
        # Import specific Libraries
        #import ...
        raise NotImplementedError()

    def from_http(self, url):
        """
        Liest Kontoumsätze von einer Internetressource ein.
        Das Standardformat wird dem der CSV Datei bei .from_csv angenommmen.
        Abweichungen werden explizit je Bank / Dienst in spezielleren Modulen berücksichtigt.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen
            ausgelesenen Kontoumsätzen entspricht.
        """
        # Import specific Libraries
        #import requests
        raise NotImplementedError()
