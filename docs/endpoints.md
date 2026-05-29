# Endpoint Map — Complete API Surface

A comprehensive inventory of every public Tickertape API endpoint discovered from production JS bundles (2026-05-29). Organized by host and category, with auth requirements, path parameters, and usage notes.

> **Important:** These are undocumented web-app endpoints reverse-engineered from Tickertape's production Next.js bundles. They can change without notice. This package does not bypass auth, scrape private user data, or include credentials.

## Host Architecture

Tickertape operates a microservice-style backend. Each subdomain serves a distinct purpose:

| Host | Purpose | Auth |
|------|---------|------|
| `api.tickertape.in` | Primary REST API — screener, portfolio, holdings, watchlists, user, trading, MF, social | Cookie/Token |
| `quotes-api.tickertape.in` | Real-time quotes (Socket.IO + REST) | No (public) |
| `gms-api.tickertape.in` | Global Market Service — US stocks, indices, forex, market status | No (public) |
| `auth.api.tickertape.in` | Authentication — OTP, social login, broker connect, session management | Per-endpoint |
| `community.api.tickertape.in` | Community/Social — posts, comments, polls, feeds | Per-endpoint |
| `channels.api.tickertape.in` | Channels/notifications | Cookie/Token |
| `analyze.api.tickertape.in` | Stock analysis / fundamentals | Cookie/Token |
| `gold.api.tickertape.in` | Digital Gold orders | Cookie/Token |
| `ecosystem.api.tickertape.in` | Smallcase ecosystem integrations | Cookie/Token |
| `payments.api.tickertape.in` | Payments / billing | Cookie/Token |
| `platform-ecosystem.api.tickertape.in` | Platform-wide ecosystem services | Cookie/Token |
| `assets.tickertape.in` | Static assets — logos, images, AMC icons | No |

Stage / pre-production hosts: `stag.tickertape.in`, `gms-api-stag.tickertape.in`

`*.prod.tickertape.in` variants (`api.prod`, `auth-api.prod`, `analyze-api.prod`, `channels-api.prod`, `community-api.prod`, `gold-api.prod`) exist but the non-prod subdomains are the live production URLs.

---

## `api.tickertape.in` — Main REST API

Base: `https://api.tickertape.in`

### Stocks & Market Data

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/search/suggest` | Search suggestions for stocks, MFs, indices | No |
| `GET` | `/stocks/feed/:sid` | Live stock feed (price, change, volume) | No |
| `GET` | `/stocks/summary/:sid` | Stock summary card (sector, mcap, ratios) | No |
| `GET` | `/v2/stocks/feed/:sid` | Stock feed v2 | No |
| `GET` | `/v2/stocks/summary/:sid` | Stock summary v2 | No |
| `GET` | `/quotes` | Current quotes for one or more sids | No |
| `GET` | `/quotes/:market/latest` | Latest quotes for a market | No |
| `GET` | `/market/:market/status` | Market open/holiday status (IN, US) | No |

### Market Mood, Movers & Homepage

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/market-mood-index` | Market Mood Index (MMI) | No |
| `GET` | `/market-mood-index/[component]` | Individual MMI component | No |
| `GET` | `/market-movers` | Top movers page data | No |
| `GET` | `/market-movers/` | Market movers alternate | No |
| `GET` | `/market-movers/deals` | Deal activity | No |
| `GET` | `/market-movers/insights/[iType]` | Market insights by type | No |
| `GET` | `/market-sectors` | Sector overview / heatmap | No |
| `GET` | `/homepage/events` | Homepage market events | No |
| `GET` | `/homepage/indices` | Homepage indices data | No |
| `GET` | `/homepage/mmi` | Homepage MMI widget | No |
| `GET` | `/homepage/portfolio` | Homepage portfolio summary | Token |
| `GET` | `/homepage/portfolio/v2` | Homepage portfolio summary v2 | Token |
| `GET` | `/homepage/stocks` | Homepage stock cards | No |
| `GET` | `/v2/homepage/events` | Homepage events v2 | No |

