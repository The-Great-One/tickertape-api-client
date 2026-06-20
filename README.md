# tickertape-api-client

A production-ready Python client for useful **public Tickertape web endpoints**.

It covers Indian equities, US stocks/indexes, market status, market mood, screeners, ETFs, indices, and mutual funds — including the useful mutual-fund portfolio/holdings endpoint:

```text
GET https://api.tickertape.in/mutualfunds/{mfId}/holdings
```

> **Important:** These are undocumented public web-app endpoints reverse-engineered from Tickertape's website. They can change without notice. Use sensible rate limits, caching, and fallbacks. This package does **not** bypass auth, scrape private user data, or include credentials.

## Installation

This project is currently installed from GitHub; it is **not published on PyPI** unless you explicitly publish a release later.

```bash
pip install git+https://github.com/The-Great-One/tickertape-api-client.git
```

For local development:

```bash
git clone https://github.com/The-Great-One/tickertape-api-client.git
cd tickertape-api-client
pip install -e ".[dev]"
```

## Quick start

```python
from tickertape_api import TickertapeClient

with TickertapeClient() as tt:
    print(tt.market_status("IN"))
    print(tt.india_quotes(["RELI", ".NSEI"]))
    print(tt.us_latest_quotes(["IXIC", "AXP", "AAPL"]))
    print(tt.us_security_chart("AXP", duration="1y"))
    print(tt.us_stock_overview("AAPL"))
    print(tt.us_financials("AAPL", "income"))
    print(tt.mutual_fund_holdings("M_MAHD"))
```

## CLI

```bash
tickertape market-status IN
tickertape quote RELI .NSEI
tickertape us-quote IXIC AXP AAPL
tickertape us-chart AXP --duration 1y
tickertape mf-search "mahindra focused"
tickertape mf-holdings M_MAHD
```

For premium fields, use either a pure CLI credential setup or the browser-assisted session capture flow.

Pure CLI setup, if you already copied a token/cookie from a logged-in Tickertape session:

```bash
# safer for shell history: paste cookie through stdin
printf '%s' 'session_cookie_here' | tickertape auth-set --cookie-stdin

# or pass explicitly
# tickertape auth-set --token 'bearer_token_here' --cookie 'raw_cookie_header_here'

tickertape auth-status
```

This writes `~/.config/tickertape-api-client/credentials.json` for `TickertapeClient.from_env()`.

Browser-assisted capture opens the real Tickertape site, lets you complete the normal login/CAPTCHA/2FA flow yourself, then saves only the resulting Tickertape cookies and visible auth token locally:

```bash
pip install "git+https://github.com/The-Great-One/tickertape-api-client.git#egg=tickertape-api-client[auth]"
python -m playwright install chromium
tickertape auth-capture
```

Credentials are saved to:

```text
~/.config/tickertape-api-client/credentials.json
```

The command does **not** submit your password, bypass 2FA/CAPTCHA, or replicate private login APIs.

### Multi-Account Support

To manage multiple Tickertape accounts (e.g., personal and family), use the
`--account` flag on any CLI command:

```bash
# Capture credentials for different accounts
tickertape auth-browserless --account sahil 7666696636:1234
tickertape auth-browserless --account dad   9888898888:5678

# Use a specific account
tickertape --account sahil portfolio-summary
tickertape --account dad   portfolio-mf

# Set default account via environment variable
export TICKERTAPE_ACCOUNT=sahil
tickertape portfolio-summary  # uses "sahil"
```

The credentials file stores accounts in an `"accounts"` dict:

```json
{
  "accounts": {
    "sahil": {
      "cookie_header": "...",
      "cookie_dict": {"jwt": "...", ...}
    },
    "dad": {
      "cookie_header": "...",
      "cookie_dict": {"jwt": "...", ...}
    }
  }
}
```

Programmatic usage:

```python
from tickertape_api import PortfolioClient, TickertapeClient

# PortfolioClient with named account
with PortfolioClient(account="sahil") as pc:
    print(pc.mf_holdings())

# TickertapeClient with named account
with TickertapeClient.from_env(account="dad") as tt:
    print(tt.screener_screens())
```

