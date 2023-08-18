# Models

## Datenbankeintrag für eine Transaktion

```
{
    'uuid': str,
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

## Datenbankeintrag für User Settings

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

### Dictionary eines Rulesets

```
{
    'primary': str,
    'regex': r-str( RegEx ),    # (optional if parsed)
    'parsed': dict(             # (optional if regex)
        str( parsed-Key ) : r-str( RegEx )
    )

    ----------- optional -----------

    'secondary': str,
    'prioriry': int
}
```
