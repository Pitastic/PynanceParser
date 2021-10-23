#!/usr/bin/python3
'''Modul für die Datenbankinteraktion'''


import sqlite3
import os


class DbInterface():
    def __init__(self):
        if os.path.isfile(self.config['DB']['path']):
            self.logger.info("Datenbank wird neu initialisiert...")
            self.initDB()

    def initDB(self):
        self.logger.critical('NotImplemented: db(initDB)')
        pass

    def select(self, query):
        self.logger.critical('NotImplemented: db(select)')
        pass

    def insert(self, bank, data):
        #TODO: Nur Umsätze speichern, die noch nicht in der DB sind (über einen Hash?)
        self.logger.critical('NotImplemented: db(insert)')
        pass

    def update(self, query):
        self.logger.critical('NotImplemented: db(update)')
        pass

    def delete(self, query):
        self.logger.critical('NotImplemented: db(delete)')
        pass
