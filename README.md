# PynanceParser

![pytest](https://img.shields.io/badge/pytest-passed%20(21/21)-green)
![pylint](https://img.shields.io/badge/pylint-9.99-green)

Abruf, Analyse und Darstellung von Kontoumsätzen bei mehreren Banken.

## Features

### Parsing

Importieren von Kontoumsätzen aus

- Umsatzübersicht im Online Banking
    - CSV Export
    - PDF Export
- Kontoauszüge
    - PDFs aus dem Online Banking Archiv
    - PDFs eingescannter Papierauszüge
- Online Quellen
    - HTTP (Daten von APIs - keine Banken-APIs leider :man_shrugging: )

Modulare Importer können nach und nach für verschiedene Banken oder spezielle Formate vorhanden sein.

### Analyse

- Automatisches Extrahieren und bewerten einer Transaktion durch Muster (RegEx)
- Automatisches Kategorisieren anhand hinterlegter Regeln
- Manuelles Kategorisieren

Hinterlegte Regeln können die extrahierten Informationen, weitere Umsatzinformationen und weitere RegExes berücksichtigen oder anhand einer Ähnlichkeitssuche eines manuell herausgesuchten Umsatzes entscheiden.

Die Klassifizierung wird dabei nach Haupt- und Unterkategorie vorgenommen und erfolgt für alle oder alle unkategorisierten Umsätze auf Wunsch, automatisch beim Import oder manuell für markierte Umsätze über die Obefläche.

### Darstellung

- Umsatzübersicht
- Statistiken
- Verteilungen

Listen und Diagramme zeigen dir, wo eigentlich das Geld geblieben ist :wink:

## Contribution

Beiträge erwünscht.

Die Reader sind modular gestaltet um Code für verschiedene Banken einfach aufzunehmen.

Für diese und andere Bereiche können gerne PullRequests gestellt werden, die allerdings alle PyTests bestehen müssen.

Für neuen Code sollte ebenfalls ein Test geschrieben werden. Gegebenenfalls wird dies vor dem Merge aber auch vom Projekt übernommen.

## Setup

```
pip install -r requirements.txt
python3 src/app.py
```