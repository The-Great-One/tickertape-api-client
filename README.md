<div align="center">

<img src="icon.png" alt="tickertape-api-client logo" width="120" height="120" />

# tickertape-api-client

**Python client for Tickertape public and authenticated portfolio APIs.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/The-Great-One/tickertape-api-client)](https://github.com/The-Great-One/tickertape-api-client/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/The-Great-One/tickertape-api-client)](https://github.com/The-Great-One/tickertape-api-client/pulls)
[![GitHub stars](https://img.shields.io/github/stars/The-Great-One/tickertape-api-client?style=social)](https://github.com/The-Great-One/tickertape-api-client/stargazers)

[Report Bug](https://github.com/The-Great-One/tickertape-api-client/issues/new?template=bug_report.md) · [Request Feature](https://github.com/The-Great-One/tickertape-api-client/issues/new?template=feature_request.md)

</div>

---

## Table of Contents

- [About](#about)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Acknowledgments](#acknowledgments)

---

## About

`tickertape-api-client` is a Python client for Tickertape's public market data
and authenticated portfolio APIs. Includes Indian stocks, US securities, mutual
funds, screeners, ETFs, indices, and portfolio holdings. Public endpoints work
without auth; portfolio endpoints require a browser-captured session.

## Features

- ✅ Public market data (stocks, MFs, screeners, US, ETFs, indices)
- ✅ Authenticated portfolio (holdings, summary, watchlists)
- ✅ Multi-account support
- ✅ Automatic JWT refresh (no relogin for days/weeks)
- ✅ Browser-assisted credential capture (Playwright)
- ✅ 227+ endpoints across 4 hosts
- ✅ Error handling (TickertapeAPIError, TickertapeHTTPError)
- 🚧 Additional endpoints

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

```bash
git clone https://github.com/The-Great-One/tickertape-api-client.git
cd tickertape-api-client
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

For browser-assisted auth capture:

```bash
pip install "tickertape-api-client[auth]"
python -m playwright install chromium
```

## Usage

### Python

```python
from tickertape_api import TickertapeClient

tt = TickertapeClient()
tt.market_status("IN")
tt.india_quotes(["RELI", ".NSEI"])
tt.stock_info("RELI")
tt.stock_inter_chart("RELI", duration="1y")
tt.mutual_fund_info("M_MAHD")
tt.screener_query({"match": {"sector": ["Financials"]}, "sortBy": "marketCap", "sortOrder": -1})
tt.us_chart("AAPL", "1Y")
tt.etf_info("HDFB")
tt.mmi_now()
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

### Authentication

Three options: CLI credential setup (`auth-set`), browser-assisted capture
(`auth-capture`), or programmatic (`TickertapeClient(auth_token=..., cookie_header=...)`
or `from_env()`). Credentials saved to `~/.config/tickertape-api-client/credentials.json`.

The auth commands do **not** submit passwords, bypass 2FA/CAPTCHA, or replicate
private login APIs.

### Session refresh

`PortfolioClient` automatically refreshes the JWT near expiry (~24h) via
`POST https://auth.api.tickertape.in/auth/refresh`, persisting new credentials.
On API 401, it forces a refresh and retries once.

### Multi-account

```bash
tickertape auth-browserless --account primary 9876543210:1234
tickertape --account primary portfolio-summary
export TICKERTAPE_ACCOUNT=primary
```

### Endpoint coverage

Market status, latest quotes, Indian stocks, US securities, mutual funds,
screeners (stock + MF), ETFs, indices, market mood/widgets, portfolio
(authenticated), search. Full inventory (227+ endpoints) in
[`docs/endpoints.md`](docs/endpoints.md).

### Error handling

```python
from tickertape_api import TickertapeAPIError, TickertapeHTTPError, TickertapeClient

try:
    TickertapeClient().stock_info("BAD")
except TickertapeHTTPError as exc:
    print(f"HTTP {exc.status_code}: {exc.payload}")
except TickertapeAPIError as exc:
    print(f"API error: {exc.payload}")
```

### Production guidance

- Treat as a **public-web-data client**, not exchange-grade market data
- Cache responses, add retries/backoff, keep rates low
- Keep Kite/broker/exchange data as source of truth for trading-critical execution
- Build fallbacks (endpoints are undocumented and may change)

## Roadmap

- [x] v0.1 – Public market data client
- [x] v0.1 – Authenticated portfolio client
- [x] v0.1 – Multi-account support
- [ ] v0.2 – Additional endpoints
- [ ] v1.0 – Stable release

See the open issues for the full list of proposed features and known bugs.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and
follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

## Contact

Sahil Goel – [@The-Great-One](https://github.com/The-Great-One) –
sahilgoel187@gmail.com

Project link: [https://github.com/The-Great-One/tickertape-api-client](https://github.com/The-Great-One/tickertape-api-client)

## Acknowledgments

- [Img Shields](https://shields.io)
- [Contributor Covenant](https://www.contributor-covenant.org)
