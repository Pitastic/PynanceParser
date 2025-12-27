# PynanceParser

![pytest](https://img.shields.io/badge/pytest-passed%20(55/55)-darkgreen)
![pylint](https://img.shields.io/badge/pylint-9.73-yellow)

*This repo is german but you are welcome to add your language to the frontend.*

Analyse und Darstellung von Kontoumsätzen bei mehreren Banken.

## Get Started

### Setup

```
python3.12 -m venv .venv
source .venv/bin/activate
.venv/bin/python3.12 -m ensurepip --upgrade # (optional)
pip install -r requirements.txt
.venv/bin/python3.12 app/server.py
```

### Start

- Importiere Kontoumsätze über CSV Listen oder PDF Kontoauszüge deiner Bank ([unterstützte Banken](#unterstützte-banken))
- Erstelle eine Gruppe mehrerer Konten, um alle diese Umsätze in einer Übersicht zu sehen
- Wende vorgefertigte oder eigene Regeln für das automatische Taggen und Kategorisieren deiner Umsätze an
- Suche und Filtere deine Umsätze nach einer Vielzahl möglicher Kriterien
- Lerne mehr über deinen Cashflow durch die Übersicht der statistischen Auswertungen. Hier kannst du alle oder nur gefilterte Umsätze berücksichtigen.

## Features

Die Funktionen des PynanceParsers setzen stark auf Reproduzierbarkeit. Das bedeutet, dass du beliebig oft gleiche Daten löschen und reimportieren kannst und halbautomatisch wieder die gleichen Ergebnisse (einmalige Transaktionen, Tagging, Kategorien, Statistiken) erhälts. Ein manuelles Editieren ist zwar möglich, aber die Ausnahme.

👉 **Modernes und responsives Design**

  *(Übersichtlich auf vielen Geräten)*

👉 **Keine doppelten Imports**

  *(Datum, Text und Betrag bilden eine einmalige Kombination)*

👉 **Automatisches Extrahieren von Zusatzinformationen**

  *(RegEx parst Kerninformationen)*

👉 **Automatisches und/oder manuelles Taggen**

  *(Regelbasiert: RegEx + Zusatzinformationen)*

👉 **Automatisches und/oder manuelles Kategorisieren**

  *(Regelbasiert: RegEx + Tags + Zusatzinformationen)*

👉 **Übersicht über alle Transaktionen**

  *(vielseitige Filtermöglichkeiten in einem Konto oder einer Kontogruppe)*

👉 **Statistische Auswertung auf dem angereicherten Datensatz**

  *(Kontextabhängige Statistken)*


### Darstellung

- Kontenverwaltung
- Kontohistorie
- Transaktionsdetails
- Statistiken/Verteilungen/Verläufe

![screenshots](https://github.com/user-attachments/assets/f6201658-eeb0-422c-b1a8-df9cb85cf842)

### Unterstützte Banken

| Bank                         | CSV | PDF |
|------------------------------|-----|-------------------------------|
| Comdirect                    | 🟢 Umsatzübersicht | 🟢 Finanzreport |
| Commerzbank                  | 🟢 Umsatzübersicht | 🟢 Kontoauszug |
| Sparkasse Hannover           | ⚫ *planned* | ⚫ *planned* |
| Volksbank Mittelhessen eG    | 🟢 Umsatzübersicht | 🟢 Kontoauszug |

Ist deine Bank noch nicht dabei? Den modularen Import kannst du mit [überschaubaren Aufwand](#entwickeln-von-neuen-readern) für deine Bank erweitern.

## Hinweise

### Workflow (CSV / PDF Imports)

Umsätze können sich beim Import überschneiden oder mehrfach hochgeladen werden: Transaktionen werden in der Regel nicht doppelt importiert.

Die Umsatzinformationen eines Kontoauszugs als PDF und der Export der Ansicht im Online Banking als CSV hat schon bei der Erstellung einen unterschiedlichen Informationsgehalt. Hinzu kommt, dass das Einlesen einer PDF nicht so verlässlich bei Zeilenumbrüchen und Leerzeichen funktioniert, weshalb Worte getrennt oder zusammengeschoben werden können. Ein und die selbe Transaktion kann daher unterschiedlich beschrieben worden sein, was einen doppelten Import (einer je Format) leider möglich macht.

Daher sollte man beachten:

- Regeln nicht auf zwingend vorhandene Leerzeichen auszulegen
- Beim Wechsel eines Formats (PDF / CSV) keine Überschneidungen zu haben (PDF zuerst, dann fehlende Transaktionen selektieren und via CSV exportieren - alternativ bei einem Format bleiben)

### Default Tagging- und Kategorisierungsregeln

In diesem Repository werden nur Basis-Regeln mitgeliefert, da speziellere und genauere Regeln sehr individuell auf einzelne Personen zugeschnitten sind. So schreibt zum Beispiel eine Versicherung die Versichertennummer mit in die Abbuchungen, was einen sehr guten Tagging-Indikator darstellt, jedoch nur für einen speziellen Nutzer dieses Programms. Das schreiben eigener Regeln ist daher unumgänglich, um bessere Ergebnisse zu erzielen.

## Anpassungen / Contribution

**You're Welcome !** :tada:

Erstelle einen Reader für verschiedene Formate deiner Bank oder ergänze die `parser` und `rules`.

### Entwickeln neuer `parser` / `rules`

Für diesen Zweck gibt es die Möglichkeit im Frontend Regeln auszuprobieren, ohne dass Umsätze geändert werden. Neue Regeln können ebenfalls über die Oberfläche temporär hochgeladen werden (bis zum Neustart des Servers) oder dauerhaft im Ordner `settings/rule` abgelegt werden. Die Dateien hier werden in alphabetisch sortierter Reihenfolge geladen (angefangen bei `00-*`), wobei spätere Regeln ggf. bestehende Regeln überschreiben können. Im Repository werden nur die Default-Regeln angepasst. Auf diese Weise können eigene Regeln gepflegt werden, ohne dass sie bei Updates verloren gehen.

**Wenn du neue Regeln für dieses Repository beitragen möchtest, gehst du wie folgt vor:**

- Erstelle einen Fork des Repositories
- Erstelle Testdaten, auf die die neuen Regeln treffen können
    - (am einfachsten ist eine JSON Datei wie `tests/commerzbank.json`)
- Erstelle einen Test wie in (`test_unit_handler_Tags.py`: `test_parsing_regex()`)
    - Tests helfen beim entwickeln, können aber auch durch die Maintainer während des Pull Request erstellt werden
- Stelle einen Pull Request

### Entwickeln von neuen Readern

Deine Bank fehlt noch in der Support Tabelle? Stelle einen Pull Request mit einem neuen Reader. [So kannst du ihn erstellen.](Reader.md).

### Testumgebung

...zusätzlich zum Setup:

```
pip install -r tests/requirements.txt
pytest
```
