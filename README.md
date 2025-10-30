# PynanceParser

![pytest](https://img.shields.io/badge/pytest-passed%20(51/51)-darkgreen)
![pylint](https://img.shields.io/badge/pylint-9.78-yellow)

Analyse und Darstellung von Kontoumsätzen bei mehreren Banken.

## Features

### Parsing

Importiere Kontoumsätzen aus Dateien im Format unterstützter Banken (Exports von Umsatzübersichten als CSV, Kontoauszüge als PDF). Für Auswertung der Ausgaben von Zeit zu Zeit.

Modulare Importer können nach und nach für verschiedene Banken oder spezielle Formate entwickelt werden. Füge einen Importer für deine Bank hinzu :wink:

### Analyse

- Keine doppelten Imports *(Datum, Text und Betrag bilden eine einmalige Kombination)*
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

## Misc

### Unterstützte Banken

| Bank                         | CSV | PDF |
|------------------------------|-------------------------------------|
| Comdirect                    | 🟢 Umsatzübersicht | 🟢 Finanzreport |
| Commerzbank                  | 🟢 Umsatzübersicht | 🟢 Kontoauszug |
| Sparkasse Hannover           | ⚫ *planned* | ⚫ *planned* |
| Volksbank Mittelhessen eG    | 🟢 Umsatzübersicht | ⚫ *planned* |

### Workflow (CSV / PDF Imports)

Umsätze können sich beim Import überschneiden oder mehrfach hochgeladen werden: Transaktionen werden in der Regel nicht doppelt importiert.

Die Umsatzinformationen eines Kontoauszugs als PDF und der Export der Ansicht im Online Banking als CSV hat schon bei der Erstellung einen unterschiedlichen Informationsgehalt. Hinzu kommt, dass das Einlesen einer PDF nicht so verlässlich bei Zeilenumbrüchen und Leerzeichen funktioniert, weshalb Worte getrennt oder zusammengeschoben werden können. Ein und die selbe Transaktion kann daher unterschiedlich beschrieben worden sein, was einen doppelten Import (einer je Format) leider möglich macht.

Daher sollte man beachten:

- Regeln nicht auf zwingend vorhandene Leerzeichen auszulegen
- Beim Wechsel eines Formats (PDF / CSV) keine Überschneidungen zu haben (PDF zuerst, dann fehlende Transaktionen selektieren und via CSV exportieren - alternativ bei einem Format bleiben)

### Tagging- und Kategorisierungsregeln

In diesem Repository werden nur Basis-Regeln mitgeliefert, da speziellere und genauere Regeln sehr individuell auf einzelne Personen zugeschnitten sind. So schreibt zum Beispiel eine Versicherung die Versichertennummer mit in die Abbuchungen, was einen sehr guten Tagging-Indikator darstellt, jedoch nur für einen speziellen Nutzer dieses Programms. Das schreiben eigener Regeln ist daher unumgänglich, um bessere Ergebnisse zu erzielen.

Für diesen Zweck gibt es aber die Möglichkeit im Frontend Regeln auszuprobieren, ohne dass Umsätze geändert werden. Neue Regeln können ebenfalls über die Oberfläche temporär hochgeladen werden (bis zum Neustart des Servers) oder dauerhaft im Ordner `settings/rule` abgelegt werden. Die Dateien hier werden in alphabetisch sortierter Reihenfolge geladen (angefangen bei `00-*`), wobei spätere Regeln ggf. bestehende Regeln überschreiben können. Im Rwepository werden nur die Default-Regeln angepasst. Auf diese Weise können eigene Regeln gepflegt werden, ohne dass sie bei Updates verloren gehen.


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
