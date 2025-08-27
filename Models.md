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