### Equity Screener

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/screener` | Screener SSR page data | No |
| `GET` | `/screener/[[...path]]` | Catch-all screener route | No |
| `GET` | `/screener-blogs` | Screener blog content | No |
| `GET` | `/screener-canonical-url-mappings` | SEO canonical URL map | No |
| `GET` | `/screener/filters` | All available filter definitions (categories, labels, metadata) | No |
| `GET` | `/screener/prebuilt` | Prebuilt screen definitions | No |
| `GET` | `/screener/v2/prebuilt` | Prebuilt screens v2 | No |
| `GET` | `/screener/universes` | Available stock universes | No |
| `GET` | `/screener/customFilters` | User's custom filter definitions | Token |
| `GET` | `/screener/customFilters/:id` | Specific custom filter | Token |
| `GET` | `/screener/customFilters/bounds` | Filter boundary (min/max) metadata | No |
| `GET` | `/screener/customUniverses` | User's custom universe definitions | Token |
| `GET` | `/screener/customUniverses/:id` | Specific custom universe | Token |
| `POST` | `/screener/query` | Execute screener query — filter labels in [`screener-filters.md`](screener-filters.md) | No (premium fields need Token) |
| `GET` | `/screener/screens` | List saved screens | Token |
| `GET` | `/screener/screens/:id` | Specific saved screen | Token |
| `GET` | `/screener/screens/load/:screenId` | Load a screen's config | Token |
| `GET` | `/screener/screens/load/default` | Load default screen | No |
| `GET` | `/screener/screens/metadata` | Screen metadata | Token |
| `GET` | `/screener/screens/user/:handle` | User's public screens | No |
| `GET` | `/screener/equity/allscreens` | All equity screens (public + user) | Token |
| `GET` | `/screener/mutual-fund/allscreens` | All MF screens | Token |
| `GET` | `/screener/home/equity` | Screener equity homepage | No |
| `GET` | `/screener/home/mutual-fund` | Screener MF homepage | No |
| `GET` | `/screener/export` | Export screener results to CSV/Excel | Token |
| `GET` | `/screener/exportLimit` | Check export limits | Token |
| `GET` | `/screener/external` | External screener integrations | Token |
| `GET` | `/screener/widget/mutual-fund` | MF screener widget | No |

### Mutual Fund Screener

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/mf-screener/filters` | MF filter definitions | No |
| `GET` | `/mf-screener/prebuilt` | MF prebuilt screens | No |
| `GET` | `/mf-screener/v2/prebuilt` | MF prebuilt screens v2 | No |
| `GET` | `/mf-screener/universes` | MF stock universes | No |
| `GET` | `/mf-screener/customFilters` | User's custom MF filters | Token |
| `GET` | `/mf-screener/customFilters/:id` | Specific custom MF filter | Token |
| `GET` | `/mf-screener/customFilters/bounds` | MF filter bounds metadata | No |
| `GET` | `/mf-screener/customUniverses` | User's custom MF universes | Token |
| `GET` | `/mf-screener/customUniverses/:id` | Specific custom MF universe | Token |
| `POST` | `/mf-screener/query` | Execute MF screener query | No |
| `GET` | `/mf-screener/screens` | List saved MF screens | Token |
| `GET` | `/mf-screener/screens/:id` | Specific MF screen | Token |
| `GET` | `/mf-screener/screens/load/:screenId` | Load MF screen config | Token |
| `GET` | `/mf-screener/screens/load/default` | Load default MF screen | No |
| `GET` | `/mf-screener/screens/metadata` | MF screen metadata | Token |
| `GET` | `/mf-screener/screens/user/:handle` | User's public MF screens | No |
| `GET` | `/mf-screener/export` | Export MF screener results | Token |
| `GET` | `/mf-screener/exportLimit` | Check MF export limits | Token |

