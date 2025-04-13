## Models

### Datenbankeintrag für eine Transaktion

```
{
    'uuid': str,            # (generated)
    'date_tx': int,         # (UTC)
    'text_tx': str,
    'betrag': float,
    'iban': str,
    'parsed': str,
    'primary_tag': str,
    'secondary_tag': str

    ----------- optional -----------

    'date_wert': int ,      # (UTC)
    'art': str,
    'currency': str,

    'parsed': dict( str: str )

    'primary_tag': str,
    'secondary_tag': str,
    'priority': int,
}
```

### Datenbankeintrag für User Settings

```
{
    'username': str,
    'password': str,            # (Hashed)
    'accounts': list(
        str( IBAN )
    ),

    ----------- optional -----------

    'preferences': dict( str : Any ),
    'rules': dict(
        str( Rulename ) : dict( ruleset )
    )
}
```

#### Dictionary eines Rulesets (Tag/Parse)

Regeln können Attribute einer Transaktion untersuchen und anhand dessen klassifizieren oder taggen. Zu den Werten kann nicht die primäre Kategorie zählen, wohl aber andere Tags, parsing Informationen oder Regexes auf den Buchungstext (und mehr).

```
{
    'uuid': str             # (generated)
    'metatype': str         # (config|rule|parser)
    'name': str,
    'regex': r-str( RegEx ),

    ----------- bei Rules ----------

    'primary': str | None,
    'secondary': str | None,

    ----------- optional -----------

    'prioriry': int,
    'parsed': dict(
        'multi': str,       # (AND|OR)
        'query': dict       # (key=Name, val=Value)
    )
}
```

## Handling von Prioritäten

Die Priorität wird zwischen 0 und 100 automatisch gesetzt, kann aber auch abgegen werden. 0 ist unwichtig, 100 ist wichtig.

Beim Tagging werden nur Einträge selektiert, die eine niedrigere Priorität haben als die akutelle Regel.

Es wird beim Taggen entweder die Priorität 1 (automatisches Taggen), die der Regel gesetzt (wenn diese höher ist) oder die explizit übermittelte. Ausnahmen sind:

- Das manuelle Taggen: Hier wird immer eine Priorität von 99 gesetzt.
- Das automatische Tagging mit einer explizit angegebenen Regel: Hier werden Einträge < 99 selektiert und überschrieben, dann aber wieder die Priorät der Regel (oder 1) gesetzt.
