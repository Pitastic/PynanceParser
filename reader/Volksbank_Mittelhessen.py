#!/usr/bin/python3 # pylint: disable=invalid-name
"""Reader für das Einlesen von Kontoumsätzen in den Formaten der Volksbank Mittelhessen."""

import datetime
import csv
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
            strip_text='\n', # übernommen von Commerzbank, da ähnliches Layout
            layout_kwargs={ # übernommen von Commerzbank, da ähnliches Layout
                "char_margin": 2,
                "word_margin": 0.5,
            },
        )
        # Begin at: "alter Kontostand vom"
        # End at: "neuer Kontostand vom"
 
    def from_http(self, url):
        """
        Liest Kontoumsätze von einer Internetressource ein.
        """
        raise NotImplementedError()

    def _newline_replace(self, text_in:str) -> str:
        """Ersetzt Newlines im Buchungsinformationen
        intelligent durch Leerzeichen oder nichts
        Args:
            text_in, str:   Input Text aus Kontoauszug
        Return:
            str: Text ohne Newlines
        """
        if not '\n' in text_in:
            return text_in

        if text_in.index('\n') < 35:
            return text_in.replace('\n', ' ')

        return text_in.replace('\n', '')
