#!/usr/bin/python3 # pylint: disable=invalid-name
"""Routen für das User Interface."""

import os
from datetime import datetime
import secrets
from flask import request, current_app, render_template, redirect, \
                  make_response, send_from_directory, session


class Routes:
    """Klasse zur Registrierung der Routen im Flask App Kontext."""
    def __init__(self, parent):
        """Registriert alle Routen im Flask App Kontext."""
        with current_app.app_context():

            @current_app.template_filter('ctime')
            def timectime(s):
                return datetime.fromtimestamp(s).strftime('%d.%m.%Y')

            @current_app.template_filter('hash')
            def to_hash(string):
                hash_value = 0

                if len(string) == 0:
                    return hash_value

                for char in string:
                    char_code = ord(char)
                    hash_value = ((hash_value << 5) - hash_value) + char_code
                    hash_value = hash_value & 0xFFFFFFFF  # Ensure 32-bit integer

                return hash_value

            @current_app.context_processor
            def version_string():
                return {
                    'version': current_app.config.get('VERSION', 'unknown')
                }

            @current_app.before_request
            def require_login():
                """
                Before Request Handler, der sicherstellt, dass der User eingeloggt ist.
                Falls nicht, wird dieser immer zur Login Seite umeleitet-
                """
                # Allow PyTest Client
                if current_app.config.get('TESTING', False):
                    return

                # Allow access to login route
                if request.endpoint == "login":
                    return

                # Allow access to CSS files
                if request.endpoint == "static" and request.path.endswith(".css"):
                    return

                # Allow access to JS files
                if request.endpoint == "static" and request.path.endswith(".js"):
                    return

                # Block everything else unless logged in
                if not session.get("logged_in"):
                    return redirect('/login')

            @current_app.route("/login", methods=["GET", "POST"])
            def login():
                """
                Login Seite, die ohne gültiges Cookie immer aufgerufen wird.
                Args (form):
                    password, str: Passwort für den Login
                Returns:
                    html: Login Formular
                """
                error = None

                if request.method == "POST":
                    password = request.form.get("password", "")
                    if secrets.compare_digest(password, current_app.config['PASSWORD']):
                        session["logged_in"] = True
                        return redirect('/')

                    error = "Invalid password"

                return render_template('login.html', error=error)

            @current_app.route("/logout")
            def logout():
                """Logout Seite, welche das Cookie löscht und zur Loin Seite weiterleitet."""
                session.clear()
                return redirect('/login')

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
                    iban, str:              IBAN zu der die Einträge angezeigt werden sollen.
                    text, str (query):      Volltextsuche im Betreff mit RegEx Support
                    peer, str (query):      Volltextsuche im Gegenkonto mit RegEx Support
                    startDate, str (query): Startdatum (Y-m-d) für die Anzeige der Einträge
                    endDate, str (query):   Enddatum (Y-m-d) für die Anzeige der Einträge
                    category, str (query):  Kategorie-Filter
                    tag, str (query):       Tag-Filter, einzelner Eintrag oder kommagetrennte Liste
                    tag_mode, str (query):  Vergleichsmodus für Tag-Filter (siehe Models.md)
                    amount_min, float (query):  Betragsfilter (größer gleich amount_min)
                    amount_max, float (query):  Betragsfilter (kleiner gleich amount_max)
                    page, int (query):      Seite für die Paginierung (default: 1)
                    descending, bool (query): Sortierreihenfolge nach Datum (default: True)
                Returns:
                    html: Startseite mit Navigation
                """
                if not parent.check_requested_iban(iban):
                    return "", 404

                # Check filter args
                condition, frontend_filters = parent.filter_to_condition(request.args)

                # Table with Transactions
                current_app.logger.debug(f"Using condition filter: {condition}")
                sort_order = request.args.get('descending', 'true').lower() == 'true'
                rows = parent.db_handler.select(iban, condition, descending=sort_order)

                # If pagination is requested, do not serve the whole page and all metadata
                entries_per_page = 50
                if 'page' in request.args:
                    page = int(request.args.get('page'))
                    start = (page - 1) * entries_per_page
                    end = start + entries_per_page
                    if start >= len(rows):
                        return "", 404  # Return 404 if no more pages can be served
                    return render_template('iban_page.html', transactions=rows[start:end])

                # All distinct Rule Names
                # (must be filtered on our own because TinyDB doesn't support 'distinct' queries)
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

                return render_template('iban.html', transactions=rows[:entries_per_page],
                                       IBAN=iban, tags=tags, categories=cats,
                                       rules=rulenames, filters=frontend_filters)

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
                    amount_min, float (query):  Betragsfilter (größer gleich amount_min)
                    amount_max, float (query):  Betragsfilter (kleiner gleich amount_max)
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
                    amount = row.get('amount', 0.0)
                    cat = row.get('category', 'unkategorisiert')
                    if cat not in sums['categories']:
                        sums['categories'][cat] = 0.0

                    sums['categories'][cat] += amount

                    tags = row.get('tags', [])
                    if not tags:
                        tags = ['untagged']
                    for tag in tags:
                        if tag not in sums['tags']:
                            sums['tags'][tag] = 0.0

                        sums['tags'][tag] += amount

                # Sort Sums
                sums['categories'] = dict(sorted(sums['categories'].items(),
                                            key=lambda item: item[1],
                                            reverse=True))
                sums['tags'] = dict(sorted(sums['tags'].items(),
                                            key=lambda item: item[1],
                                            reverse=True))

                return render_template('stats.html', sums=sums, IBAN=iban,
                                       filters=frontend_filters)

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
                    return {'error': f'Keine Gruppe angelegt: {r.get("error")}'}, 400

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
                    return {'error': f'No data inserted: {r.get("error")}'}, 400

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
                    bank (str, optional): Bankkennung (Default: Generic)
                Returns:
                    json: Informationen zur Datei und Ergebnis der Untersuchung.
                """
                input_file = request.files.get('file-batch')
                if not input_file:
                    return {'error': 'Es wurde keine Datei übermittelt.'}, 400

                # Store Upload file to tmp
                path = f"/tmp/{secrets.token_hex(12)}"
                content_type, size = parent.mv_fileupload(input_file, path)

                # Daten einlesen und in Object speichern (Bank und Format default bzw. wird geraten)
                content_format = {
                    'application/json': 'json',
                    'text/csv': 'csv',
                    'application/pdf': 'pdf',
                    'text/plain': 'text',
                }.get(content_type)

                # Special handling for PDFs (extension needed)
                if content_format == 'pdf':
                    os.rename(path, f'{path}.pdf')
                    path = f'{path}.pdf'

                # Read Input and Parse the contents
                try:
                    parsed_data = parent.read_input(
                        path, bank=request.form.get('bank', 'Generic'),
                        data_format=content_format
                    )

                    # Verarbeitete Kontiumsätze in die DB speichern
                    # und vom Objekt und Dateisystem löschen
                    insert_result = parent.db_handler.insert(parsed_data, iban)
                    inserted = insert_result.get('inserted')

                except (KeyError, ValueError) as ex:
                    return {
                        "error": (
                            "Die hochgeladene Datei konnte nicht verarbeitet werden, "
                            "da das Format unvollständig ist oder nicht erwartet wurde: "
                            + ex.__class__.__name__ + " " + str(ex)
                        )
                    }, 406

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
                print(request.files)
                input_file = request.files.get('settings-input')
                if not input_file:
                    return {'error': 'Es wurde keine Datei übermittelt.'}, 400

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
                    iban, str:  IBAN zu der die Datenbank geleert werden soll.
                                (Default: Primäre IBAN aus der Config)
                Returns:
                    json: Informationen zum Ergebnis des Löschauftrags.
                """
                return parent.db_handler.truncate(iban), 200

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
                        filters=custom_rule.get('filter'),
                        parsed_keys=list(custom_rule.get('parsed', {}).keys()),
                        parsed_vals=list(custom_rule.get('parsed', {}).values()),
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

            @current_app.route('/api/stats/<iban>', methods=['GET'])
            def statsIban(iban):
                """
                Liefert Statistiken zur IBAN zurück.

                Args (uri):
                    iban, str:  IBAN zu der die Statistiken angezeigt werden sollen.
                Returns:
                    json: Statistiken zur IBAN
                        - min_date, str: Datum der ältesten Transaktion
                        - max_date, str: Datum der jüngsten Transaktion
                        - number_tx, int: Anzahl der Transaktionen
                """
                if not parent.check_requested_iban(iban):
                    return "", 404

                stats = parent.db_handler.min_max_collection(iban, 'date_tx')
                return stats, 200
