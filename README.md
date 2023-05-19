# PyCashFlow

Abruf, Analyse und Darstellung von Kontoumsätzen bei mehreren Banken.

## Features

### Parse

- CSV Import (exportierte Kontoümsätze)
- PDF Import (Kontoauszüge aus dem Onlinebanking Archiv)
- HTTP (Daten von APIs - keine Banken-APIs leider :man_shrugging: )

Modulare Importer können nach und nach für verschiedene Banken oder spezielle Formate vorhanden sein.

### Analyse

- Tagging
- Reguläre Ausdrücke
- Automatisches Tagging

Klassifizierung von Kontoumsätzen nach Haupt- und Unterkategorie. Das automatische Tagging erfolgt auf Wunsch und Grundlage der bisherigen Taggings mittels KI.

### Darstellung

- Umsatzübersicht
- Statistiken
- Verteilungen

Listen und Diagramme zeigen dir, wo eigentlich das Geld geblieben ist :wink:

## Contribution

Beiträge erwünscht.

Die Parser sind modular gestaltet um Code für verschiedene Banken einfach aufzunehmen.

Für diese und andere Bereiche können gerne PullRequests gestellt werden, die allerdings alle PyTests bestehen müssen.

Für neuen Code sollte ebenfalls ein Test geschrieben werden. Gegebenenfalls wird dies vor dem Merge aber auch vom Projekt übernommen.

## Setup

```
pip install -r requirements.txt
```