### Portfolio (Read-only views)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/portfolio` | Portfolio SSR page data | Token |
| `GET` | `/portfolio/[[...path]]` | Catch-all portfolio route | Token |
| `GET` | `/portfolio/equity` | Equity portfolio view | Token |
| `GET` | `/portfolio/mutualfunds` | MF portfolio view | Token |
| `GET` | `/portfolio/mutualfunds/contribution` | MF contribution breakdown | Token |
| `GET` | `/portfolio/us-stocks` | US stocks portfolio view | Token |
| `GET` | `/portfolio/useq` | US equity portfolio (alternate) | Token |
| `GET` | `/portfolio/useq/contribution` | US equity contribution breakdown | Token |
| `GET` | `/portfolio/holdings/status` | Holdings sync status | Token |
| `GET` | `/portfolio/holdings/gateway/mutualFunds/init` | Init MF holdings gateway | Token |
| `GET` | `/portfolio/v2/holdings/:id` | Holdings detail v2 | Token |
| `GET` | `/portfolio/v2/holdings/status` | Holdings status v2 | Token |
| `GET` | `/portfolio/v3/holdings/status` | Holdings status v3 | Token |
| `GET` | `/portfolio/v2/scores/:id` | Portfolio score v2 | Token |
| `GET` | `/portfolio/scores` | Portfolio scores | Token |
| `GET` | `/portfolio/metrics` | Portfolio metrics | Token |
| `GET` | `/portfolio/redflags` | Portfolio red flags | Token |
| `GET` | `/portfolio/insights/diversificationScore` | Diversification score | Token |
| `GET` | `/portfolio/insights/forecast` | Portfolio forecast | Token |
| `GET` | `/portfolio/widget/brokers/config` | Broker widget config | Token |

### User Data (profile, holdings, watchlists)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/user/profile` | User profile | Token |
| `GET` | `/user/status` | User account status | Token |
| `GET` | `/user/subscription` | User subscription/plan details | Token |
| `GET` | `/user/flags` | Feature flags | Token |
| `GET` | `/user/setFlag` | Set a feature flag | Token |
| `GET` | `/user/dismissed` | Dismissed notifications/CTAs | Token |
| `GET` | `/user/bank` | Linked bank accounts | Token |
| `GET` | `/user/holdings` | All holdings | Token |
| `GET` | `/user/holdings/:sid` | Holdings for a specific stock | Token |
| `GET` | `/user/holdings/commentary` | Holdings commentary/analysis | Token |
| `GET` | `/user/holdings/contribution` | Holdings contribution | Token |
| `GET` | `/user/holdings/report` | Holdings report card | Token |
| `GET` | `/user/mfholdings` | MF holdings | Token |
| `GET` | `/user/mfholdings/commentary` | MF holdings commentary | Token |
| `GET` | `/user/mfholdings/disconnect` | Disconnect MF holdings | Token |
| `GET` | `/user/mfholdings/report` | MF holdings report | Token |
| `GET` | `/user/mfHoldings/insights/diversificationScore` | MF diversification score | Token |
| `GET` | `/user/mutualfunds/creditlimit/v2` | MF credit limit v2 | Token |
| `GET` | `/user/credit/combined/v3` | Combined credit v3 | Token |
| `GET` | `/user/credit/summary` | Credit summary | Token |
| `GET` | `/user/keyRatios` | Key financial ratios for holdings | Token |
| `GET` | `/user/basket` | Basket/wishlist | Token |
| `GET` | `/user/basket/securities/:sid` | Add/remove security from basket | Token |
| `GET` | `/user/applyOffer` | Apply an offer/promo | Token |
| `GET` | `/user/downgrade` | Plan downgrade options | Token |
| `GET` | `/user/trialEligibility` | Check trial eligibility | Token |
| `GET` | `/user/searchHistory` | User's search history | Token |
| `GET` | `/user/resendVerification` | Resend email/mobile verification | Token |
| `GET` | `/user/pan/verify` | PAN verification | Token |
| `GET` | `/user/pan/confirm` | PAN confirmation | Token |
| `GET` | `/user/order/init` | Initiate order | Token |
| `GET` | `/user/loan` | Loan/leverage details | Token |
| `GET` | `/user/loan/token` | Loan token | Token |
| `GET` | `/user/loan/token/v2` | Loan token v2 | Token |
| `GET` | `/user/usequity/delink` | Delink US equity account | Token |
| `GET` | `/user/usequity/token` | US equity token | Token |
| `GET` | `/users/:id/memberships` | User membership details | Token |
| `GET` | `/users/config` | User configuration | Token |
| `GET` | `/users/handle/:handle/status` | Check handle availability | No |
| `GET` | `/users/stock/import/init` | Initiate stock import (SC/Kite) | Token |
| `GET` | `/users/stock/import/refetch` | Refetch imported stocks | Token |
| `GET` | `/users/stock/import/status` | Check import status | Token |

