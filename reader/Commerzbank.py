#!/usr/bin/python3 # pylint: disable=invalid-name
"""Reader für das Einlesen von Kontoumsätzen in dem Format, der Commerzbank."""

import datetime
import csv
import camelot

from reader.Generic import Reader as Generic


class Reader(Generic):
    """
    Reader um aus übermittelten Daten Kontoführungsinformationen auszulesen.
    Dieser Reader ist speziell für die Daten angepasst, wie sie bei der Commerzbank vorkommen.
    """

    def from_csv(self, filepath):
        """
        Liest Kontoumsätze von Kontoauszügen ein,
        die im CSV Format von der Commerzbank herintergeladen wurden.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen ausgelesenen
            Kontoumsätzen.
        """
        result = []
        with open(filepath, 'r', encoding='utf-8-sig') as infile:

            reader = csv.DictReader(infile, delimiter=';')
            date_format = "%d.%m.%Y"

            for row in reader:

                betrag = float(row['Betrag'].replace('.', '').replace(',', '.'))
                date_tx = datetime.datetime.strptime(
                            row['Buchungstag'], date_format
                        ).replace(tzinfo=datetime.timezone.utc).timestamp()
                valuta = datetime.datetime.strptime(
                            row['Wertstellung'], date_format
                        ).replace(tzinfo=datetime.timezone.utc).timestamp()
                line = {
                    'date_tx': date_tx,
                    'valuta': valuta,
                    'art': row['Umsatzart'],
                    'text_tx': row['Buchungstext'],
                    'betrag': betrag,
                    'pper': row.get('Auftraggeber', row.get('IBAN Auftraggeberkonto')),
                    'currency': row['Währung'],
                    'parsed': {},
                    'category': None,
                    'tags': None
                }

                if not line['betrag']:
                    continue  # Skip Null-Buchungen

                result.append(line)

        return result

    def from_pdf(self, filepath):
        """
        Liest Kontoumsätze von Kontoauszügen ein,
        die im PDF Format von der Commerzbank ausgestellt worden sind.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen
            ausgelesenen Kontoumsätzen entspricht.
        """
        tables = camelot.read_pdf(
            filepath,
            pages='all',
            flavor='stream',
            strip_text='\n',
            columns=["296,335,454"],
            table_areas=["60,567,573,51"],
            layout_kwargs={
                "char_margin": 2,
                "word_margin": 0.5,
            },
        )

        # Tabellen aller Seiten zusammenfügen
        self.all_rows = []
        for t in tables:
            if not t.data:
                continue

            self.all_rows.extend(t.data)

        # Start bei den Kontoumsätzen
        start_index = 0
        end_index = len(self.all_rows)
        for row in self.all_rows:

            if row[0].replace(' ', '').lower().startswith('angabenzudenumsätzen'):
                # Last row before transactions
                start_index = self.all_rows.index(row) + 1

            if 'Kreditlinie' in row[0]:
                # First row after transactions
                end_index = self.all_rows.index(row)
                break

        result = []
        date_tx = 0
        date_tx_year = "1970"  # Default Year if not found yet
        enumerated_table = enumerate(self.all_rows[start_index:end_index])
        for i, row in enumerated_table:

            if row[0].startswith('Buchungsdatum: '):
                # All following rows have this 'date_tx'
                date_tx_year = row[0][-4:]
                date_tx = datetime.datetime.strptime(
                    row[0][-10:], "%d.%m.%Y"
                ).replace(tzinfo=datetime.timezone.utc).timestamp()
                continue  # Skip Header Rows

            # negativer Betrag in Spalte "Lasten" oder positiv "zu Gunsten"
            betrag = f"-{row[2][:-1]}" if row[2] else row[3]

            line = {
                'date_tx': date_tx,
                'valuta': datetime.datetime.strptime(
                        f"{row[1]}.{date_tx_year}", "%d.%m.%Y"
                    ).replace(tzinfo=datetime.timezone.utc).timestamp(),
                'art': "",
                'text_tx':  row[0],
                'betrag': float(betrag.replace('.', '').replace(',', '.')),
                'pper': row[0],
                'currency': "EUR",
                'parsed': {},
                'category': None,
                'tags': None
            }

            while self._check_next_line_available(start_index, end_index, i):
                # 1. There are more lines in the table
                # 2. Next line belongs to this transaction
                # (no new date but text continuation - last line in this block is 'art')
                prev_line_len = len(row[0])
                i, row = next(enumerated_table)

                line['art'] = row[0] # Overwrite to keep value of last line in block

                if self._check_next_line_available(start_index, end_index, i):
                    # Line overflow or intentional line break?
                    glue = ' ' if prev_line_len < 35 else ''
                    line['text_tx'] += glue + row[0]

            if not line['betrag']:
                continue  # Skip Null-Buchungen

            result.append(line)

        return result

    def from_http(self, url):
        raise NotImplementedError("from_http is not implemented yet for Commerzbank Reader")

    def _check_next_line_available(self, start_index, end_index, i):
        """
        Hilfsmethode um zu prüfen, ob die nächste Zeile im
        ausgelesenen PDF-Dokument noch verfügbar ist.

        Args:
            start_index (int): Startindex der Kontoumsätze
            end_index (int): Endindex der Kontoumsätze
            i (int): Aktueller Index in der Iteration
        Returns:
            bool: True, wenn die nächste Zeile noch verfügbar ist, sonst False
        """
        if start_index + i + 1 >= end_index:
            return False

        if self.all_rows[start_index + i + 1][1] != '':
            return False

        if self.all_rows[start_index + i + 1][0].startswith('Buchungsdatum: '):
            return False

        return True
