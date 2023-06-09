#!/usr/bin/python3 # pylint: disable=invalid-name
"""Parser für das Einlesen von Kontoumsätzen in dem Format, der Commerzbank."""


from parsers.Generic import Parser as Generic


class Parser(Generic):
    """
    Parser um aus übermittelten Daten Kontoführungsinformationen auszulesen.
    Dieser Parser ist speziell für die Daten angepasst, wie sie bei der Commerzbank vorkommen.
    """
    def __init__(self):
        """
        Initialisiert eine Instanz der Parser-Klasse für Kontoumsätze der Commerzbank.
        """
        super().__init__()
        return

    def from_pdf(self, filepath):
        """
        Liest Kontoumsätze von Kontoauszügen ein,
        die im PDF Format von der Commerzbank ausgestellt worden sind.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen
            ausgelesenen Kontoumsätzen entspricht.
        """
        raise NotImplementedError()
