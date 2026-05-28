# Endpoint map

Useful public endpoints wrapped by this package. Authenticated calls are supported by forwarding user-supplied `TICKERTAPE_AUTH_TOKEN` / `TICKERTAPE_COOKIE` values, or by reading a local `~/.config/tickertape-api-client/credentials.json` file. The client does not obtain credentials or bypass access controls.

## Auth capture

For premium fields, install the optional Playwright extra and capture your own logged-in browser session:

```bash
pip install "git+https://github.com/The-Great-One/tickertape-api-client.git#egg=tickertape-api-client[auth]"
python -m playwright install chromium
tickertape auth-capture
```

This opens the real Tickertape website. You complete login/CAPTCHA/2FA manually, then press Enter in the terminal. The command saves Tickertape cookies and any visible auth token to `~/.config/tickertape-api-client/credentials.json` with `0600` permissions. It does not submit passwords, bypass login controls, or mirror private authentication APIs.

## GMS API

- `GET /market/{market}/status`
- `GET /quotes/US/latest?tickers=IXIC,AXP`
- `GET /quotes/FOREX/latest?tickers=USDINR`
- `GET /US/securities/info?ticker=AAPL,MSFT`
- `GET /US/etfs/info?ticker=VOO,GLD`
- `GET /US/securities/{ticker}/overview`
- `GET /US/etfs/{ticker}/overview`
- `GET /US/securities/{ticker}/charts/intra?duration=1d`
- `GET /US/securities/{ticker}/charts/inter?duration=1y`
- `GET /US/securities/{ticker}/financials/income?view=normal`
- `GET /US/securities/{ticker}/financials/balancesheet?view=normal`
- `GET /US/securities/{ticker}/financials/cashflow?view=normal`
- `GET /US/filters`

## Main API

- `GET /search?text=...`
- `GET /search/suggest?text=...`
- `GET /stocks/info/{sid}`
- `GET /stocks/summary/{sid}`
- `GET /stocks/charts/intra/{sid}`
- `GET /stocks/charts/inter/{sid}`
- `GET /stocks/news/{sid}`
- `GET /stocks/investmentChecklists/{sid}`
- `GET /stocks/financials/{statement}/{sid}/{period}/{view}`
- `GET /etfs/info/{sid}`
- `GET /etfs/summary/{sid}`
- `GET /indices/info/{sid}`
- `GET /indices/constituents/{sid}`
- `GET /mmi/now`
- `GET /screener/filters`
- `GET /screener/prebuilt`
- `POST /screener/query` — filter labels documented in [`screener-filters.md`](screener-filters.md)
- `GET /mutualfunds/list`
- `GET /mutualfunds/{mfId}/info`
- `GET /mutualfunds/{mfId}/summary`
- `GET /mutualfunds/{mfId}/holdings`
- `GET /mutualfunds/{mfId}/charts/inter?duration=1y`
- `GET /mutualfunds/{mfId}/charts/sip`
- `GET /mutualfunds/{mfId}/fundmanagers`
- `GET /mutualfunds/{mfId}/investmentChecklists`
- `GET /mutualfunds/{mfId}/widget`
- `GET /mf-screener/filters`
- `GET /mf-screener/prebuilt`
- `POST /mf-screener/query`
