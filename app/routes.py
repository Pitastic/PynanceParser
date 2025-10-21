#!/usr/bin/python3 # pylint: disable=invalid-name
"""Routen für das User Interface."""

import os
from datetime import datetime
from flask import request, current_app, render_template, redirect, \
                  make_response, send_from_directory


class Routes:
    """Klasse zur Registrierung der Routen im Flask App Kontext."""
    def __init__(self, parent):
        """Registriert alle Routen im Flask App Kontext."""
        with current_app.app_context():

            @current_app.template_filter('ctime')
            def timectime(s):
                return datetime.fromtimestamp(s).strftime('%d.%m.%Y')

            @current_app.route('/', methods=['GET'])
            def welcome() -> str:
                """
                Startseite mit Navigation und Uploadformular.
                Returns:
                    html: Startseite mit Navigation und Uploadformular
                """
                ibans = parent.db_handler.list_ibans()
                groups = parent.db_handler.list_groups()
                meta = parent.db_handler.filter_metadata(condition=None)
                return render_template('index.html', ibans=ibans, groups=groups, meta=meta)

            @current_app.route('/<iban>', methods=['GET'])
            def iban(iban) -> str:
                """
                Startseite in einem Konto.

                Args (uri):
                    iban, str:  IBAN zu der die Einträge angezeigt werden sollen.
                    startDate, str (query): Startdatum (Y-m-d) für die Anzeige der Einträge
                    endDate, str (query):   Enddatum (Y-m-d) für die Anzeige der Einträge
                    category, str (query):  Kategorie-Filter
                    tag, str (query):       Tag-Filter, einzelner Eintrag oder kommagetrennte Liste
                    tag_mode, str (query):  Vergleichsmodus für Tag-Filter (siehe Models.md)
                    betrag, float (query):  Betragsfilter
                    betrag_mode, str (query): Vergleichsmodus für Betragsfilter (siehe Models.md)
                Returns:
                    html: Startseite mit Navigation
                """
                if not parent.check_requested_iban(iban):
                    return "", 404

                # Check filter args
                condition, frontend_filters = parent.filter_to_condition(request.args)

                # Table with Transactions
                current_app.logger.debug(f"Using condition filter: {condition}")
                rows = parent.db_handler.select(iban, condition)
                rulenames = parent.db_handler.filter_metadata({'key':'metatype', 'value': 'rule'})
                rulenames = [r.get('name') for r in rulenames if r.get('name')]

                # All distinct Tags
                # (must be filtered on our own because TinyDB doesn't support 'distinct' queries)
                tags = []
                tag_query = {'key': 'tags', 'value': [], 'compare': '!='}
                for row in parent.db_handler.select(iban, condition=tag_query):
                    for t in row.get('tags', []):
                        if t not in tags:
                            tags.append(t)

                # All distinct Categories
                # (must be filtered on our own because TinyDB doesn't support 'distinct' queries)
                cats = []
                cat_query = {'key': 'category', 'value': None, 'compare': '!='}
                for row in parent.db_handler.select(iban, condition=cat_query):
                    c = row.get('category')
                    if c and c not in cats:
                        cats.append(c)

                return render_template('iban.html', transactions=rows, IBAN=iban,
                                       rules=rulenames, tags=tags, categories=cats,
                                       filters=frontend_filters)

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
                tx_details = parent.db_handler.select(
                    iban, {
                        'key': 'uuid',
                        'value': t_id,
                        'compare': '=='
                    }
                )
                if not tx_details:
                    return {'error': 'No transaction found'}, 404

                # All distinct Tags
                # (must be filtered on our own because TinyDB doesn't support 'distinct' queries)
                tags = []
                tag_query = {'key': 'tags', 'value': [], 'compare': '!='}
                for row in parent.db_handler.select(iban, condition=tag_query):
                    for t in row.get('tags', []):
                        if t not in tags:
                            tags.append(t)

                # All distinct Categories
                # (must be filtered on our own because TinyDB doesn't support 'distinct' queries)
                cats = []
                cat_query = {'key': 'category', 'value': None, 'compare': '!='}
                for row in parent.db_handler.select(iban, condition=cat_query):
                    c = row.get('category')
                    if c and c not in cats:
                        cats.append(c)

                return render_template('tx.html', tx=tx_details[0], cats=cats, tags=tags)

            @current_app.route('/<iban>/stats', methods=['GET'])
            def show_stats(iban) -> str:
                """
                Zeigt Statistiken zur aktuellen IBAN an.

                Args (uri):
                    iban, str:  IBAN zu der die Statistiken angezeigt werden sollen.
                    startDate, str (query): Startdatum (Y-m-d) für die Anzeige der Einträge
                    endDate, str (query):   Enddatum (Y-m-d) für die Anzeige der Einträge
                    category, str (query):  Kategorie-Filter
                    tag, str (query):       Tag-Filter, einzelner Eintrag oder kommagetrennte Liste
                    tag_mode, str (query):  Vergleichsmodus für Tag-Filter (siehe Models.md)
                    betrag, float (query):  Betragsfilter
                    betrag_mode, str (query): Vergleichsmodus für Betragsfilter (siehe Models.md)
                Returns:
                    html: Seite mit Grafiken und Statistiken über die slektierten Einträge
                    (IBAN und optional Query)
                """
                if not parent.check_requested_iban(iban):
                    return "", 404

                # Check filter args
                condition, frontend_filters = parent.filter_to_condition(request.args)
                # Table with Transactions
                current_app.logger.debug(f"Using condition filter: {condition}")
                rows = parent.db_handler.select(iban, condition)

                # Calculate TOP categories and tags
                sums = {'categories': {}, 'tags': {}}
                for row in rows:
                    betrag = row.get('betrag', 0.0)
                    cat = row.get('category', 'unkategorisiert')
                    if cat not in sums['categories']:
                        sums['categories'][cat] = 0.0

                    sums['categories'][cat] += betrag

                    tags = row.get('tags', [])
                    if not tags:
                        tags = ['untagged']
                    for tag in tags:
                        if tag not in sums['tags']:
                            sums['tags'][tag] = 0.0

                        sums['tags'][tag] += betrag

                # Sort Sums
                sums['categories'] = dict(sorted(sums['categories'].items(),
                                            key=lambda item: item[1],
                                            reverse=True))
                sums['tags'] = dict(sorted(sums['tags'].items(),
                                            key=lambda item: item[1],
                                            reverse=True))

                return render_template('stats.html', sums=sums, IBAN=iban,
                                       filters=frontend_filters)

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
                r = parent.db_handler.add_iban_group(groupname, ibans)
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
                tx_details = parent.db_handler.select(
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
                r = parent.db_handler.set_metadata(entry, overwrite=True)

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
                        meta = parent.db_handler.filter_metadata({
                            'key': 'metatype',
                            'value': rule_filter})
                        return meta, 200

                    # Select specific Meta ID
                    meta = parent.db_handler.get_metadata(rule_filter)
                    return meta, 200

                # Select all Meta
                meta = parent.db_handler.filter_metadata(condition=None)
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
                content_type, size = parent.mv_fileupload(input_file, path)

                # Daten einlesen und in Object speichern (Bank und Format default bzw. wird geraten)
                content_formats = {
                    'application/json': 'json',
                    'text/csv': 'csv',
                    'application/pdf': 'pdf',
                    'text/plain': 'text',
                }

                # Read Input and Parse the contents
                parsed_data = parent.read_input(
                    path, data_format=content_formats.get(content_type)
                )

                # Verarbeitete Kontiumsätze in die DB speichern
                # und vom Objekt und Dateisystem löschen
                insert_result = parent.db_handler.insert(parsed_data, iban)
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
                _ = parent.mv_fileupload(input_file, path)

                # Import and cleanup
                result = parent.db_handler.import_metadata(path, metatype=metadata)
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
                deleted_entries = parent.db_handler.truncate(iban)
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
                return parent.tagger.tag(iban, rule_name, dry_run)

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
                return parent.tagger.categorize(iban, rule_name, prio, prio_set, dry_run)

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
                `Tagger.tag_and_cat_custom()` wenn Rulename == "ui_selected_custom" ist
            
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
                data = request.json
                if data.get('rule_name', "") == "ui_selected_custom":
                    # Custom Rule defined
                    custom_rule = data.get('rule', {})
                    return parent.tagger.tag_or_cat_custom(
                        iban,
                        category=custom_rule.get('category'),
                        tags=custom_rule.get('tags'),
                        filters=custom_rule.get('filters'),
                        parsed_keys=custom_rule.get('parsed_keys'),
                        parsed_vals=custom_rule.get('parsed_vals'),
                        multi=custom_rule.get('multi', 'AND'),
                        prio=custom_rule.get('prio', 1),
                        prio_set=custom_rule.get('prio_set'),
                        dry_run=data.get('dry_run', False)
                    )

                # Preset Rule defined or Default (if all None)
                return parent.tagger.tag_and_cat(
                    iban,
                    rule_name=data.get('rule_name'),
                    category_name=data.get('category_name'),
                    dry_run=data.get('dry_run', False)
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
                        - overwrite, bool: Wenn True, werden die bestehenden Tags überschrieben.
                Returns:
                    dict: updated, int: Anzahl der gespeicherten Datensätzen
                """
                data = request.json
                tags = data.get('tags')
                assert tags is not None, 'No tags provided'
                overwrite = data.get('overwrite', False)
                return parent.set_manual_tag_and_cat(iban, t_id, tags=tags, overwrite=overwrite)

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
                return parent.set_manual_tag_and_cat(iban, t_id, category=category)

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

                    updated = parent.set_manual_tag_and_cat(iban, tx, category=category)
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
                        - overwrite, bool: Wenn True, werden die bestehenden Tags überschrieben.
                Returns:
                    dict: updated, int: Anzahl der gespeicherten Datensätzen
                """
                updated_entries = {'updated': 0}
                data = request.json
                tags = data.get('tags')
                t_ids = data.get('t_ids')
                assert tags and t_ids, 'No tags or transactions provided'
                overwrite = data.get('overwrite', False)
                for tx in t_ids:

                    updated = parent.set_manual_tag_and_cat(
                        iban, tx, tags=tags, overwrite=overwrite
                    )
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
                return parent.remove_tags(iban, t_id)

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
                return parent.remove_cat(iban, t_id)

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

                    updated = parent.remove_tags(iban, t_id)
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

                    updated = parent.remove_cat(iban, t_id)
                    updated_entries['updated'] += updated.get('updated')

                return updated_entries
