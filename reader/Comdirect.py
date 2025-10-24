#!/usr/bin/python3 # pylint: disable=invalid-name
"""Reader für das Einlesen von Kontoumsätzen in den Formaten der Comdirect Bank."""

import datetime
import csv
import re

from reader.Generic import Reader as Generic


class Reader(Generic):
    """
    Reader um aus übermittelten Daten Kontoführungsinformationen auszulesen.
    Dieser Reader ist speziell für die Daten angepasst, wie sie bei der Comidrect Bank vorkommen.
    """
    def __init__(self): # pylint: disable=useless-parent-delegation
        """
        Initialisiert eine Instanz der Reader-Klasse für Kontoumsätze der Comdirect Bank.
        """
        #TODO: Es wird ggf. einen Usecase für super.__init__() in Zukunft geben
        super().__init__()

    def from_csv(self, filepath):
        """
        Liest Kontoumsätze von Kontoauszügen ein,
        die im CSV Format von der Comidrect Bank herintergeladen wurden.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen
            ausgelesenen Kontoumsätzen entspricht.
        """
        result = []
        with open(filepath, 'r', encoding='Windows-1252') as infile:

            # Skip the first 4 lines of the file: Standard Comdirect Header
            for _ in range(4):
                next(infile)

            # Start Reading CSV content
            reader = csv.DictReader(infile, delimiter=';')
            date_format = "%d.%m.%Y"
            for row in reader:
                date_tx = row['Buchungstag']
                if date_tx == "offen":
                    # Skippe offene Buchungen
                    continue

                date_tx = datetime.datetime.strptime(
                            date_tx, date_format
                        ).replace(tzinfo=datetime.timezone.utc).timestamp()
                valuta = datetime.datetime.strptime(
                            row['Wertstellung (Valuta)'], date_format
                        ).replace(tzinfo=datetime.timezone.utc).timestamp()
                betrag = float(row['Umsatz in EUR'].replace(',', '.'))
                text_tx = row['Buchungstext']
                rx = re.compile(r'Auftraggeber\:\s(.*)Buchungstext\:\s(.*)')
                match = rx.match(text_tx)

                result.append({
                    'date_tx': date_tx,
                    'valuta': valuta,
                    'art': row['Vorgang'],
                    'text_tx': match.group(2).strip(),
                    'betrag': betrag,
                    'gegenkonto': match.group(1).strip(),
                    'currency': "EUR",
                    'parsed': {},
                    'category': None,
                    'tags': None
                })

        return result

    def from_pdf(self, filepath):
        """
        Liest Kontoumsätze von Kontoauszügen ein,
        die im PDF Format von der Comidrect Bank ausgestellt worden sind.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen
            ausgelesenen Kontoumsätzen entspricht.
        """
        raise NotImplementedError()