The old flat format (top-level `cookie_header` / `cookie_dict` keys) continues
to work and is treated as the default account.

## Endpoint coverage

### Market status

```python
tt.market_status("IN")
tt.market_status("US")
```

Backed by:

```text
GET https://gms-api.tickertape.in/market/{market}/status
```

Useful fields:

- `isOpen`
- `isHoliday`
- `isWeekend`
- `currentWindow`
- `nextWindow`
- `prevWindow`
- `reason`

### Latest quotes

```python
tt.india_quotes(["RELI", ".NSEI"])
tt.us_latest_quotes(["IXIC", "GSPC", "DJI", "AXP"])
tt.forex_latest("USDINR")
```

Backed by:

```text
GET https://quotes-api.tickertape.in/quotes?sids=RELI,.NSEI
GET https://gms-api.tickertape.in/quotes/US/latest?tickers=IXIC,AXP
GET https://gms-api.tickertape.in/quotes/FOREX/latest?tickers=USDINR
```

US quote fields observed:

- `p`: latest price/index level
- `lcp`: last close price
- `v`: volume
- `t`: timestamp in milliseconds
- `s`: symbol

### Indian stocks

```python
tt.stock_info("RELI")
tt.stock_summary("RELI")
tt.stock_intra_chart("RELI")
tt.stock_inter_chart("RELI", start=1748442493416, end=1779978493416)
tt.stock_news("RELI")
tt.stock_checklists("RELI")
tt.stock_financials("RELI", statement="income", period="annual", view="normal")
```

### US securities

```python
tt.us_asset_info(["AAPL", "MSFT"])
tt.us_asset_info(["VOO", "GLD"], asset_type="etfs")
tt.us_stock_overview("AAPL")
tt.us_etf_overview("VOO")
tt.us_chart("AAPL", "1D")   # intraday, maps to duration=1d
tt.us_chart("AAPL", "5Y")   # historical, maps to duration=5y
tt.us_security_chart("AXP", duration="1y")
tt.us_security_chart("AAPL", duration="5y")
tt.us_financials("AAPL", "income")
tt.us_financials("AAPL", "balancesheet")
tt.us_financials("AAPL", "cashflow")
tt.us_filters()
```

Backed by:

```text
GET https://gms-api.tickertape.in/US/securities/info?ticker=AAPL,MSFT
GET https://gms-api.tickertape.in/US/etfs/info?ticker=VOO,GLD
GET https://gms-api.tickertape.in/US/securities/AAPL/overview
GET https://gms-api.tickertape.in/US/etfs/VOO/overview
GET https://gms-api.tickertape.in/US/securities/AAPL/charts/intra?duration=1d
GET https://gms-api.tickertape.in/US/securities/{ticker}/charts/inter?duration=1y
GET https://gms-api.tickertape.in/US/securities/AAPL/financials/income?view=normal
GET https://gms-api.tickertape.in/US/securities/AAPL/financials/balancesheet?view=normal
GET https://gms-api.tickertape.in/US/securities/AAPL/financials/cashflow?view=normal
GET https://gms-api.tickertape.in/US/filters
```

Observed response fields:

- `marketStatus.start`
- `marketStatus.end`
- `points[].ts`
- `points[].lp`
- `points[].v`
- `h`: high over period
- `l`: low over period
- `r`: return over period

### Mutual funds

```python
# Full MF universe. Search locally by name/isin/mfId.
universe = tt.mutual_funds_list()["universe"]

# Fund details.
tt.mutual_fund_info("M_MAHD")
tt.mutual_fund_summary("M_MAHD")

# Portfolio / holdings — the endpoint you asked for.
holdings = tt.mutual_fund_holdings("M_MAHD")
print(holdings["currentAllocation"][:5])

# Other useful MF endpoints.
tt.mutual_fund_chart("M_MAHD", duration="1y")
tt.mutual_fund_sip_chart("M_MAHD")
tt.mutual_fund_fund_managers("M_MAHD")
tt.mutual_fund_checklists("M_MAHD")
tt.mutual_fund_widget("M_MAHD")
```

