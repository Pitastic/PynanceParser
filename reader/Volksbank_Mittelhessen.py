#!/usr/bin/python3 # pylint: disable=invalid-name
"""Reader für das Einlesen von Kontoumsätzen in den Formaten der Volksbank Mittelhessen."""

import datetime
import csv
import re
import camelot

from reader.Generic import Reader as Generic


class Reader(Generic):
    """
    Reader um aus übermittelten Daten Kontoführungsinformationen auszulesen.
    Dieser Reader ist speziell für die Daten angepasst, wie sie bei der
    Volksbank Mittelhessen vorkommen.
    """

    def from_csv(self, filepath):
        """
        Liest Kontoumsätze von Kontoauszügen ein,
        die im CSV Format von der Volksbank Mittelhessen herintergeladen wurden.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen
            ausgelesenen Kontoumsätzen.
        """
        result = []
        with open(filepath, 'r', encoding='utf-8') as infile:

            # Start Reading CSV content
            reader = csv.DictReader(infile, delimiter=';')
            date_format = "%d.%m.%Y"
            for row in reader:
                date_tx = row['Buchungstag']
                if date_tx == "offen" or not row['Betrag']:
                    # Skippe offene Buchungen / Hinweise
                    continue

                betrag = float(row['Betrag'].replace(',', '.'))
                date_tx = datetime.datetime.strptime(
                            date_tx, date_format
                        ).replace(tzinfo=datetime.timezone.utc).timestamp()
                valuta = datetime.datetime.strptime(
                            row['Valutadatum'], date_format
                        ).replace(tzinfo=datetime.timezone.utc).timestamp()

                line = {
                    'date_tx': date_tx,
                    'valuta': valuta,
                    'art': row['Buchungstext'],
                    'text_tx': row['Verwendungszweck'],
                    'betrag': betrag,
                    'gegenkonto': row['Name Zahlungsbeteiligter'],
                    'currency': row['Waehrung'],
                    'parsed': {},
                    'category': None,
                    'tags': None
                }

                if row.get('Glaeubiger ID'):
                    line['parsed']['Gläubiger-ID'] = row['Glaeubiger ID']

                if row.get('Mandatsreferenz'):
                    line['parsed']['Mandatsreferenz'] = row['Mandatsreferenz']

                result.append(line)

        return result

    def from_pdf(self, filepath):
        """
        Liest Kontoumsätze von Kontoauszügen ein,
        die im PDF Format von der Volksbank Mittelhessen ausgestellt worden sind.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen
            ausgelesenen Kontoumsätzen entspricht.
        """
        tables = camelot.read_pdf(
            filepath,
            pages="all", # End -1
            flavor="stream",
            table_areas=["60,629,573,51"],
            columns=["75,112,440,526"],
            split_text=True,
            #layout_kwargs={ # übernommen von Commerzbank, da ähnliches Layout
            #    "char_margin": 2,
            #    "word_margin": 0.5,
            #},
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
        date_tx_year = None
        for row in self.all_rows:

            if row[2].replace(' ', '').lower().startswith('alterkontostand'):
                # Last row before transactions
                start_index = self.all_rows.index(row) + 1
                date_tx_year = row[2][-4:]  # Jahr für die Transaktionen merken

            if row[2].replace(' ', '').lower().startswith('neuerkontostand'):
                # First row after transactions + final line
                end_index = self.all_rows.index(row) - 1
                break

        if date_tx_year is None or re.match(r'^\d{4}$', date_tx_year) is None:
            raise ValueError("Konnte Jahr der Transaktionen nicht ermitteln.")

        result = []
        enumerated_table = enumerate(self.all_rows[start_index:end_index])

        # Zeilen anhand der Datumsspalte zusammenfügen
        re_datecheck = re.compile(r'^\d{2}\.\d{2}')

        for i, row in enumerated_table:

            if not re_datecheck.match(row[0]) and not re_datecheck.match(row[1]):
                continue  # Skip Header and unvalid Rows

            # Positives 'Haben' oder negatives 'Soll'
            betrag = f'-{row[3]}' if row[3] else row[4]
            betrag = betrag[:-2].replace('.', '').replace(',', '.')

            line = {
                'date_tx': datetime.datetime.strptime(
                    f"{row[0]}{date_tx_year}", "%d.%m.%Y"
                ).replace(tzinfo=datetime.timezone.utc).timestamp(),
                'valuta': datetime.datetime.strptime(
                    f"{row[1]}{date_tx_year}", "%d.%m.%Y"
                ).replace(tzinfo=datetime.timezone.utc).timestamp(),
                'art': row[2],
                'text_tx': "",
                'betrag': float(betrag),
                'gegenkonto': "",
                'currency': "EUR",
                'parsed': {},
                'category': None,
                'tags': None
            }

            if not line['betrag']:
                continue  # Skip Null-Buchungen

            # Mehrzeilige Buchungstexte zusammenfügen
            while self._check_next_line_available(start_index, end_index, i):
                # 1. There are more lines in the table
                # 2. Next line belongs to this transaction
                # 3. First next line is: Gegenkonto
                prev_line_len = len(row[3])
                i, row = next(enumerated_table)
                if not line['text_tx']:
                    line['gegenkonto'] = row[2]
                    line['text_tx'] = row[2]
                    continue

                line['text_tx'] += self._how_to_glue(prev_line_len, row[2])

            result.append(line)

        return result

    def from_http(self, url):
        """
        Liest Kontoumsätze von einer Internetressource ein.
        """
        raise NotImplementedError()

    def _how_to_glue(self, prev_line_len, text_tx):
        """Stellt ein oder kein Leerzeichen an das Ende
        der Zeichenkette, um die nächste Zeile passend entgegenzunehmen."""
        if prev_line_len < 54:
            return ' ' + text_tx

        return text_tx

    def _check_next_line_available(self, start_index, end_index, i):
        """
        Hilfsmethode um zu prüfen, ob die nächste Zeile im
        ausgelesenen PDF-Dokument noch verfügbar ist und zur selben Buchung gehört.

        Args:
            start_index (int): Startindex der Kontoumsätze
            end_index (int): Endindex der Kontoumsätze
            i (int): Aktueller Index in der Iteration
        Returns:
            bool: True, wenn die nächste Zeile noch verfügbar ist, sonst False
        """
        next_lines_index = start_index + i + 1
        if next_lines_index >= end_index:
            return False

        if self.all_rows[next_lines_index][2] == '':
            return False

        if self.all_rows[next_lines_index][0] != '' or \
           self.all_rows[next_lines_index][1] != '':
            return False

        return True