### Watchlists

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/watchlists` | List all watchlists | Token |
| `GET` | `/watchlists/:watchlistId` | Specific watchlist | Token |
| `GET` | `/watchlists/:watchlistId/constituents` | Watchlist contents | Token |
| `GET` | `/watchlists/:id/addToBasket` | Add watchlist item to basket | Token |
| `GET` | `/watchlists/data` | Aggregated watchlist data | Token |
| `GET` | `/watchlists/tabs` | Watchlist tab configuration | Token |
| `GET` | `/watchlists/tabs/:key` | Specific tab by key | Token |
| `GET` | `/watchlists/tabs/:tab` | Specific tab | Token |

### Trading & Broker

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/broker/application/status` | Broker application status | Token |
| `GET` | `/api/v1/remittances` | Fund remittances | Token |
| `GET` | `/api/v1/trades` | List trades | Token |
| `GET` | `/api/v1/trades/:tradeId` | Trade detail | Token |
| `POST` | `/api/v1/trades/:tradeId/cancel` | Cancel trade | Token |
| `GET` | `/api/v1/trades/config` | Trading configuration | Token |
| `POST` | `/api/v1/trades/preview` | Preview trade | Token |
| `GET` | `/gateway/connect/init` | Init broker gateway connection | Token |
| `GET` | `/gateway/holdings/init` | Init holdings gateway | Token |
| `GET` | `/gateway/holdings/init/:id` | Holdings gateway for specific broker | Token |
| `GET` | `/gateway/holdings/mutualFunds/init` | MF holdings gateway | Token |
| `GET` | `/gateway/token` | Broker gateway token | Token |
| `GET` | `/gateway/token/:id` | Gateway token for specific broker | Token |
| `GET` | `/holdings/scConnectTokenUrl` | Smallcase connect token URL | Token |
| `GET` | `/holdings/scConnectTokenUrl/v2` | Smallcase connect token URL v2 | Token |

### Portfolio V1 API (api/v1/users)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/users/portfolio` | Portfolio overview v1 | Token |
| `GET` | `/api/v1/users/commission` | Broker commission details | Token |
| `GET` | `/api/v1/users/fund-history` | Fund transaction history | Token |
| `GET` | `/api/v1/users/funds` | Available funds | Token |
| `GET` | `/api/v1/users/holdings/:ticker` | Holdings for a ticker v1 | Token |
| `GET` | `/api/v1/users/order-history` | Order history | Token |
| `GET` | `/api/v1/users/tax-documents` | Tax documents list | Token |
| `GET` | `/api/v1/users/tax-documents/download-options` | Tax document download options | Token |

---

## `auth.api.tickertape.in` — Authentication

Base: `https://auth.api.tickertape.in`

### Email Auth

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/email/sendOTP` | Send OTP to email |
| `POST` | `/auth/email/sendOTP/V3` | Send OTP v3 |
| `POST` | `/auth/email/verifyOTP` | Verify email OTP |
| `POST` | `/auth/email/verifyOTP/V3` | Verify email OTP v3 |
| `POST` | `/auth/email/social` | Social auth via email |
| `POST` | `/auth/email/tokenLogin` | Token-based email login |
| `POST` | `/auth/emailLogin` | Email/password login |
| `GET` | `/auth/emailStatus` | Check email verification status |

### Mobile Auth

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/mobile/sendOTP` | Send OTP to mobile |
| `POST` | `/auth/mobile/sendOTP/V2` | Send OTP v2 |
| `POST` | `/auth/mobile/sendOtp` | Send OTP (camelCase variant) |
| `POST` | `/auth/mobile/verifyOTP` | Verify mobile OTP |
| `POST` | `/auth/mobile/verifyOTP/V2` | Verify OTP v2 |
| `POST` | `/auth/mobile/verifyOtp` | Verify OTP (camelCase variant) |
| `POST` | `/auth/mobileLogin/V3` | Mobile login v3 |

