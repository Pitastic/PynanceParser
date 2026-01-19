#!/usr/bin/python3 # pylint: disable=invalid-name
"""Reader für das Einlesen von Kontoumsätzen in einem allgemeinen Format"""

import datetime
import csv
import re


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

    def _parse_from_strftime(self, date_string, date_format):
        """
        Hilfsmethode um ein Datum aus einem String mit einem Format in einen UTC-Timestamp
        umzuwandeln.

        Args:
            date_string (str): Datum als String
            date_format (str): Formatstring wie von `datetime.strptime` verwendet

        Returns:
            int: UTC-Timestamp des übergebenen Datums
        """
        try:
            return datetime.datetime.strptime(
                date_string, date_format
            ).replace(tzinfo=datetime.timezone.utc).timestamp()

        except ValueError as e:
            if "day is out of range for month" in str(e):
                # Handle invalid dates like 31.11.2023 -> 30.11.2023
                split_char = re.search(r'[^\d]', date_string)
                if not split_char:
                    raise e  # No valid split character found

                # Replace just the day part
                split_char = split_char.group(0)
                day_index = date_format.split(split_char).index('%d')
                if day_index == -1:
                    raise e  # No day part found in format

                date_string_list = date_string.split(split_char)
                date_string_list[day_index] = int(date_string_list[day_index]) - 1
                date_string = split_char.join(map(str, date_string_list))

                return self._parse_from_strftime(
                    date_string, date_format
                )

            raise e  # Re-raise other ValueErrors
