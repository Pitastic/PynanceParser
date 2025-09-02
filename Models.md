## Models

### Datenbankeintrag für eine Transaktion

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

### Metadaten

#### Dictionary eines Rulesets (Tag/Parse)

Regeln können Attribute einer Transaktion untersuchen und anhand dessen klassifizieren oder taggen. Zu den Werten kann nicht die primäre Kategorie zählen, wohl aber andere Tags, parsing Informationen oder Regexes auf den Buchungstext (und mehr).

```
{
    'uuid': str             # (generated)
    'metatype': str         # (config|rule|parser)
    'name': str,
    'regex': r-str( RegEx ),

    -------- Zusatz bei Rules -------

    'category': str | None,
    'tags': list[str] | None,

    . . . . . . . optional . . . . . .

    'prioriry': int,
    'parsed': dict(
        'multi': str,       # (AND|OR)
        'query': dict       # (key=Name, val=Value)
    )
}
```

#### Dictionary einer Config

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

## Handling von Prioritäten

Die Priorität wird zwischen 0 und 100 automatisch gesetzt, kann aber auch abgegen werden. 0 ist unwichtig, 100 ist wichtig.

Beim Tagging werden nur Einträge selektiert, die eine niedrigere Priorität haben als die akutelle Regel.

Es wird beim Taggen entweder die Priorität 1 (automatisches Taggen), die der Regel gesetzt (wenn diese höher ist) oder die explizit übermittelte. Ausnahmen sind:

- Das manuelle Taggen: Hier wird immer eine Priorität von 99 gesetzt.
- Das automatische Tagging mit einer explizit angegebenen Regel: Hier werden Einträge < 99 selektiert und überschrieben, dann aber wieder die Priorät der Regel (oder 1) gesetzt.



------

Tags als Filter werden immer ODER verknüpft. Es reicht also, wenn mindestens ein Tag der Liste vorhanden ist (Keyword `in`). Sollen alle Tags enthalten sein, muss der Operator `all` heißen. Soll keines enthalten sein, muss der Operator `notin` sein.


## Rule Objects

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

TODO: Ergänzen

#### .tags, list (nur bei metatype: `rule`)

Liste mit Tags, die bei getroffene Einträge hinzugefügt werden.

#### .category, str (nur bei metatype: `category`)

Name der Hauptkategorie, die bei einem Treffer für den Eintrag gesetzt werden soll. Es muss entweder eine Haupt- oder eine Sekundärkategorie angegeben werden.

#### .subcategory, str (nur bei metatype: `category`)

Name der Sekundärkategorie, die bei einem Treffer für den Eintrag gesetzt werden soll. Es muss entweder eine Haupt- oder eine Sekundärkategorie angegeben werden.

#### .priority, int (nur bei metatype: `category`)

Priorität der Regel. Eine höhere Priorität (größere Zahl) überschreibt zuvor gesetzt Kategorien mit einer niedrigeren Priorität.