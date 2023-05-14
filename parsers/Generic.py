#!/usr/bin/python3
"""Parser für das Einlesen von Kontoumsätzen in einem allgemeinen Format"""

class Parser:
    def __init__(self):
        """
        Initialisiert eine Instanz von Generic-Parser.
        """
        raise NotImplemented()

    def prepare(self, uri):
        """
        Bereitet die Ressource für das Parsing vor und testet ihre Lesbarkeit und Erreichbarkeit.
        
        Args:
            uri (str): Der Pfad zur Ressource, der Kontoumsätze für das Einlesen enthält.
        """
        raise NotImplemented()

    def from_csv(self):
        """
        Liest Kontoumsätze aus einer CSV Datei ein. Das Standardformat wird dabei mit einer Semikolon-separierten Liste pro Zeile angenommen, die dem Datenbankschema entspricht.
        Abweichungen werden explizit je Bank / Dienst in spezielleren Modulen berücksichtigt.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen ausgelesenen Kontoumsätzen entspricht.
        """
        raise NotImplemented()

    def from_pdf(self):
        """
        Liest Kontoumsätze von Kontoauszügen im PDF Format ein. Das Standardformat wird dem der CSV Datei bei .from_csv angenommmen.
        Abweichungen werden explizit je Bank / Dienst in spezielleren Modulen berücksichtigt.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen ausgelesenen Kontoumsätzen entspricht.
        """
        raise NotImplemented()

    def from_http(self):
        """
        Liest Kontoumsätze von einer Internetressource ein. Das Standardformat wird dem der CSV Datei bei .from_csv angenommmen.
        Abweichungen werden explizit je Bank / Dienst in spezielleren Modulen berücksichtigt.

        Returns:
            Liste mit Dictonaries, als Standard-Objekt mit allen ausgelesenen Kontoumsätzen entspricht.
        """
        raise NotImplemented()
