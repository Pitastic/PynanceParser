#!/usr/bin/python3 # pylint: disable=invalid-name
"""Datenbankhandler für die Interaktion mit einer SQLite Datenbankdatei."""


import sqlite3


class SQLiteHandler:
    """
    Handler für die Interaktion mit einer SQLite Datenbank.
    """
    def __init__(self, config, logger):
        """
        Initialisiert eine Instanz von SQLiteHandler und
        stellt eine Verbindung zur Datenbankdatei her.

        Args:
            database (str): Der Dateipfad zur SQLite-Datenbank.
        """
        self.config = config
        self.logger = logger
        self.database = self.config['DB']['path']
        self.connection = None

        try:
            self.connection = sqlite3.connect(self.database)
            self.connection.row_factory = sqlite3.Row
            self.create_schema(self.config['DEFAULT']['iban'])
        except sqlite3.Error as ex:
            self.logger.error(f"Fehler beim Verbindungsaufbau zur Datenbank: {ex}")

    def create_schema(self, iban):
        """
        Erstellt ein Schema für die Datenbank eines bestimmten Kontos (IBAN).

        Args:
            IBAN, str: IBAN vom Konto des Benutzers
        """
        try:
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                if len(tables) == 0:
                    cursor.execute(f"""CREATE TABLE IF NOT EXISTS
                        {iban} (
                            id INTEGER PRIMARY KEY,
                            hash TEXT UNIQUE,
                            date_tx INTEGER NOT NULL,
                            text_tx TEXT NOT NULL,
                            betrag REAL NOT NULL,
                            iban TEXT NOT NULL,
                            date_wert INTEGER,
                            art TEXT,
                            currency TEXT NOT NULL DEFAULT 'EUR',
                            primary_tag TEXT,
                            secondary_tag TEXT
                        );""")
                    self.logger.info(f"Datenbankschema für {iban} wurde erstellt")
                else:
                    self.logger.info(f"Datenbankschema für {iban} existiert bereits")
        except sqlite3.Error as ex:
            self.logger.error(f"Fehler beim Erstellen des Datenbankschemas für {iban}: {ex}")


    def select(self, table, columns=None, condition=None):
        """
        Selektiert Datensätze aus der angegebenen Tabelle basierend auf einer Bedingung.

        Args:
            table (str): Der Name der Tabelle.
            columns (str, optional): Eine Liste von Spaltennamen, die ausgewählt werden sollen.
                                     Standardmäßig werden alle Spalten ausgewählt.
            condition (str, optional): Die Bedingung, die die ausgewählten Datensätze einschränkt.
                                       Standardmäßig wird nichts eingeschränkt.

        Returns:
            list: Eine Liste von Dictionaries, die die ausgewählten Datensätze repräsentieren.
            Jedes Dictionary enthält die Spaltennamen als Schlüssel und die zugehörigen Werte.
        """
        if columns is None:
            columns = ["*"]
        try:
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute(f"SELECT {','.join(columns)} FROM {table} WHERE {condition}")
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                return results
        except sqlite3.Error as ex:
            self.logger.error(f"Fehler beim Auswählen der Datensätze: {ex}")

    def insert(self, table, data):
        """
        Fügt einen oder mehrere Datensätze (des gleichen Schemas) in die angegebene Tabelle ein.

        Args:
            table (str): Der Name der Tabelle.
            data (list): Eine Liste von Dictionaries, mit den einzufügenden Datensätzen.

        Returns:
            int: Die Anzahl der eingefügten Datensätze.
        """
        try:
            with self.connection:
                cursor = self.connection.cursor()
                placeholders = ", ".join(["?"] * len(data[0].keys()))
                columns = ", ".join(data[0].keys())
                values = [list(item.values()) for item in data]
                sql_string = f"""INSERT OR IGNORE INTO
                    {table} ({columns})
                    VALUES ({placeholders})"""
                cursor.executemany(sql_string, values)
                return cursor.rowcount
        except sqlite3.Error as ex:
            self.logger.error(f"Fehler beim Einfügen der Datensätze: {ex}")

    def update(self, table, data, condition):
        """
        Aktualisiert Datensätze in der angegebenen Tabelle basierend auf einer Bedingung.

        Args:
            table (str): Der Name der Tabelle.
            data (dict): Ein Dictionary, das die zu aktualisierenden Spalten und Werte enthält.
            condition (str): Die Bedingung, die die zu aktualisierenden Datensätze einschränkt.

        Returns:
            int: Die Anzahl der aktualisierten Datensätze.
        """
        try:
            with self.connection:
                cursor = self.connection.cursor()
                placeholders = ", ".join([f"{column} = ?" for column in data.keys()])
                values = list(data.values())
                cursor.execute(f"UPDATE {table} SET {placeholders} WHERE {condition}", values)
                return cursor.rowcount
        except sqlite3.Error as ex:
            self.logger.error(f"Fehler beim Aktualisieren der Datensätze: {ex}")

    def delete(self, table, condition):
        """
        Löscht Datensätze aus der angegebenen Tabelle basierend auf einer Bedingung.

        Args:
            table (str): Der Name der Tabelle.
            condition (str): Die Bedingung, die die zu löschenden Datensätze einschränkt.

        Returns:
            int: Die Anzahl der gelöschten Datensätze.
        """
        try:
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute(f"DELETE FROM {table} WHERE {condition}")
                return cursor.rowcount
        except sqlite3.Error as ex:
            self.logger.error(f"Fehler beim Löschen der Datensätze: {ex}")
