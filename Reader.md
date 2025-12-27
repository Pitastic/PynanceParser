## Entwickeln von neuen Readern

### Erstelle notwendige Dateien

Neben dem Modul benätigst du noch einen Test. Ziel des Tests ist es, dass lokal eine Beispiel Datei importiert wird, wenn sie vorhanden ist und im Ergebnis geprüft wird, ob die eingelesenen Einträge sinnvoll sind. Eine Prüfung nach Transaktionsinhalten findet nicht statt.

**Lade keine privaten Kontoauszüge in das Repository hoch !**

Kopiere dazu am besten `tests/test_unit_reader_Comdirect.py` und...

- Passe den Dateinamen der Beispieldatei an
- Entscheide, ggf. eine Testfunktion zu überspringen mit `@pytest.mark.skip(reason="Currently not implemented yet")`

Kopiere als nächstes `reader/Generic.py` und

- Passe den Dateinamen der Beispieldatei an
- Entwickle deinen Reader (siehe unten) und teste ihn zwischendurch/am Ende mit `pytest -svx tests/test_unit_reader_*.py`

Der Test führt die `from_csv` bzw. `from_pdf` Funktion aus und überprüft, ob das Format richtig ist und die Werte der Transaktionen über entsprechende Keys mit sinnvollen Werten verfügen.

### Logik des Readers erstellen

Ziel der Funktion `from_csv` bzw. `from_pdf` ist es, eine Liste von Transaktionen in Form eines Dictionaries einzulesen, wobei die Keys der Vorgabe des [allgemeinen Models für Transaktionen](Models.md) folgt.

Für das Einlesen einer PDF ist dabei mehr Aufwand notwendig. Hierbei kommt das Modul `camelot` zum Einsatz.

Für die Entwicklung der richtigen Einstellungen wird neben dem Python Modul auch das CLI Programm empfohlen. Installation und Konfigurationen findest du in der [Dokumentation](https://camelot-py.readthedocs.io/en/master/).

#### Step by Step

- Lege eine Beispieldatei nach `/tmp/bank.pdf`
- Nutze den `grid` Modus im CLI, um angezeigt zu bekommen, was `camelot` mit den jeweiligen Einstellungen für Tabelleninhalte finden würde.
- Übertrage die erfolgreichen Flags und Einstellungen in den Python Aufruf im Reader-Modul
- Lasse dir dort erst alle eingelesenen Zeileninhalte ausgeben (während eines `pytests`) und entscheide, wie du die Inhalte ggf. umformen, zusammenfassen oder trennen musst, um das [erwartete Muster](Models.md) zu erhalten.

Ein guter Start ist folgender Aufruf:

```
camelot -plot grid /tmp/bank.pdf
```

Nützliche Flags sind `-p` für einzelne Seiten (schneller bzw. können so auch Edgecases geprüft werden), `-C` um die Koordinaten von Spalten festzulegen (meistens erforderlich) und `-T` um den Bereich festzulegen, wo nach einer Tabelle geprüft werden soll (meistens erforderlich). Ein fortgeschrittenerer Aufruf könnte daher so aussehen:

```
camelot -p 1,6 stream -C "75,112,440,526" -T "60,629,573,51" -plot grid /tmp/bank.pdf
```

Am Schluss kann noch der Wert eingestellt werden, ab dem Buchstaben vertikal oder horizontal zu einem Wort oder einer Zeile zusammengefasst oder schon getrennt werden. Mit dem Argument `layout_kwargs` in der Python-Methode können Argumente an den darunterliegenden `PDFMiner` durchgereicht werden, was genau diese Einstellungen ermöglicht.

Die Dokumentation dieser möglichen Werte findet man in der [Dokumentation des PDFMiner](https://pdfminersix.readthedocs.io/en/latest/reference/composable.html). Der [Commerbank.py Reader](reader/Commerzbank.py) nutzt diese wegen der bestimmten Schriftart und Zeichenabständen im PDF.

## Stelle einen Pull Request

Beschreibe, welche Features du hinzugefügt oder verbessert hast. Pytest und Pylint werden hier geprüft. Das Testen des neuen Imports kann nur bei dir erfolgen, da die Maintainer in der Regel über keine Testdateien dafür verfügen. Teste daher sorgfältig.
