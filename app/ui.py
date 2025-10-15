#!/usr/bin/python3 # pylint: disable=invalid-name
"""Routen und Funktionen für das User Interface."""

import sys
import os
import json
import logging
from datetime import datetime
from flask import request, current_app, render_template, redirect, \
                  make_response, send_from_directory

# Add Parent for importing Classes
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from handler.TinyDb import TinyDbHandler
from handler.MongoDb import MongoDbHandler
from handler.Tags import Tagger

from reader.Generic import Reader as Generic
from reader.Commerzbank import Reader as Commerzbank


class UserInterface():
    """Basisklasse mit Methoden für den Programmablauf"""

    def __init__(self):
        """
        Initialisiert eine Instanz der Basisklasse und lädt die Konfiguration sowie die Logunktion.
        """
        # Datenbankhandler
        if current_app.config['DATABASE_BACKEND'] == 'tiny':
            self.db_handler = TinyDbHandler()

        elif current_app.config['DATABASE_BACKEND'] == 'mongo':
            self.db_handler = MongoDbHandler()

        else:
            raise NotImplementedError(("The configure database engine ",
                                     f"{current_app.config['DATABASE_BACKEND']} ",
                                      "is not supported !"))
        assert self.db_handler, \
            (f"DbHandler {current_app.config['DATABASE_BACKEND']} Klasse konnte nicht ",
             "instanziiert werden")

        # Reader
        self.readers = {
            'Generic': Generic,
            'Commerzbank': Commerzbank,
        }

        # Tagger
        self.tagger = Tagger(self.db_handler)

        # Weitere Attribute
        self.reader = None

        #TODO: Usermanagement, #7
        # Jeder User soll seine eigene Collection haben.
        # Die Collection beinhaltet Dokumente als Settings, Regeln
        # oder Transaktionen zu verschiedenen Konten des Benutzers.
        # Im Init und/oder als Decorator jeder Funktion muss der User
        # aus der Session ermittelt werden. Fallback ist der in der Config
        # hinterlegte Deafult-User, sofern Authentification noch nicht
        # implementiert ist.

        # Define Routes
        with current_app.app_context():

            @current_app.route('/', methods=['GET'])
            def welcome() -> str:
                """
                Startseite mit Navigation und Uploadformular.
                Returns:
                    html: Startseite mit Navigation und Uploadformular
                """
                ibans = self.db_handler.list_ibans()
                groups = self.db_handler.list_groups()
                meta = self.db_handler.filter_metadata(condition=None)
                return render_template('index.html', ibans=ibans, groups=groups, meta=meta)

            @current_app.route('/<iban>', methods=['GET'])
            def iban(iban) -> str:
                """
                Startseite in einem Konto.

                Args (uri):
                    iban, str:  IBAN zu der die Einträge angezeigt werden sollen.
                    startDate, str (query): Startdatum (Y-m-d) für die Anzeige der Einträge
                    endDate, str (query):   Enddatum (Y-m-d) für die Anzeige der Einträge
                Returns:
                    html: Startseite mit Navigation
                """
                if iban is None:
                    # No IBAN provided, redirect to welcome
                    redirect('/')

                if not self.db_handler.get_group_ibans(iban, True):
                    # It's not an IBAN or valid Groupname
                    return "", 404

                # Check filter args
                condition = []

                start_date = request.args.get('startDate')
                if start_date is not None:
                    # Convert to valid date format
                    try:
                        start_date = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
                        condition.append({
                            'key': 'date_tx',
                            'value': start_date,
                            'compare': '>='
                        })

                    except (ValueError, TypeError) as e:
                        logging.warning(f"Invalid startDate format '{e}' will be ignored")

                end_date = request.args.get('endDate')
                if end_date is not None:
                    # Convert to valid date format
                    try:
                        end_date = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
                        condition.append({
                            'key': 'date_tx',
                            'value': end_date,
                            'compare': '<='
                        })

                    except (ValueError, TypeError) as e:
                        logging.warning(f"Invalid endDate format '{e}' will be ignored")

                # Table with Transactions and other Meta Data
                rows = self.db_handler.select(iban, condition)
                rulenames = self.db_handler.filter_metadata({'key':'metatype', 'value': 'rule'})
                rulenames = [r.get('name') for r in rulenames if r.get('name')]
                cats = self.db_handler.filter_metadata({'key':'metatype', 'value': 'category'})
                cats = [r.get('category') for r in cats if r.get('category')]
                return render_template('iban.html', transactions=rows, iban=iban,
                                       rules=rulenames, categories=cats)

            @current_app.route('/<iban>/<t_id>', methods=['GET'])
            def showTx(iban, t_id):
                """
                Ansicht einer einzelnen Transaktion.
                Args (uri):
                    iban, str: IBAN
                    t_id, int: Datenbank ID der Transaktion
                Returns:
                    json: Details zu einer bestimmten Transaktion
                """
                tx_details = self.db_handler.select(
                    iban, {
                        'key': 'uuid',
                        'value': t_id,
                        'compare': '=='
                    }
                )
                if not tx_details:
                    return {'error': 'No transaction found'}, 404

                return render_template('tx.html', tx=tx_details[0])

            @current_app.route('/logout', methods=['GET'])
            def logout():
                """
                Loggt den User aus der Session aus und leitet zur Startseite weiter.

                Returns:
                    redirect: Weiterleitung zur Startseite
                """
                return redirect('/')

            @current_app.route('/sw.js')
            def sw():
                response = make_response(
                    send_from_directory(
                        os.path.join('app', 'static'), path='sw.js'
                    )
                )
                response.headers['Content-Type'] = 'application/javascript'
                return response

            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            # - API Endpoints - - - - - - - - - - - - - - - - - - - -
            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -

            @current_app.route('/api/addgroup/<groupname>', methods=['PUT'])
            def addGroup(groupname):
                """
                Erstellt eine Gruppe mit zugeordneten IBANs.
                Args (uri / json):
                    groupname, str: Name der Gruppe
                    ibans, list[str]: Liste mit IBANs, die der Gruppe zugeordnet werden sollen
                Returns:
                    json: Informationen zur neu angelegten Gruppe
                """
                #TODO: User muss Rechte an allen IBANs der neuen Gruppe haben (related #7)
                data = request.json
                ibans = data.get('ibans')
                assert ibans is not None, 'No IBANs provided'
                r = self.db_handler.add_iban_group(groupname, ibans)
                if not r.get('inserted'):
                    return {'error': 'No Group added', 'reason': r.get('error')}, 400

                return r, 201

            @current_app.route('/api/<iban>/<t_id>', methods=['GET'])
            def getTx(iban, t_id):
                """
                Gibt alle Details zu einer bestimmten Transaktion zurück.
                Args (uri):
                    iban, str: IBAN
                    t_id, int: Datenbank ID der Transaktion
                Returns:
                    json: Details zu einer bestimmten Transaktion
                """
                tx_details = self.db_handler.select(
                    iban, {
                        'key': 'uuid',
                        'value': t_id,
                        'compare': '=='
                    }
                )
                if not tx_details:
                    return {'error': 'No transaction found'}, 404

                return tx_details[0], 200

            @current_app.route('/api/saveMeta/', defaults={'rule_type':'rule'}, methods=['POST'])
            @current_app.route('/api/saveMeta/<rule_type>', methods=['PUT'])
            def saveMeta(rule_type):
                """
                Einfügen oder updaten von Metadaten in der Datenbank.
                Args (json / file):
                    rule_type, str: Typ der Regel (rule | parser | config)
                    rule, dict: Regel-Objekt
                """
                if not request.json:
                    return {'error': 'No file or json provided'}, 400

                entry = request.json
                entry['metatype'] = rule_type
                r = self.db_handler.set_metadata(entry, overwrite=True)

                if not r.get('inserted'):
                    return {'error': 'No data inserted', 'reason': r.get('error')}, 400

                return r, 201

            @current_app.route('/api/getMeta/', methods=['GET'], defaults={'rule_filter':None})
            @current_app.route('/api/getMeta/<rule_filter>', methods=['GET'])
            def getMeta(rule_filter):
                """
                Auflisten von Metadaten (optional gefilter)
                Args (json):
                    rule_filter, str: Typ der Regel (rule | parser | config) oder ID
                """
                if rule_filter is not None:

                    if rule_filter in ['rule', 'parser', 'config']:
                        # Select specific Meta Type
                        meta = self.db_handler.filter_metadata({
                            'key': 'metatype',
                            'value': rule_filter})
                        return meta, 200

                    # Select specific Meta ID
                    meta = self.db_handler.get_metadata(rule_filter)
                    return meta, 200

                # Select all Meta
                meta = self.db_handler.filter_metadata(condition=None)
                return meta, 200

            @current_app.route('/api/upload/<iban>', methods=['POST'])
            def uploadIban(iban):
                """
                Endpunkt für das Annehmen hochgeladener Kontoumsatzdateien.
                Im Anschluss wird automatisch die Untersuchung der Inhalte angestoßen.

                Args (multipart/form-data):
                    file-input (binary): Dateiupload aus Formular-Submit
                Returns:
                    json: Informationen zur Datei und Ergebnis der Untersuchung.
                """
                input_file = request.files.get('file-input')
                if not input_file:
                    return {'error': 'No file provided'}, 400

                # Store Upload file to tmp
                path = '/tmp/transactions.tmp'
                content_type, size = self._mv_fileupload(input_file, path)

                # Daten einlesen und in Object speichern (Bank und Format default bzw. wird geraten)
                content_formats = {
                    'application/json': 'json',
                    'text/csv': 'csv',
                    'application/pdf': 'pdf',
                    'text/plain': 'text',
                }

                # Read Input and Parse the contents
                parsed_data = self._read_input(
                    path, data_format=content_formats.get(content_type)
                )

                # Verarbeitete Kontiumsätze in die DB speichern
                # und vom Objekt und Dateisystem löschen
                insert_result = self.db_handler.insert(parsed_data, iban)
                inserted = insert_result.get('inserted')
                os.remove(path)

                return_code = 201 if inserted else 200
                return {
                    'size': size,
                    'filename': input_file.filename,
                    'content_type': content_type,
                    'inserted': inserted,
                }, return_code

            @current_app.route('/api/upload/metadata/<metadata>', methods=['POST'])
            def uploadRules(metadata):
                """
                Endpunkt für das Annehmen hochgeladener Tagging- und Parsingregeln..

                Args (uri, multipart/form-data):
                    metadata (str): [regex|parser|config] Type of Metadata to save
                    file-input (binary): Dateiupload aus Formular-Submit
                Returns:
                    json: Informationen zur Datei und Ergebnis der Untersuchung.
                """
                input_file = request.files.get('file-input')
                if not input_file:
                    return {'error': 'No file provided'}, 400

                # Store Upload file to tmp
                path = f'/tmp/{metadata}.tmp'
                _ = self._mv_fileupload(input_file, path)
                
                # Import and cleanup
                result = self.db_handler.import_metadata(path, metatype=metadata)
                os.remove(path)
                return result, 201 if result.get('inserted') else 200

            @current_app.route('/api/deleteDatabase/<iban>', methods=['DELETE'])
            def deleteDatabase(iban):
                """
                Leert die Datenbank zu einer IBAN
                Args (uri):
                    iban, str:  (optional) IBAN zu der die Datenbank geleert werden soll.
                                (Default: Primäre IBAN aus der Config)
                Returns:
                    json: Informationen zum Ergebnis des Löschauftrags.
                """
                deleted_entries = self.db_handler.truncate(iban)
                return {'deleted': deleted_entries}, 200

            @current_app.route('/api/tag/<iban>', methods=['PUT'])
            def tag(iban) -> dict:
                """
                Tagged die Kontoumsätze und aktualisiert die Daten in der Instanz.
                Die Argumente werden nach Prüfung an die Tagger-Klasse weitergegeben.

                Args (json) - siehe Tagger.tag():
                    rule_name, str: Name der Regel, die angewendet werden soll.
                                    (Default: Alle Regeln werden angewendet)
                    dry_run, bool:  Switch to show, which TX would be updated. Do not update.
                Returns:
                    json: Informationen zum Ergebnis des Taggings.
                """
                rule_name = request.json.get('rule_name')
                dry_run = request.json.get('dry_run', False)
                return self.tagger.tag(iban, rule_name, dry_run)

            @current_app.route('/api/cat/<iban>', methods=['PUT'])
            def cat(iban) -> dict:
                """
                Kategorisiert die Kontoumsätze und aktualisiert die Daten in der Instanz.
                Die Argumente werden nach Prüfung an die Tagger-Klasse weitergegeben.

                Args (json) - siehe Tagger.categorize():
                    rule_name, str: Name der Regel, die angewendet werden soll.
                                    (Default: Alle Regeln werden angewendet)
                    dry_run, bool:  Switch to show, which TX would be updated. Do not update.
                    prio, int:      Override ruleset value of priority for this categorization run
                                    in comparison with already cat. transactions
                                    (higher = more important)
                    prio_set, int:  Override: Compare with 'prio' but set this value instead.
                Returns:
                    json: Informationen zum Ergebnis des Taggings.
                """
                rule_name = request.json.get('rule_name')
                dry_run = request.json.get('dry_run', False)
                prio = request.json.get('prio')
                prio_set = request.json.get('prio_set')
                return self.tagger.categorize(iban, rule_name, prio, prio_set, dry_run)

            @current_app.route('/api/tag-and-cat/<iban>', methods=['PUT'])
            def tag_and_cat(iban) -> dict:
                """
                Tagged und/oder Kategorisiert die Kontoumsätze und aktualisiert die
                Daten in der Instanz. Je nach übergebenen Argumenten erfolgt dies
                automatisch anhand der Regeln in der Datenbank oder
                anhand einer übergebenen Regel.
                
                Nutzt die Methoden:
                 `Tagger.tag_and_cat()` mit presets
                 `Tagger.tag_and_cat()` mit angegebenen Regelnamen, wenn
                                        `rule_name` oder `category_name` gesetzt ist
                `Tagger.tag_and_cat_custom()` wenn mindestens ein Kriterium gesetzt ist von
                                        `category`, `tags`, `filters`, `parsed_keys`, `parsed_vals`
            
                Args (json):
                    rule_name:      UUID der anzuwendenden Taggingregel.
                                    Reserviertes Keyword 'ai' führt nur das AI Tagging aus.
                    category_name:  UUID der anzuwendenden Kategorisierungsregel.
                    category:       Name der zu setzenden Primärkategory.
                    tags:           Liste der zu setzenden Tags.
                    filters:        Liste mit Regelsätzen (dict)
                    parsed_keys:    Liste mit Keys zur Prüfung in geparsten Daten.
                    parsed_vals:    Liste mit Values zur Prüfung in geparsten Daten.
                    multi:          Logische Verknüpfung der Kriterien (AND|OR).
                    prio:           Value of priority for this tagging run
                                    in comparison with already tagged transactions
                                    This value will be set as the new priority in DB.
                                    (higher = important)
                    prio_set:       Compare with 'prio' but set this value instead.
                    dry_run:        Switch to show, which TX would be updated. Do not update.
                Returns:
                    json: Informationen zum Ergebnis des Taggings.
                """
                if any(k in request.json for k in (
                    'category', 'tags', 'filters','parsed_keys', 'parsed_vals'
                )):
                    # Custom Rule defined
                    return self.tagger.tag_or_cat_custom(
                        iban,
                        category=request.json.get('category'),
                        tags=request.json.get('tags'),
                        filters=request.json.get('filters'),
                        parsed_keys=request.json.get('parsed_keys'),
                        parsed_vals=request.json.get('parsed_vals'),
                        multi=request.json.get('multi', 'AND'),
                        prio=request.json.get('prio', 1),
                        prio_set=request.json.get('prio_set'),
                        dry_run=request.json.get('dry_run', False)
                    )

                # Preset Rule defined or Default (if all None)
                return self.tagger.tag_and_cat(
                    iban,
                    rule_name=request.json.get('rule_name'),
                    category_name=request.json.get('category_name'),
                    dry_run=request.json.get('dry_run', False)
                )

            @current_app.route('/api/setManualTag/<iban>/<t_id>', methods=['PUT'])
            def setManualTag(iban, t_id):
                """
                Handler für _set_manual_tag() für einzelne Einträge.

                Args (uri/json):
                    iban, str: IBAN
                    t_id, str: Datenbank ID der Transaktion, die getaggt werden soll
                    data, dict: Daten für die Aktualisierung
                        - tags, list[str]: Bezeichnung der zu setzenden Tags
                Returns:
                    dict: updated, int: Anzahl der gespeicherten Datensätzen
                """
                data = request.json
                tags = data.get('tags')
                assert tags is not None, 'No tags provided'
                return self._set_manual_tag_and_cat(iban, t_id, tags=tags)

            @current_app.route('/api/setManualCat/<iban>/<t_id>', methods=['PUT'])
            def setManualCat(iban, t_id):
                """
                Handler für _set_manual_tag() für einzelne Einträge.

                Args (uri/json):
                    iban, str: IBAN
                    t_id, str: Datenbank ID der Transaktion, die getaggt werden soll
                    data, dict: Daten für die Aktualisierung
                        - category, str: Bezeichnung der zu setzenden Kategorie
                Returns:
                    dict: updated, int: Anzahl der gespeicherten Datensätzen
                """
                data = request.json
                category = data.get('category')
                assert category is not None, 'No category provided'
                return self._set_manual_tag_and_cat(iban, t_id, category=category)

            @current_app.route('/api/setManualCats/<iban>', methods=['PUT'])
            def setManualCats(iban):
                """
                Handler für _set_manual_tag() für mehrere Einträge.

                Args (uri/json):
                    iban, str: IBAN
                    data, dict: Daten für die Aktualisierung
                        - t_ids, list[str]: Liste mit Datenbank IDs der Transaktionen,
                                            die getaggt werden sollen
                        - category, str: Bezeichnung der zu setzenden Kategorie
                Returns:
                    dict: updated, int: Anzahl der gespeicherten Datensätzen
                """
                updated_entries = {'updated': 0}
                data = request.json
                category = data.get('category')
                t_ids = data.get('t_ids')
                assert category and t_ids, 'No category or transactions provided'
                for tx in t_ids:

                    updated = self._set_manual_tag_and_cat(iban, tx, category=category)
                    updated_entries['updated'] += updated.get('updated')

                return updated_entries

            @current_app.route('/api/setManualTags/<iban>', methods=['PUT'])
            def setManualTags(iban):
                """
                Handler für _set_manual_tag() für mehrere Einträge.

                Args (uri/json):
                    iban, str: IBAN
                    data, dict: Daten für die Aktualisierung
                        - t_ids, list[str]: Liste mit Datenbank IDs der Transaktionen,
                                            die getaggt werden sollen
                        - tags, list[str]: Bezeichnung der zu setzenden Tags
                Returns:
                    dict: updated, int: Anzahl der gespeicherten Datensätzen
                """
                updated_entries = {'updated': 0}
                data = request.json
                tags = data.get('tags')
                t_ids = data.get('t_ids')
                assert tags and t_ids, 'No tags or transactions provided'
                for tx in t_ids:

                    updated = self._set_manual_tag_and_cat(iban, tx, tags=tags)
                    updated_entries['updated'] += updated.get('updated')

                return updated_entries

            @current_app.route('/api/removeTag/<iban>/<t_id>', methods=['PUT'])
            def removeTag(iban, t_id):
                """
                Entfernt gesetzte Tags für einen Eintrag-

                Args (uri/json):
                    iban, str: IBAN
                    t_id, str: Datenbank ID der Transaktion,
                               die bereinigt werden soll.
                Returns:
                    dict: updated, int: Anzahl der gespeicherten Datensätzen
                """
                return self._remove_tags(iban, t_id)

            @current_app.route('/api/removeCat/<iban>/<t_id>', methods=['PUT'])
            def removeCat(iban, t_id):
                """
                Entfernt gesetzte Tags für einen Eintrag-

                Args (uri/json):
                    iban, str: IBAN
                    t_id, str: Datenbank ID der Transaktion,
                               die bereinigt werden soll.
                Returns:
                    dict: updated, int: Anzahl der gespeicherten Datensätzen
                """
                return self._remove_cat(iban, t_id)

            @current_app.route('/api/removeTags/<iban>', methods=['PUT'])
            def removeTags(iban):
                """
                Entfernt gesetzte Tags für mehrere Einträge.

                Args (uri/json):
                    iban, str: IBAN
                    t_ids, list[str]: Datenbank IDs der Transaktionen,
                                      die bereinigt werden sollen.
                Returns:
                    dict: updated, int: Anzahl der gespeicherten Datensätzen
                """
                data = request.json
                t_ids = data.get('t_ids')
                assert t_ids, 'No transactions provided'

                updated_entries = {'updated': 0}
                for t_id in t_ids:

                    updated = self._remove_tags(iban, t_id)
                    updated_entries['updated'] += updated.get('updated')

                return updated_entries

            @current_app.route('/api/removeCats/<iban>', methods=['PUT'])
            def removeCats(iban):
                """
                Entfernt gesetzte Tags für einen Eintrag-

                Args (uri/json):
                    iban, str: IBAN
                    t_ids, list[str]: Datenbank IDs der Transaktionen,
                                      die bereinigt werden sollen.
                Returns:
                    dict: updated, int: Anzahl der gespeicherten Datensätzen
                """
                data = request.json
                t_ids = data.get('t_ids')
                assert t_ids, 'No transactions provided'

                updated_entries = {'updated': 0}
                for t_id in t_ids:

                    updated = self._remove_cat(iban, t_id)
                    updated_entries['updated'] += updated.get('updated')

                return updated_entries

    def _set_manual_tag_and_cat(self, iban, t_id,
                                tags: list=None, category: str=None) -> dict:
        """
        Setzt manuell eine Kategorie und/oder Tags für einen bestimmten Eintrag.

        Args:
            iban, str: IBAN
            t_id, int: Datenbank ID der Transaktion, die getaggt werden soll
            tags, list[str]: Bezeichnung der zu setzenden Tags
            category, str: Bezeichnung der zu setzenden Kategorie
        Returns:
            dict: updated, int: Anzahl der gespeicherten Datensätzen
        """
        assert tags or category, 'No tags or category provided'
        new_tag_data = {}

        if tags is not None:
            if not isinstance(tags, list):
                tags = [tags]

            new_tag_data['tags'] = tags

        if category is not None:
            new_tag_data['category'] = category
            new_tag_data['prio'] = 99  # Manuell gesetzte Tags haben immer hohe Prio

        condition = {
            'key': 'uuid',
            'value': t_id,
            'compare': '=='
        }

        updated_entries = self.db_handler.update(new_tag_data, iban, condition)
        return updated_entries

    def _remove_tags(self, iban, t_id):
        """
        Entfernt ein gesetztes Tag für einen Eintrag.

        Args:
            iban, str: IBAN
            t_id, str: Datenbank ID der Transaktion,
                       die bereinigt werden soll.
        Returns:
            dict: updated, int: Anzahl der gespeicherten Datensätzen
        """
        new_data = {
            'tags': []
        }
        condition = [{
            'key': 'uuid',
            'value': t_id,
            'compare': '=='
        }]

        updated_entries = self.db_handler.update(new_data, iban, condition)
        return updated_entries

    def _remove_cat(self, iban, t_id):
        """
        Entfernt eine Kategorie von einen Eintrag.

        Args:
            iban, str: IBAN
            t_id, str: Datenbank ID der Transaktion,
                       die bereinigt werden soll.
        Returns:
            dict: updated, int: Anzahl der gespeicherten Datensätzen
        """
        new_data = {
            'prio': 0,
            'category': None,
        }
        condition = [{
            'key': 'uuid',
            'value': t_id,
            'compare': '=='
        }]

        updated_entries = self.db_handler.update(new_data, iban, condition)
        return updated_entries

    def _mv_fileupload(self, input_file, path):
        """
        Verschiebt die hochgeladene Datei in ein temporäres Verzeichnis.

        Args:
            input_file (binary): Dateiupload aus Formular-Submit
            path (str): Pfad zur temporären Datei
        Returns:
            str: Content-Type der Datei
        """
        content_type = input_file.content_type
        size = 0
        with open(path, 'wb') as f:

            while True:
                data = input_file.read(8192)

                if not data:
                    break

                size += len(data)
                f.write(data)

        return content_type, size

    def _read_input(self, uri, bank='Generic', data_format=None):
        """
        Liest Kontoumsätze aus der Ressource ein. Wenn das Format nicht angegeben ist,
        wird es versucht zu erraten. Speichert dann eine Liste mit Dictonaries,
        als Standard-Objekt mit den Kontoumsätzen in der Instanz.

        Args:
            uri (str): Pfad zur Ressource mit den Kontoumsätzen.
            bank (str): Bezeichnung der Bank bzw. des einzusetzenden Readers.
            format (str, optional): Bezeichnung des Ressourcenformats (http, csv, pdf).
        Returns:
            list(dict): Geparste und getaggte Kontoumsätze
        """
        # Format
        if data_format is None:
            #TODO: Logik zum Erraten des Datentyps, #10
            data_format = 'csv'

        # Reader
        self.reader = self.readers.get(
            bank, self.readers.get('Generic')
        )()

        parsing_method = {
            'pdf': self.reader.from_pdf,
            'csv': self.reader.from_csv,
            'http': self.reader.from_http
        }.get(data_format)

        data = parsing_method(uri)
        if data is None:
            return []

        return self.tagger.parse(data)
