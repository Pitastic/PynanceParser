#!/usr/bin/python3 # pylint: disable=invalid-name
"""Reader für das Einlesen von Kontoumsätzen in dem Format, der Commerzbank."""

from reader.Generic import Reader as Generic


class Reader(Generic):
    """
    Reader um aus übermittelten Daten Kontoführungsinformationen auszulesen.
    Dieser Reader ist speziell für die Daten angepasst, wie sie bei der Commerzbank vorkommen.
    """
    def __init__(self):
        """
        Initialisiert eine Instanz der Reader-Klasse für Kontoumsätze der Commerzbank.
        """
        super().__init__()

    def from_pdf(self, filepath):
        """
        Liest Kontoumsätze von Kontoauszügen ein,
        die im PDF Format von der Commerzbank ausgestellt worden sind.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen
            ausgelesenen Kontoumsätzen entspricht.
        """
        raise NotImplementedError()
