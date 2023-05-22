#!/usr/bin/python3
"""Zunächst beispielhafter Programmablauf im prozedualen Stil (später Flask?)"""


import sys
from handler.MainHandler import MainHandler


# Arg 1 : Dateipfad zu PDF Kontoauszug der Commerzbank


# Basis-Instanz, die die Ablaufmethoden bereitstellt:
Operator = MainHandler()

# Daten einlesen und in Object speichern (Bank und Format default bzw. wird geraten)
Operator.read_input(sys.argv[1])
Operator.parse()

# Eingelesene Umsätze kategorisieren
Operator.tag()

# Verarbeitete Kontiumsätze in die DB speichern und vom Objekt löschen
Operator.flush_to_db()

# Manuelle Durchsicht der erstellten Datenbankdatei
