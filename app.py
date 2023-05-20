#!/usr/bin/python3
"""Zunächst beispielhafter Programmablauf im prozedualen Stil (später Flask?)"""


import sys
import os

from base import BaseClass


# Arg 1 : Dateipfad zu PDF Kontoauszug der Commerzbank


# Basis-Instanz, die die Ablaufmethoden bereitstellt:
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.conf')
Operator = BaseClass(config_path)

# Daten einlesen und in Object speichern (Bank und Format default bzw. wird geraten)
Operator.parse(sys.argv[1])

# Eingelesene Umsätze kategorisieren
Operator.tag()
#print(Operator.data)

# Verarbeitete Kontiumsätze in die DB speichern und vom Objekt löschen
Operator.flush_to_db()
