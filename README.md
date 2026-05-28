# tickertape-api-client

A production-ready Python client for useful **public Tickertape web endpoints**.

It covers Indian equities, US stocks/indexes, market status, market mood, screeners, ETFs, indices, and mutual funds — including the useful mutual-fund portfolio/holdings endpoint:

```text
GET https://api.tickertape.in/mutualfunds/{mfId}/holdings
```

> **Important:** These are undocumented public web-app endpoints reverse-engineered from Tickertape's website. They can change without notice. Use sensible rate limits, caching, and fallbacks. This package does **not** bypass auth, scrape private user data, or include credentials.

## Installation

```bash
pip install tickertape-api-client
```

From GitHub:

```bash
pip install git+https://github.com/The-Great-One/tickertape-api-client.git
```

## Quick start

```python
from tickertape_api import TickertapeClient

with TickertapeClient() as tt:
    print(tt.market_status("IN"))
    print(tt.india_quotes(["RELI", ".NSEI"]))
    print(tt.us_latest_quotes(["IXIC", "AXP", "AAPL"]))
    print(tt.us_security_chart("AXP", duration="1y"))
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
tt.us_security_chart("AXP", duration="1y")
tt.us_security_chart("AAPL", duration="5y")
```

Backed by:

```text
GET https://gms-api.tickertape.in/US/securities/{ticker}/charts/inter?duration=1y
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
