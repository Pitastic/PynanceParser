# PynanceParser

![pytest](https://img.shields.io/badge/pytest-passed%20(26/26)-darkgreen)
![pylint](https://img.shields.io/badge/pylint-9.93-darkgreen)

Analyse und Darstellung von Kontoumsätzen bei mehreren Banken.

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

Modulare Importer können nach und nach für verschiedene Banken oder spezielle Formate entwickelt werden. Füge einen Importer für deine Bank hinzu :wink:

### Analyse

- Automatisches Extrahieren und bewerten einer Transaktion durch Muster *(RegEx parst Kerninformationen)*
- Automatisches Kategorisieren anhand hinterlegter Regeln *(RegEx + Kerninformationen)*
- Manuelles Kategorisieren

Hinterlegte Regeln können die extrahierten Informationen, weitere Umsatzinformationen und weitere RegExes berücksichtigen und ermöglichen so komplexe Bewertungen einfach zu erstellen.

Eine Klassifizierung *(Tagging)* wird dabei nach Haupt- und Unterkategorie vorgenommen. Sie erfolgt bei einem Durchlauf optional für alle unkategorisierten Umsätze, auf alle oder auf einen Teil anhand einer festgelegten Priorität (der Kategorie).

### Darstellung

- Umsatzübersicht
- Statistiken
- Verteilungen

Listen und Diagramme zeigen dir, wo eigentlich das Geld geblieben ist :thinking:

## Contribution

You're Welcome !

Erstelle einen Reader für verschiedene Formate deiner Bank.

Dieses Repo ist test-driven. Vor dem Merge ist ein Unit- und ggf. Integrationtest erforderlich, der aber auch vom Kernprojekt erstellt werden kann.

## Setup

```
pip install -r requirements.txt
python3 app/app.py
```

### Testumgebung

...zusätzlich zum Setup:

```
pip install -r tests/requirements.txt
pytest
```