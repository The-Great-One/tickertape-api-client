# tickertape-api-client

`tickertape-api-client` is a typed Python wrapper around useful public Tickertape web endpoints.

See the repository README for complete examples and endpoint notes.

Documentation pages:

- [Endpoint map](endpoints.md)
- [Stock screener filters](screener-filters.md)

## Install

```bash
pip install git+https://github.com/The-Great-One/tickertape-api-client.git
```

## Minimal example

```python
from tickertape_api import TickertapeClient

with TickertapeClient() as tt:
    print(tt.market_status("IN"))
    print(tt.us_latest_quotes(["IXIC", "AXP"]))
    print(tt.mutual_fund_holdings("M_MAHD")["currentAllocation"][:10])
```

## CLI-only auth setup

```bash
printf '%s' 'session_cookie_here' | tickertape auth-set --cookie-stdin
tickertape auth-status
```

This stores manually provided token/cookie material in `~/.config/tickertape-api-client/credentials.json` for `TickertapeClient.from_env()`.

## Browser-assisted auth capture

```bash
pip install "git+https://github.com/The-Great-One/tickertape-api-client.git#egg=tickertape-api-client[auth]"
python -m playwright install chromium
tickertape auth-capture
```

This opens the normal Tickertape website and waits for you to complete login manually. It then stores cookies/token in `~/.config/tickertape-api-client/credentials.json` for `TickertapeClient.from_env()`.
