# PynanceParser

![pytest](https://img.shields.io/badge/pytest-passed%20(51/51)-darkgreen)
![pylint](https://img.shields.io/badge/pylint-9.79-yellow)

Analyse und Darstellung von Kontoumsätzen bei mehreren Banken.

## Features

### Parsing

Importiere Kontoumsätzen aus Dateien im Format unterstützter Banken (Exports von Umsatzübersichten als CSV, Kontoauszüge als PDF).

Modulare Importer können nach und nach für verschiedene Banken oder spezielle Formate entwickelt werden. Füge einen Importer für deine Bank hinzu :wink:

### Analyse

- Automatisches Extrahieren von Zusatzinformationen einer Transaktion durch Muster *(RegEx parst Kerninformationen)*
- Automatisches und/oder manuelles Taggen von Umsätzen *(Regelbasiert: RegEx + Zusatzinformationen)*
- Automatisches und/oder manuelles Kategorisieren von Umsätzen *(Regelbasiert: RegEx + Tags und weitere Indikatoren)*
- Übersicht über alle Transaktionen *(Vielseitige Filtermöglichkeiten)*
- Statistische Auswertung auf dem angereicherten Datensatz vieler Transaktionen *(interaktive Grafiken)*

Hinterlegte Regeln können die extrahierten Informationen, weitere Umsatzinformationen und weitere RegExes berücksichtigen und ermöglichen so komplexe Bewertungen einfach zu erstellen.

Ein Tagging findet anschließend auf angereicherten Informationen regelbasiert statt und kann außerdem auch manuell erfolgen.

Auf dieser Grundlage werden Umsätze Kategorisiert wobei auch das händisch editiert werden kann.

### Darstellung

- Kontohistorie
- Transaktionsansicht
- Statistiken/Verteilungen/Verläufe

Listen und Diagramme zeigen dir, wo eigentlich das Geld geblieben ist :thinking:

## Contribution

You're Welcome !

Erstelle einen Reader für verschiedene Formate deiner Bank oder ergänze die `parser` und `rules`.

## Setup

```
python3.12 -m venv .venv
source .venv/bin/activate
.venv/bin/python3.12 -m ensurepip --upgrade # (optional)
pip install -r requirements.txt
.venv/bin/python3.12 app/server.py
```

### Testumgebung

...zusätzlich zum Setup:

```
pip install -r tests/requirements.txt
pytest
```

## Entwickeln von neuen Readern

- Erstelle einen neuen Test unter `tests/`
    - (kopiere am besten `tests/test_unit_reader_Comdirect.py`)
- Erstelle ein neues Skript unter `reader/`
    - (kopiere am besten `reader/Generic.py`)
- Passe die Logik im Test so an, dass dieser ausgeführt wird, wenn eine Testdatei vorhanden ist.
- Entwickle deinen Reader und teste ihn dabei immer wieder mit `pytest -svx tests/test_unit_reader_*.py`
- Pushe **keine** Testdaten (Kontoumsätze) ins Repo!

## Entwickeln neuer `parser` / `rules`

- Erstelle Testdaten, auf die die neuen Regeln treffen können
    - (am einfachsten ist eine JSON Datei wie `tests/commerzbank.json`)
- Erstelle einen Test wie in (`test_unit_handler_Tags.py`: `test_parsing_regex()`)
    - Tests helfen beim entwickeln, können aber auch durch mich beim Pull Request erstellt werden
