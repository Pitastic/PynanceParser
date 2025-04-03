# Models

## Datenbankeintrag für eine Transaktion

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

### Dictionary eines Rulesets (Tag/Parse)

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
