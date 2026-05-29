# tickertape-api-client

`tickertape-api-client` is a typed Python wrapper around Tickertape's public web endpoints.

It covers Indian equities, US stocks/indexes, market status, market mood, screeners, ETFs, indices, mutual funds, portfolio data, watchlists, and more — including real-time quotes via Socket.IO.

Documentation pages:

- [Complete Endpoint Map](endpoints.md) — all 227 discovered endpoints, organized by host and category, with auth requirements
- [Stock Screener Filters](screener-filters.md) — every filter label for screener queries, with premium/locked status

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

Stores token/cookie in `~/.config/tickertape-api-client/credentials.json` for `TickertapeClient.from_env()`.

## Browser-assisted auth capture

```bash
pip install "git+https://github.com/The-Great-One/tickertape-api-client.git#egg=tickertape-api-client[auth]"
python -m playwright install chromium
tickertape auth-capture
```

Opens the normal Tickertape website, waits for you to complete login manually, then saves cookies/token locally.
