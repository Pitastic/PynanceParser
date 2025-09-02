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
    'iban': str,

    ----------- optional -----------

    'date_wert': int ,      # (UTC)
    'art': str,
    'currency': str,
    'parsed': dict( str: str )
    'category': str,
    'subcategory': str,
    'tags': list[str],
    'priority': int,
}
```

## Rule Objects

```
{
    'uuid': str
    'metatype': str
    'name': str,
    'regex': r-str(RegEx),
    'parsed': dict(
        'multi': str,
        'query': dict(
            'key': str,
            'value': int, str, bool, list,
            'compare': str
        )
    )
    'category': str | None,
    'subcategory': str | None,
    'tags': list | dict | None,
    'prioriry': int
}
```

Regeln können Attribute einer Transaktion untersuchen und anhand dessen klassifizieren oder taggen. Bei den Regeln zum Tagging können auch zuvor geparste Informationen zählen; bei den Regeln zum Kategorisieren zusätzlich auch bereits gesetzte Tags einer Transaktion. Beide Typen unterscheiden sich in der Angabe beim Schlüssel `metatype`, sind aber sonst sehr ähnlich. Persistente Regeln werden als `json` im Ordner `settings/rule` abgelegt. Die Nummerierung im Dateinamen gibt die Lade-Reihenfolge an. Später geladene Regeln können frühere überschreiben.

### Schlüssel dieses Objektes

#### .uuid, str

Generierte Zeichenkette zur eindeutigen Identifizierung des Eintrags.

#### .metatype, str (`rule` | `category`)

Klassifiziert das Objekt als Regel für das Tagging oder zur Kategorisierung. Einige Schlüssel werden abhängig von dieser Angabe anders genutzt (siehe unten).

#### .name, str

Frei wählbarer Name der Regel.

#### .regex, r-str (optional)

Regex String, der auf den Buchungstext angewendet werden soll. Dabei muss immer genau eine Treffergruppe definiert werden.

#### .parsed, dict (optional)

Dictionary mit Argumenten zum durchsuchen von geparsten Werten einer Transaktion:

##### .parsed.multi, str (`AND` | `OR`)

Art der Verkettung der Filter. Ohne diese Angabe oder ohne das `parsed` Objekt wird der Default `AND` gewählt. Wird hier `OR` angegeben, werden alle Filter (`regex`, `tags`, `parsed`-keys) mit `OR` verknüpft.

##### .parsed.query.key, str, int

Die Bezeichnung (Schlüssel) des Werts, der geprüft werden soll.

##### .parsed.query.value, str | int | bool | list

Der Wert, mit dem der Wert aus der Datenbank abgeglichen werden soll.

##### .parsed.query.compare, str (`==` | `!=` | `<` | `>` | `<=` | `>=` | `in` | `notin` | `all`)

Art des Vergleichs:

```
Wert-aus-DB von .parsed.query.key
$compare
.parsed.query.value
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

#### .tags, list | dict (optional bei metatype: `category`)

Dieser Schlüssel wird je nach `metatype` unterschiedlich gehandhabt:

- `rule` : Liste mit Tags, die bei getroffene Einträge hinzugefügt werden.
- `category`: Dictionary, welches als Filterargument hinzugefügt wird.

#### .tags.tags, list (nur bei metatype: `category`)

Liste von Tags, die abgeglichen werden soll.

#### .tags.compare, str (`in` | `notin` | `all`) (nur bei metatype: `category`) (optional)

Art des Listenabgleichs:

- `in`: Mindestens ein Tag der Liste muss in einem Eintrag vorhanden sein (default).
- `all`: Alle Tags müssen bei einem Eintrag vorhanden sein.
- `notin`: Es darf kein Eintrag der Liste in einem Eintra vorhanden sein.

#### .category, str (nur bei metatype: `category`)

Name der Hauptkategorie, die bei einem Treffer für den Eintrag gesetzt werden soll. Es muss entweder eine Haupt- oder eine Sekundärkategorie angegeben werden.

#### .subcategory, str (nur bei metatype: `category`)

Name der Sekundärkategorie, die bei einem Treffer für den Eintrag gesetzt werden soll. Es muss entweder eine Haupt- oder eine Sekundärkategorie angegeben werden.

#### .priority, int (nur bei metatype: `category`)

Priorität der Regel. Eine höhere Priorität (größere Zahl) überschreibt zuvor gesetzt Kategorien mit einer niedrigeren Priorität.

Ein manuelles Kategorisieren hat immer die höchste Priorität.