### Login & Session

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/login` | Login |
| `POST` | `/auth/login/V2` | Login v2 |
| `POST` | `/auth/login/V3` | Login v3 |
| `POST` | `/auth/logout` | Logout |
| `POST` | `/auth/token` | Get auth token |
| `POST` | `/auth/refresh` | Refresh session token |
| `POST` | `/auth/extendSession` | Extend session |
| `POST` | `/auth/verify` | Verify session |
| `GET` | `/auth/user/v2` | Authenticated user info v2 |

### Social & Broker Connect

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/socialLogin` | Social login (Google/Apple) |
| `POST` | `/auth/socialLogin/V3` | Social login v3 |
| `POST` | `/auth/connectSocial` | Connect social account |
| `POST` | `/auth/disconnectSocial` | Disconnect social account |
| `POST` | `/auth/connectBroker` | Connect broker (Zerodha, etc.) |
| `POST` | `/auth/connectBroker/v2` | Connect broker v2 |
| `POST` | `/auth/disconnectBroker` | Disconnect broker |
| `POST` | `/auth/disconnectBroker/v2/:id` | Disconnect specific broker v2 |
| `POST` | `/auth/disconnectSecondaryBrokers` | Disconnect all secondary brokers |

### Gateway & Misc

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/gateway` | Auth gateway |
| `POST` | `/auth/gatewayLogin` | Gateway login |
| `GET` | `/auth/lspToken` | LSP token |
| `POST` | `/auth/otp` | Generic OTP endpoint |
| `GET` | `/api/` | API health / root |

---

## `gms-api.tickertape.in` — Global Market Service

Base: `https://gms-api.tickertape.in`

These endpoints are already wrapped by `TickertapeClient` methods:

| Method | Path | Client Method | Description |
|--------|------|---------------|-------------|
| `GET` | `/market/{market}/status` | `.market_status("IN")` / `("US")` | Market open/close/holiday status |
| `GET` | `/quotes/US/latest?tickers=AAPL,MSFT` | `.us_latest_quotes(["AAPL", "MSFT"])` | US stock/index latest quotes |
| `GET` | `/quotes/FOREX/latest?tickers=USDINR` | `.forex_latest("USDINR")` | Forex quotes |
| `GET` | `/US/securities/info?ticker=AAPL,MSFT` | `.us_asset_info(["AAPL", "MSFT"])` | US security info |
| `GET` | `/US/etfs/info?ticker=VOO,GLD` | `.us_asset_info(["VOO", "GLD"], asset_type="etfs")` | US ETF info |
| `GET` | `/US/securities/{ticker}/overview` | `.us_stock_overview("AAPL")` | US stock overview |
| `GET` | `/US/etfs/{ticker}/overview` | `.us_etf_overview("VOO")` | US ETF overview |
| `GET` | `/US/securities/{ticker}/charts/intra?duration=1d` | `.us_chart("AAPL", "1D")` | US intraday chart |
| `GET` | `/US/securities/{ticker}/charts/inter?duration=1y` | `.us_security_chart("AXP", duration="1y")` | US historical chart |
| `GET` | `/US/securities/{ticker}/financials/income?view=normal` | `.us_financials("AAPL", "income")` | US income statement |
| `GET` | `/US/securities/{ticker}/financials/balancesheet?view=normal` | `.us_financials("AAPL", "balancesheet")` | US balance sheet |
| `GET` | `/US/securities/{ticker}/financials/cashflow?view=normal` | `.us_financials("AAPL", "cashflow")` | US cash flow |
| `GET` | `/US/filters` | `.us_filters()` | US stock filter definitions |

---

## `quotes-api.tickertape.in` — Real-time Quotes

Base: `https://quotes-api.tickertape.in`

