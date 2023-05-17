#!/usr/bin/python3
"""Datenbankhandler für die Interaktion mit einer SQLite Datenbankdatei."""


import sqlite3


class SQLiteHandler:
    def __init__(self, database):
        """
        Initialisiert eine Instanz von SQLiteHandler und stellt eine Verbindung zur Datenbankdatei her.

        Args:
            database (str): Der Dateipfad zur SQLite-Datenbank.
        """
        self.database = database
        self.connection = None

        try:
            self.connection = sqlite3.connect(self.database)
            self.connection.row_factory = sqlite3.Row
            self.create_schema()
        except sqlite3.Error as e:
            print("Fehler beim Verbindungsaufbau zur Datenbank:", e)

    def create_schema(self):
        try:
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                if len(tables) == 0:
                    #TODO: Ein Datenbankschema erstellen
                    cursor.execute("CREATE TABLE IF NOT EXISTS Cashflow (id INTEGER PRIMARY KEY, name TEXT);")
                    print("Datenbankschema wurde erstellt")
                else:
                    print("Datenbankschema existiert bereits")
        except sqlite3.Error as e:
            print("Fehler beim Erstellen des Datenbankschemas:", e)


    def select(self, table, columns=["*"], condition=None):
        """
        Selektiert Datensätze aus der angegebenen Tabelle basierend auf einer Bedingung.

        Args:
            table (str): Der Name der Tabelle.
            columns (str, optional): Eine Liste von Spaltennamen, die ausgewählt werden sollen. Standardmäßig werden alle Spalten ausgewählt.
            condition (str, optional): Die Bedingung, die die ausgewählten Datensätze einschränkt. Standardmäßig wird nichts eingeschränkt.

        Returns:
            list: Eine Liste von Dictionaries, die die ausgewählten Datensätze repräsentieren. Jedes Dictionary enthält die Spaltennamen als Schlüssel und die zugehörigen Werte.
        """
        try:
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute(f"SELECT {','.join(columns)} FROM {table} WHERE {condition}")
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                return results
        except sqlite3.Error as e:
            print("Fehler beim Auswählen der Datensätze:", e)

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
                placeholders = ", ".join([len(data[0].keys()) * "?"])
                columns = ", ".join(data[0].keys())
                values = [list(item.values()) for item in data]
                cursor.executemany(f"INSERT OR IGNORE INTO {table} ({columns}) VALUES ({placeholders})", values)
                return cursor.rowcount
        except sqlite3.Error as e:
            print("Fehler beim Einfügen der Datensätze:", e)

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
        except sqlite3.Error as e:
            print("Fehler beim Aktualisieren der Datensätze:", e)

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
        except sqlite3.Error as e:
            print("Fehler beim Löschen der Datensätze:", e)
