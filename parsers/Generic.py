#!/usr/bin/python3
"""Parser für das Einlesen von Kontoumsätzen in einem allgemeinen Format"""

import datetime


class Parser:
    def __init__(self):
        """
        Initialisiert eine Instanz von Generic-Parser.
        Das Standard-Objekt, was vom Parsing zurückgegeben wird, sollte so aussehen:
        dict({
            'date_buchung': date,
            'text': str,
            'betrag': float,
            'iban': str,
            'date_wert': date,      # (optional)
            'art': str              # (optional)
            'currency': str         # (optional)
        })
        """
        pass

    def from_csv(self, filepath):
        """
        Liest Kontoumsätze aus einer CSV Datei ein. Das Standardformat wird dabei mit einer Semikolon-separierten Liste pro Zeile angenommen, die dem Datenbankschema entspricht.
        Abweichungen werden explizit je Bank / Dienst in spezielleren Modulen berücksichtigt.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen ausgelesenen Kontoumsätzen entspricht.
        """
        # Import specific Libraries
        import csv

        result = []
        with open(filepath, 'r') as infile:

            reader = csv.DictReader(infile, delimiter=';')
            date_format = "%d.%m.%Y"

            for row in reader:
                betrag = float(row['Betrag'].replace(',', '.'))
                result.append({
                    'date_buchung': datetime.datetime.strptime(
                        row['Buchungstag'], date_format
                    ).date(),
                    'date_wert': datetime.datetime.strptime(
                        row['Wertstellung'], date_format
                    ).date(),
                    'art': row['Umsatzart'],
                    'text': row['Buchungstext'],
                    'betrag': betrag,
                    'iban': row['IBAN Auftraggeberkonto'],
                    'currency': row['Währung']
                })

        return result

    def from_pdf(self, filepath):
        """
        Liest Kontoumsätze von Kontoauszügen im PDF Format ein. Das Standardformat wird dem der CSV Datei bei .from_csv angenommmen.
        Abweichungen werden explizit je Bank / Dienst in spezielleren Modulen berücksichtigt.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen ausgelesenen Kontoumsätzen entspricht.
        """
        # Import specific Libraries
        #import ...
        raise NotImplemented()

    def from_http(self, url):
        """
        Liest Kontoumsätze von einer Internetressource ein. Das Standardformat wird dem der CSV Datei bei .from_csv angenommmen.
        Abweichungen werden explizit je Bank / Dienst in spezielleren Modulen berücksichtigt.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen ausgelesenen Kontoumsätzen entspricht.
        """
        # Import specific Libraries
        #import requests
        raise NotImplemented()
