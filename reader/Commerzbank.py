#!/usr/bin/python3 # pylint: disable=invalid-name
"""Reader für das Einlesen von Kontoumsätzen in dem Format, der Commerzbank."""

import datetime
import camelot

from reader.Generic import Reader as Generic


class Reader(Generic):
    """
    Reader um aus übermittelten Daten Kontoführungsinformationen auszulesen.
    Dieser Reader ist speziell für die Daten angepasst, wie sie bei der Commerzbank vorkommen.
    """
    def __init__(self): # pylint: disable=useless-parent-delegation
        """
        Initialisiert eine Instanz der Reader-Klasse für Kontoumsätze der Commerzbank.
        """
        #TODO: Es wird ggf. einen Usecase für super.__init__() in Zukunft geben
        super().__init__()

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
        all_rows = []
        for t in tables:
            if not t.data:
                continue

            all_rows.extend(t.data)

        # Start bei den Kontoumsätzen
        start_index = 0
        end_index = len(all_rows)
        for row in all_rows:

            if row[0].replace(' ', '').lower().startswith('angabenzudenumsätzen'):
                # Last row before transactions
                start_index = all_rows.index(row) + 1

            if 'Kreditlinie' in row[0]:
                # First row after transactions
                end_index = all_rows.index(row)
                break

        result = []
        date_tx = 0
        date_tx_year = "1970"  # Default Year if not found yet
        enumerated_table = enumerate(all_rows[start_index:end_index])
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
                'text_tx': row[0],
                'betrag': float(betrag.replace('.', '').replace(',', '.')),
                'gegenkonto': row[0],
                'currency': "EUR",
                'parsed': {},
                'category': None,
                'tags': None
            }

            while start_index + i + 1 < end_index and \
               all_rows[start_index + i + 1][1] == '' and \
               not all_rows[start_index + i + 1][0].startswith('Buchungsdatum: '):
                # 1. There are more lines in the table
                # 2. Next line belongs to this transaction
                # (no new date but text continuation - last line in this block is 'art')
                i, row = next(enumerated_table)

                line['text_tx'] += ' ' + row[0]
                line['art'] = row[0] # Overwrite to keep value of last line in block

            result.append(line)

        return result

    def from_http(self, url):
        raise NotImplementedError("from_http is not implemented yet for Commerzbank Reader")
