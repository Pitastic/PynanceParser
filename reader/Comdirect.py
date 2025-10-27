#!/usr/bin/python3 # pylint: disable=invalid-name
"""Reader für das Einlesen von Kontoumsätzen in den Formaten der Comdirect Bank."""

import datetime
import csv
import re
import camelot

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
        rx = re.compile(r'Auftraggeber\:\s(.*)Buchungstext\:\s(.*)')
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
        # Nur Seiten mit den Tabellen analysieren
        tables = camelot.read_pdf(
            filepath,
            pages="2-end",
            flavor="stream",
            strip_text="\n",
            row_tol=10,
            columns=["115,187,305,500"]
        )

        if not tables:
            raise ValueError("No tables found in PDF file.")

        # Tabellen aller Seiten zusammenfügen
        all_rows = []
        for t in tables[:-2]:
            if not t.data:
                continue

            all_rows.extend(t.data)

        # Start bei den Kontoumsätzen
        start_index = 0
        end_index = len(all_rows)
        for row in all_rows:

            if row[0] == 'Alter Saldo':
                # Last row before transactions
                start_index = all_rows.index(row) + 1

        # Ausschnit der Tabelle entnehmen und
        # Zeilen anhand der Datumsspalte zusammenfügen
        # Format:
        # all_rows # Table [ Row1: [ Cell1, Cell2, Cell3 ] , Row2: [ ... ] , ... ]
        result = []
        enumerated_table = enumerate(all_rows[start_index:end_index])
        for i, row in enumerated_table:

            if row[0] == 'BuchungstagValuta':
                continue  # Skip Header Rows

            date_format = "%d.%m.%Y"
            line = {
                'date_tx': datetime.datetime.strptime(
                        row[0][:10], date_format
                    ).replace(tzinfo=datetime.timezone.utc).timestamp(),
                'valuta': datetime.datetime.strptime(
                        row[0][10:], date_format
                    ).replace(tzinfo=datetime.timezone.utc).timestamp(),
                'art': row[1].replace(' ', ''),
                'text_tx': row[3],
                'betrag': float(row[4].replace('.', '').replace(',', '.')),
                'gegenkonto': row[2],
                'currency': "EUR",
                'parsed': {},
                'category': None,
                'tags': None
            }

            while start_index + i + 1 < end_index and \
               all_rows[start_index + i + 1][0] == '' and \
               all_rows[start_index + i + 1][3] != '':
                # 1. There are more lines in the table
                # 2. Next line belongs to this transaction (no new date but text continuation)
                i, row = next(enumerated_table)
                line['text_tx'] += ' ' + row[3]

            result.append(line)

        return result

    def from_http(self, url):
        """
        Liest Kontoumsätze von einer Internetressource ein.
        """
        raise NotImplementedError()