The holdings endpoint returns `currentAllocation`. Equity rows include useful fields such as:

```json
{
  "type": "Equity",
  "title": "Reliance Industries Ltd",
  "rating": "Equity",
  "sid": "RELI",
  "ticker": "RELIANCE",
  "slug": "/stocks/reliance-industries-RELI",
  "latest": 7.00779988662863,
  "change3m": 1.4262424028198906
}
```

### Screeners

```python
tt.screener_filters()
tt.screener_prebuilt()
tt.screener_query({"match": {"sector": ["Financials"]}, "sortBy": "marketCap", "sortOrder": -1})

tt.mutual_fund_screener_filters()
tt.mutual_fund_screener_prebuilt()
tt.mutual_fund_screener({"match": {"option": ["Growth"]}, "sortBy": "aum", "sortOrder": -1})
```

Some screener queries may require auth server-side. The client exposes the endpoints but will raise clear `TickertapeHTTPError` / `TickertapeAPIError` if Tickertape rejects a request.

The complete stock screener filter list is documented in [`docs/screener-filters.md`](docs/screener-filters.md), including category, `label`, display name, and premium/locked status.

Premium screener fields can be requested only with a legitimate logged-in Tickertape session that has access to them. The client does not log in, bypass access controls, or store credentials unless you explicitly create a local credentials file or run the browser-assisted `tickertape auth-capture` flow; it only forwards user-supplied auth material:

```python
from tickertape_api import TickertapeClient

# Option 1: pass explicitly
client = TickertapeClient(
    auth_token="<bearer-token>",
    cookie_header="<raw Cookie header from your browser session>",
)

# Option 2: read from env
# export TICKERTAPE_AUTH_TOKEN='...'
# export TICKERTAPE_COOKIE='...'
client = TickertapeClient.from_env()

# Option 3: persistent local credentials file
# mkdir -p ~/.config/tickertape-api-client
# chmod 700 ~/.config/tickertape-api-client
# cat > ~/.config/tickertape-api-client/credentials.json <<'JSON'
# {"auth_token": "...", "cookie_header": "..."}
# JSON
# chmod 600 ~/.config/tickertape-api-client/credentials.json
client = TickertapeClient.from_env()

# Option 4: CLI-only credential setup after manually copying session material
# printf '%s' 'session_cookie_here' | tickertape auth-set --cookie-stdin
# tickertape auth-status
client = TickertapeClient.from_env()

# Option 5: browser-assisted capture of your logged-in session
# pip install "git+https://github.com/The-Great-One/tickertape-api-client.git#egg=tickertape-api-client[auth]"
# python -m playwright install chromium
# tickertape auth-capture
client = TickertapeClient.from_env()

client.screener_query({
    "match": {},
    "sortBy": "mrktCapf",
    "sortOrder": -1,
    "project": ["estrvng"],  # premium: 1Y Forward Revenue Growth
    "offset": 0,
    "count": 10,
})
```

Without access, Tickertape currently returns a clear 403 payload such as `No access for estrvng`.

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

## Error handling

```python
from tickertape_api import TickertapeAPIError, TickertapeHTTPError, TickertapeClient

try:
    TickertapeClient().stock_info("BAD")
except TickertapeHTTPError as exc:
    print(exc.status_code, exc.payload)
except TickertapeAPIError as exc:
    print(exc.payload)
```

## Production guidance

- Treat this as a **public-web-data client**, not an exchange-grade market data feed.
- Cache responses where possible.
- Add retries/backoff in your application layer for batch jobs.
- Keep request rates low.
- Keep Kite / broker / exchange data as the source of truth for trading-critical Indian execution.
- Build fallbacks because endpoints are undocumented and may move or change shape.

## Development

```bash
git clone https://github.com/The-Great-One/tickertape-api-client.git
cd tickertape-api-client
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check .
mypy src
python -m build
```

## License

MIT
