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