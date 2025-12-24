# Models

## Dictionary einer Config

```
{
    'uuid': str             # (generated)
    'metatype': str         # (config)
    'name': str,            # Typ des Configeintrags (user, group, ui...)

    -------- Zusatz je Config Typ -------

    **kwargs
    
    . . . . . . . z.B. User . . . . . . .

    'username': str,
    'password': str         # hashed
    'ibans': list           # Eigentümer
    'rules': dict           # private Regeln
    'parser': dict          # private Parser

    . . . . . . . z.B. Gruppe . . . . . .

    'groupname': str
    "ibans": list,          # IBANs, die zur Gruppe gheören
    "members": [
        { "user": "anna", "role": "owner" },
        { "user": "bob", "role": "viewer" }
    ]
}
```

## Datenbankeintrag für eine Transaktion

```
{
    'uuid': str,            # (generated)
    'date_tx': int,         # (UTC)
    'text_tx': str,
    'betrag': float,
    'pper': str,

    ----------- optional -----------

    'valuta': int ,      # (UTC)
    'art': str,
    'currency': str,
    'parsed': dict( str: str )
    'category': str,
    'tags': list[str],
    'priority': int,
}
```

## Parsing Objects

Beim Import eines Kontoauszugs werden die Transaktionen in ihre Grunddaten zerlegt und in einer Datenbankgespeichert. Das Parsing erkennt nach bestimmten Regeln Informationen, die sich aus den Rohdaten ergeben und reichert damit den Informationsgehalt der einzelnen Transaktion an.

Bei jeder Regex-Regel gilt, dass der Ausdruck genau eine Matching-Group ergeben muss, deren Informationen als Wert des Parsings übernommen wird.

```
{
    'metatype': str,
    'name': str,
    'regex': r-str(RegEx)
}
```

#### .metatype, str (`parser`)

Klassifiziert das Objekt als Regel für das Parsing.

#### .name, str

Frei wählbarer Name der Regel.

#### .regex, r-str (optional)

Regex String, der auf den Buchungstext angewendet werden soll. Er muss genau eine Matching-Group enthalten. Der Wert dieses Treffers (der Gruppe) wird als Wert mit dem Namen der Regel in der Transaktion als Ergebnis gespeichert.

## Rule Objects

```
{
    'metatype': str
    'name': str,
    'multi': str,
    'parsed': dict(
        key, str | int : value str | int | bool | list
    )
    'filter': list( dict(
        'key': str,
        'value': int, str, bool, list,
        'compare': str
    ) )
    'category': str | None,
    'tags': list,
    'prioriry': int | None
}
```

Regeln können Attribute einer Transaktion untersuchen und anhand dessen klassifizieren oder taggen. Bei den Regeln zum Tagging können auch zuvor geparste Informationen zählen; bei den Regeln zum Kategorisieren zusätzlich auch bereits gesetzte Tags einer Transaktion. Beide Typen unterscheiden sich in der Angabe beim Schlüssel `metatype`, sind aber sonst sehr ähnlich. Persistente Regeln werden als `json` im Ordner `settings/rule` abgelegt. Die Nummerierung im Dateinamen gibt die Lade-Reihenfolge an. Später geladene Regeln mit gleichem Namen können frühere überschreiben.

### Schlüssel dieses Objektes

#### .metatype, str (`rule` | `category`)

Klassifiziert das Objekt als Regel für das Tagging oder zur Kategorisierung. Einige Schlüssel werden abhängig von dieser Angabe anders genutzt (siehe unten).

#### .name, str

Frei wählbarer Name der Regel.

##### .multi, str (`AND` | `OR`)

Art der Verkettung der Filter. Ohne diese Angabe wird der Default `AND` gewählt. Wird hier `OR` angegeben, werden alle Filter (`tags`, `filter`, `parsed`-keys) mit `OR` verknüpft.

#### .parsed, dict (optional)

Ein Dictionary, bei dem der `key` der Bezeichner für den geparsten Wert einer Transaktion unter `.parsed.$WERT` ist, der mit dem `value` abgeglichen wird.

##### .parsed[].key, str, int

Die Bezeichnung (Schlüssel) des Werts, der geprüft werden soll.

#### filter, list (optional)

Liste mit Dictionaryies, die Argumenten zum durchsuchen von allgemeinen Werten einer Transaktion enthalten.

##### filter[].key, str | int

Die Bezeichnung (Schlüssel) des Werts, der geprüft werden soll. `key` kann hier jeder Bezeichner sein, der in der ersten Ebene des Transaktionsobjektes vorkommen könnte. Daher kann auch `tags` mit einer Liste als `filter[].value` verwendet werden (s.u.). Ausgenommen sind hier lediglich `parsed` Werte, für die es ja aber dafür eine eigene Filterangabe gibt.

#### filter[].value, str | int | bool | list

Der Wert, mit dem der Wert aus der Datenbank abgeglichen werden soll.

#### filter[].compare, str (`==` | `!=` | `<` | `>` | `<=` | `>=` | `in` | `notin` | `all` | `regex`)

Art des Vergleichs:

```
Wert-aus-DB von rule.key
$compare
rule.value
```

Dabei haben die Operatoren folgende Bedeutung:

- `==` : Die Werte müssen exakt gleich sein (default).
- `!=` : Die Werte müssen ungleich sein.
- `<` : Der Wert in der Datenbank muss kleiner sein als der Vergleichswert.
- `>` : Der Wert in der Datenbank muss größer sein als der Vergleichswert.
- `<=` : Der Wert in der Datenbank muss kleiner oder gleich sein wie der Vergleichswert.
- `>=` : Der Wert in der Datenbank muss größer oder gleich sein wie der Vergleichswert.
- `in`: Mindestens ein Wert der Vergleichsliste muss in dem Listenwert aus der Datenbank vorkommen.
- `all`: Alle Werte der Vergleichsliste müssen in dem Listenwert aus der Datenbank vorkommen.
- `notin`: Kein Wert der Vergleichsliste darf in dem Listenwert aus der Datenbank vorkommen.
- `regex`: Regex String, der auf den Buchungstext angewendet werden soll. Ein Teil-Treffer des RegExes wird als Treffer gewertet.

#### .tags, list (nur bei metatype: `rule`)

Liste mit Tags, die bei getroffene Einträge hinzugefügt werden.

#### .category, str (nur bei metatype: `category`)

Name der Hauptkategorie, die bei einem Treffer für den Eintrag gesetzt werden soll. Es muss entweder eine Haupt- oder eine Sekundärkategorie angegeben werden.

#### .priority, int (nur bei metatype: `category`)

Priorität der Regel. Eine höhere Priorität (größere Zahl) überschreibt zuvor gesetzt Kategorien mit einer niedrigeren Priorität.

Ein manuelles Kategorisieren hat immer die höchste Priorität.
