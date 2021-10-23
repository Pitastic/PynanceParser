#!/usr/bin/python3
'''Basisklasse für die Vererbung allgemeiner Attribute'''


import sys
import logging
import configparser


class Base():
    def __init__(self, configpath):
        # Logging
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler('pycashflow.log', 'w', 'utf-8')
        handler.setFormatter(
            logging.Formatter('[%(asctime)s] %(levelname)s (%(module)s): %(message)s'))
        self.logger.addHandler(handler)
        # Config
        try:
            self.config = configparser.ConfigParser()
            self.config.read(configpath)
        except Exception as e:
            self.logger.critical("Config Pfad '{}' konnte nicht heladen werden !".format(configpath))
            sys.exit()
