#!/usr/bin/python3
"""Parser für das Einlesen von Kontoumsätzen in dem Format, der Commerzbank."""


from parsers.Generic import Parser as Generic


class Parser(Generic):
    def __init__(self):
        """
        Initialisiert eine Instanz der Parser-Klasse für Kontoumsätze der Commerzbank.
        """
        super().__init__()

    def from_csv(self):
        """
        Liest Kontoumsätze aus einer CSV Datei ein, die aus dem OnlineBanking der Commerzbank stammt.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen ausgelesenen Kontoumsätzen entspricht.
        """
        raise NotImplemented()

    def from_pdf(self):
        """
        Liest Kontoumsätze von Kontoauszügen ein, die im PDF Format von der Commerzbank ausgestellt worden sind.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen ausgelesenen Kontoumsätzen entspricht.
        """
        raise NotImplemented()