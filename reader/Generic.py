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
        Das Standard-Objekt, was vom Parsing zurückgegeben wird, 
        folgt dem Template in `Models.md` sofern die Felder mit den Informationen
        von hier sicher gefüllt werden können.
        """
        return

    def from_csv(self, filepath):
        """
        Liest Kontoumsätze aus einer CSV Datei ein. Das Standardformat wird dabei mit einer
        Semikolon-separierten Liste pro Zeile angenommen, die dem Datenbankschema entspricht.
        Abweichungen werden explizit je Bank / Dienst in spezielleren Modulen berücksichtigt.

        Erwartetes Format:
            - Encoding: UTF-8
            - Text eingeschlossen mit ` " `
            - Spalten getrennt mit ` ; `
            - Datumsformate: ` %d.%m.%Y `
            - Erwartete Spalten (Reihenfolge egal, 'Gegenkonto' ist optional):
                - Buchungstag, Valuta, Art, Betrag, Währung, Buchungstext, Gegenkonto

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen ausgelesenen
            Kontoumsätzen.
        """
        result = []
        with open(filepath, 'r', encoding='utf-8') as infile:

            reader = csv.DictReader(infile, delimiter=';')
            date_format = "%d.%m.%Y"

            for row in reader:

                amount = float(row['Betrag'].replace('.', '').replace(',', '.'))
                date_tx = datetime.datetime.strptime(
                            row['Buchungstag'], date_format
                        ).replace(tzinfo=datetime.timezone.utc).timestamp()
                valuta = datetime.datetime.strptime(
                            row['Valuta'], date_format
                        ).replace(tzinfo=datetime.timezone.utc).timestamp()
                line = {
                    'date_tx': date_tx,
                    'valuta': valuta,
                    'art': row['Art'],
                    'text_tx': row['Buchungstext'],
                    'amount': amount,
                    'peer': row.get('Gegenkonto'),
                    'currency': row['Währung'],
                    'parsed': {},
                    'category': None,
                    'tags': None
                }

                if not line['amount']:
                    continue  # Skip Null-Buchungen

                result.append(line)

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
        raise NotImplementedError()
