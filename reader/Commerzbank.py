#!/usr/bin/python3 # pylint: disable=invalid-name
"""Reader für das Einlesen von Kontoumsätzen in dem Format, der Commerzbank."""

import re
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
            '/tmp/commerzbank.pdf',
            pages='all',
            flavor='stream',
            strip_text='\n',
            columns=["335,573"],
            table_areas=["60,567,573,51"]
        )
        #TODO: Start bei "Buchungsdatum"
        #TODO: Ende bei "Kreditlinie"
        #TODO: Trenner zwischen den Einträgen in Spalte Valuta (wenn leer == zum vorherigen)
        #TODO: Buchungsdatum auf alle Einträge die auf diese Überschrift folgen anwenden
        raise NotImplementedError()