### REST

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/quotes?sids=RELI,.NSEI` | Batch quote request — returns current price, change, volume for comma-separated security IDs |

### WebSocket (Socket.IO)

Tickertape uses Socket.IO over WebSocket transport for real-time streaming:

- **Server:** `quotes-api.tickertape.in`
- **Transports:** `websocket`, `polling`
- **Namespace:** `/quotes?sids=<comma-separated-sids>`

In-app Socket.IO route paths:
- `/stocks` — Live stock ticks
- `/screener` — Screener result updates
- `/portfolio` — Portfolio value changes
- `/mutualfunds` — MF NAV updates
- `/indices` — Index ticks
- `/etfs` — ETF ticks
- `/pricing` — Pricing updates
- `/market-mood-index` — MMI real-time
- `/us-stocks` — US stock ticks
- `/profile` — User profile updates
- `/space` — Spaces/rooms
- `/social-pricing` — Social feed pricing

---

## Social / Community Endpoints

### `community.api.tickertape.in` — Community

Base: `https://community.api.tickertape.in`

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/social` | Social feed | Token |
| `GET` | `/v2/posts` | Posts list v2 | Token |
| `GET` | `/v3/posts` | Posts list v3 | Token |
| `GET` | `/posts/:postID` | Single post | Token |
| `GET` | `/v3/posts/:postID` | Single post v3 | Token |
| `GET` | `/v2/comments` | Comments list v2 | Token |
| `GET` | `/v2/comments/:commentID` | Single comment v2 | Token |
| `GET` | `/comments/:commentID` | Single comment v1 | Token |
| `POST` | `/comments/share` | Share a comment | Token |
| `GET` | `/v2/polls` | Polls list v2 | Token |
| `GET` | `/v2/polls/:id` | Single poll v2 | Token |
| `POST` | `/polls/vote` | Vote on a poll | Token |
| `GET` | `/v3/feeds` | User feed v3 | Token |

---

## WebSocket Streams

Tickertape's real-time data layer uses Socket.IO over WebSocket transport. The server is `quotes-api.tickertape.in` with namespace templates like `/quotes?sids=<comma-separated-ids>`.

In the JS bundles, Socket.IO client connects to these route paths within the app:
`/stocks`, `/screener`, `/portfolio`, `/mutualfunds`, `/indices`, `/etfs`, `/pricing`, `/market-mood-index`, `/us-stocks`, `/profile`, `/space`, `/social-pricing`

These are app-route paths that trigger Socket.IO namespace connections, not Socket.IO namespaces themselves. The actual namespace is constructed programmatically at connection time.

---

## Analytics / Third-party

| URL | Purpose |
|-----|---------|
| `https://api2.amplitude.com/2/httpapi` | Amplitude event tracking |
| `https://api2.amplitude.com/batch` | Amplitude batch events |
| `https://tickertape-d9bd1.firebaseio.com` | Firebase Realtime Database |

---

## Auth Requirements

**Public (no auth):**
- Stocks, quotes, market status, MMI, market movers, sectors
- Screener filters, prebuilt screens, MF screener filters/prebuilt
- US stock data via GMS API
- Search suggestions
- Handle availability check

**Authenticated (cookie/token required):**
- Portfolio data, holdings, watchlists
- User profile, subscriptions, feature flags
- Trading, broker connections, remittances
- Custom filters, custom universes, saved screens
- Premium screener fields (403 without valid subscription)
- Social feed, posts, comments, polls
- Screen export

**Setup:**
```bash
# CLI credential setup (for already-copied session material)
printf '%s' 'session_cookie_here' | tickertape auth-set --cookie-stdin

# Browser-assisted capture (opens Tickertape, you log in manually)
pip install "git+https://github.com/The-Great-One/tickertape-api-client.git#egg=tickertape-api-client[auth]"
python -m playwright install chromium
tickertape auth-capture
```

Credentials stored at `~/.config/tickertape-api-client/credentials.json` with `0600` permissions.

### Python usage

```python
from tickertape_api import TickertapeClient

# Public endpoints
with TickertapeClient() as tt:
    tt.market_status("IN")
    tt.india_quotes(["RELI", ".NSEI"])
    tt.us_latest_quotes(["IXIC", "AAPL"])
    tt.mmi_now()
    tt.screener_filters()               # all filter labels
    tt.screener_query({"match": {"sector": ["Financials"]}, "sortBy": "marketCap", "sortOrder": -1})

# Authenticated endpoints
client = TickertapeClient.from_env()
client.screener_query({
    "match": {},
    "sortBy": "mrktCapf",
    "sortOrder": -1,
    "project": ["estrvng"],  # premium: 1Y Forward Revenue Growth
    "offset": 0,
    "count": 10,
})
client.stock_holdings("RELI")
client.watchlists()

# PortfolioClient (for direct portfolio endpoint access)
from tickertape_api import PortfolioClient
p = PortfolioClient.from_env()
p.get_holdings()
p.get_scores()
p.get_redflags()
```

---

## Rate Limits & Production Guidance

- Endpoints are undocumented web-app internals — they can change shape or move without notice
- Rate limits are not published; keep request rates low (similar to browser usage)
- Cache responses where possible; add retries with backoff for batch jobs
- Build fallbacks: use Kite/broker data as source of truth for trading-critical execution
- Premium screener fields return 403 (`No access for <label>`) without a valid subscription session

See the [README](../README.md) for full installation and usage, and [`screener-filters.md`](screener-filters.md) for the complete filter label reference.
