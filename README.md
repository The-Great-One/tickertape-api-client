# tickertape-api-client

A production-ready Python client for **public Tickertape web endpoints** — Indian equities, US stocks/indexes, mutual funds, screeners, ETFs, indices, market mood, and authenticated portfolio access with automatic session refresh.

[![PyPI version](https://img.shields.io/pypi/v/tickertape-api-client.svg)](https://pypi.org/project/tickertape-api-client/)
[![Python 3.10+](https://img.shields.io/pypi/pyversions/tickertape-api-client.svg)](https://pypi.org/project/tickertape-api-client/)
[![License: MIT](https://img.shields.io/pypi/l/tickertape-api-client.svg)](https://github.com/The-Great-One/tickertape-api-client/blob/main/LICENSE)
[![CI](https://github.com/The-Great-One/tickertape-api-client/actions/workflows/ci.yml/badge.svg)](https://github.com/The-Great-One/tickertape-api-client/actions)

> **Important:** These are undocumented public web-app endpoints reverse-engineered from Tickertape's website. They can change without notice. Use sensible rate limits, caching, and fallbacks. This package does **not** bypass auth, scrape private user data, or include credentials.

## Installation

```bash
pip install tickertape-api-client
```

With portfolio support (curl_cffi for cookie impersonation):

```bash
pip install "tickertape-api-client[portfolio]"
```

With browser-assisted auth capture (Playwright):

```bash
pip install "tickertape-api-client[auth]"
```

With everything:

```bash
pip install "tickertape-api-client[portfolio,auth]"
```

For local development:

```bash
git clone https://github.com/The-Great-One/tickertape-api-client.git
cd tickertape-api-client
pip install -e ".[dev]"
```

## Quick start

### Public endpoints (no auth needed)

```python
from tickertape_api import TickertapeClient

with TickertapeClient() as tt:
    # Market status
    print(tt.market_status("IN"))

    # Indian stock quotes
    print(tt.india_quotes(["RELI", ".NSEI"]))

    # US stock quotes
    print(tt.us_latest_quotes(["AAPL", "MSFT", "GOOGL"]))

    # US stock financials
    print(tt.us_financials("AAPL", "income"))

    # Mutual fund holdings
    print(tt.mutual_fund_holdings("M_MAHD"))

    # Screener query
    print(tt.screener_query({"match": {"sector": ["Financials"]}, "sortBy": "marketCap", "sortOrder": -1}))
```

### Authenticated portfolio (session cookies)

```python
from tickertape_api import PortfolioClient

# Uses cookies stored at ~/.config/tickertape-api-client/credentials.json
with PortfolioClient() as pc:
    # Mutual fund holdings
    print(pc.mf_holdings())

    # Stock holdings
    print(pc.stock_holdings())

    # Portfolio summary
    print(pc.portfolio_summary())

    # US holdings
    print(pc.us_holdings())

    # Watchlists
    print(pc.watchlists())
```

### CLI

```bash
# Public data
tickertape market-status IN
tickertape quote RELI .NSEI
tickertape us-quote AAPL MSFT GOOGL
tickertape us-chart AAPL --duration 1y
tickertape mf-search "mahindra focused"
tickertape mf-holdings M_MAHD

# Portfolio (requires auth setup)
tickertape portfolio-summary
tickertape portfolio-mf
```

## Authentication

### Option 1: CLI credential setup

If you already have a cookie/token from a logged-in Tickertape browser session:

```bash
# Safer for shell history: paste cookie through stdin
printf '%s' 'session_cookie_here' | tickertape auth-set --cookie-stdin

# Or pass explicitly
tickertape auth-set --token 'bearer_token_here' --cookie 'raw_cookie_header_here'

tickertape auth-status
```

### Option 2: Browser-assisted capture

Opens the real Tickertape site, lets you complete the normal login/CAPTCHA/2FA flow, then saves only the resulting cookies locally:

```bash
pip install "tickertape-api-client[auth]"
python -m playwright install chromium
tickertape auth-capture
```

### Option 3: Programmatic

```python
from tickertape_api import TickertapeClient

# Pass explicitly
client = TickertapeClient(
    auth_token="<bearer-token>",
    cookie_header="<raw Cookie header from your browser session>",
)

# Or from env vars
# export TICKERTAPE_AUTH_TOKEN='...'
# export TICKERTAPE_COOKIE='...'
client = TickertapeClient.from_env()
```

Credentials are saved to `~/.config/tickertape-api-client/credentials.json`.

The auth commands do **not** submit passwords, bypass 2FA/CAPTCHA, or replicate private login APIs.

## Session refresh (no relogin needed)

The `PortfolioClient` automatically refreshes your Tickertape session the same way the browser does:

1. When the JWT nears expiry (~24h), it calls `POST https://auth.api.tickertape.in/auth/refresh` with your persisted cookies (no body)
2. The server returns a new JWT + CSRF token
3. New credentials are persisted back to disk
4. On API `401`, it also forces a refresh and retries the request once

This means your session stays alive across days/weeks of inactivity — just like your browser. No relogin needed unless the server-side session itself expires.

```python
from tickertape_api import PortfolioClient

# Force a refresh manually
with PortfolioClient(account="primary") as pc:
    pc._refresh_jwt_if_needed(force=True)  # refresh now
    print(pc.mf_holdings())  # uses fresh JWT
```

### Multi-account support

Manage multiple Tickertape accounts (personal, family, etc.):

```bash
# Capture credentials for different accounts
tickertape auth-browserless --account primary 9876543210:1234
tickertape auth-browserless --account family  9123456789:5678

# Use a specific account
tickertape --account primary portfolio-summary
tickertape --account family  portfolio-mf

# Set default via environment variable
export TICKERTAPE_ACCOUNT=primary
tickertape portfolio-summary  # uses "primary"
```

```python
from tickertape_api import PortfolioClient, TickertapeClient

# PortfolioClient with named account
with PortfolioClient(account="primary") as pc:
    print(pc.mf_holdings())

# TickertapeClient with named account
with TickertapeClient.from_env(account="family") as tt:
    print(tt.screener_screens())

# Iterate all accounts
for account, client in PortfolioClient.iter_accounts():
    print(f"{account}: {client.portfolio_summary()}")
```

The credentials file uses an `"accounts"` dict:

```json
{
  "accounts": {
    "primary": {
      "cookie_header": "...",
      "cookie_dict": {"jwt": "...", "x-csrf-token-tickertape-prod": "..."}
    },
    "family": {
      "cookie_header": "...",
      "cookie_dict": {"jwt": "...", "x-csrf-token-tickertape-prod": "..."}
    }
  }
}
```

The old flat format (top-level keys) continues to work as the default account.

## Endpoint coverage

### Market status

```python
tt.market_status("IN")   # India
tt.market_status("US")    # US
```

Backed by: `GET https://gms-api.tickertape.in/market/{market}/status`

Fields: `isOpen`, `isHoliday`, `isWeekend`, `currentWindow`, `nextWindow`, `reason`

### Latest quotes

```python
tt.india_quotes(["RELI", ".NSEI"])
tt.us_latest_quotes(["AAPL", "MSFT", "GOOGL"])
tt.forex_latest("USDINR")
```

Backed by:
- `GET https://quotes-api.tickertape.in/quotes?sids=RELI,.NSEI`
- `GET https://gms-api.tickertape.in/quotes/US/latest?tickers=AAPL,MSFT`
- `GET https://gms-api.tickertape.in/quotes/FOREX/latest?tickers=USDINR`

### Indian stocks

```python
tt.stock_info("RELI")
tt.stock_summary("RELI")
tt.stock_intra_chart("RELI")
tt.stock_inter_chart("RELI", duration="1y")
tt.stock_news("RELI")
tt.stock_checklists("RELI")
tt.stock_financials("RELI", statement="income", period="annual", view="normal")
tt.stock_ohlc("RELI")               # OHLC candles
tt.stock_ohlc_with_splits("RELI")   # split-adjusted OHLC
tt.stock_intraday_ohlc("RELI")      # intraday candles
```

### US securities

```python
tt.us_asset_info(["AAPL", "MSFT"])
tt.us_asset_info(["VOO", "GLD"], asset_type="etfs")
tt.us_stock_overview("AAPL")
tt.us_etf_overview("VOO")
tt.us_chart("AAPL", "1D")            # intraday
tt.us_chart("AAPL", "5Y")            # historical
tt.us_security_chart("AAPL", duration="1y")
tt.us_financials("AAPL", "income")
tt.us_financials("AAPL", "balancesheet")
tt.us_financials("AAPL", "cashflow")
tt.us_ohlc("AAPL", duration="1y")    # OHLC candles
tt.us_filters()                       # available screener filters
```

### Mutual funds

```python
# Full MF universe (search locally by name/isin/mfId)
universe = tt.mutual_funds_list()["universe"]

# Fund details
tt.mutual_fund_info("M_MAHD")
tt.mutual_fund_summary("M_MAHD")

# Portfolio / holdings
holdings = tt.mutual_fund_holdings("M_MAHD")
print(holdings["currentAllocation"][:5])

# Other MF endpoints
tt.mutual_fund_chart("M_MAHD", duration="1y")
tt.mutual_fund_sip_chart("M_MAHD")
tt.mutual_fund_fund_managers("M_MAHD")
tt.mutual_fund_checklists("M_MAHD")
tt.mutual_fund_widget("M_MAHD")
tt.mutual_fund_ohlc("M_MAHD", duration="1y")  # OHLC candles
```

### Screeners

```python
# Stock screener
tt.screener_filters()
tt.screener_prebuilt()
tt.screener_query({
    "match": {"sector": ["Financials"]},
    "sortBy": "marketCap",
    "sortOrder": -1,
})

# Mutual fund screener
tt.mutual_fund_screener_filters()
tt.mutual_fund_screener_prebuilt()
tt.mutual_fund_screener({
    "match": {"option": ["Growth"]},
    "sortBy": "aum",
    "sortOrder": -1,
})
```

The complete stock screener filter list is in [`docs/screener-filters.md`](docs/screener-filters.md).

### ETFs and indices

```python
tt.etf_info("HDFB")
tt.etf_summary("HDFB")
tt.index_info(".NSEI")
tt.index_constituents(".NSEI")
```

### Market mood / widgets

```python
tt.mmi_now()
tt.product_tape()
tt.product_banners()
tt.platform_smallcase_widget(["fd", "smallcases"])
```

### Portfolio (authenticated)

```python
from tickertape_api import PortfolioClient

with PortfolioClient() as pc:
    pc.mf_holdings()           # Mutual fund holdings
    pc.stock_holdings()        # Stock holdings
    pc.us_holdings()           # US holdings
    pc.portfolio_summary()     # Overall summary
    pc.holdings_status()       # Holdings status
    pc.quote_portfolio()       # Portfolio quotes
    pc.watchlists()            # User watchlists
```

### Search

```python
tt.search("reliance")
tt.suggest("reliance")
```

## Error handling

```python
from tickertape_api import TickertapeAPIError, TickertapeHTTPError, TickertapeClient

try:
    TickertapeClient().stock_info("BAD")
except TickertapeHTTPError as exc:
    print(f"HTTP {exc.status_code}: {exc.payload}")
except TickertapeAPIError as exc:
    print(f"API error: {exc.payload}")
```

## Production guidance

- Treat this as a **public-web-data client**, not an exchange-grade market data feed
- Cache responses where possible
- Add retries/backoff in your application layer for batch jobs
- Keep request rates low
- Keep Kite/broker/exchange data as the source of truth for trading-critical execution
- Build fallbacks because endpoints are undocumented and may change

## API reference

The complete endpoint inventory is in [`docs/endpoints.md`](docs/endpoints.md) (227+ endpoints across 4 hosts).

### Key classes

| Class | Purpose | Transport |
|-------|---------|-----------|
| `TickertapeClient` | Public endpoints (stocks, MFs, screeners, US, etc.) | httpx |
| `PortfolioClient` | Authenticated portfolio endpoints | curl_cffi (cookie impersonation) |
| `Candle` | OHLC candle data structure | — |
| `OHLCResult` | OHLC result with splits | — |

## Development

```bash
git clone https://github.com/The-Great-One/tickertape-api-client.git
cd tickertape-api-client
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"

# Run checks
ruff check .
mypy src
pytest
python -m build
```

## License

MIT — see [LICENSE](LICENSE)