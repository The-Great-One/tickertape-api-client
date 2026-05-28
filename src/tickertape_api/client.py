"""Synchronous client for public Tickertape web endpoints.

These endpoints are reverse-engineered from Tickertape's public web application.
They are undocumented and may change without notice. This package intentionally
ships with conservative defaults: timeouts, browser-like headers, clear errors,
and no credential handling.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, Literal, cast

import httpx

from .exceptions import TickertapeAPIError, TickertapeHTTPError
from .types import JSON, JSONObject

Market = Literal["IN", "US"]


class TickertapeClient:
    """Client for useful public Tickertape endpoints.

    Parameters:
        timeout: Per-request timeout in seconds.
        client: Optional preconfigured ``httpx.Client`` for testing or advanced use.
        user_agent: User-Agent header sent with each request.
    """

    api_base = "https://api.tickertape.in"
    gms_base = "https://gms-api.tickertape.in"
    quotes_base = "https://quotes-api.tickertape.in"
    platform_base = "https://platform-ecosystem.api.tickertape.in"

    def __init__(
        self,
        *,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
        user_agent: str = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 Chrome/125 Safari/537.36 tickertape-api-client/0.1"
        ),
    ) -> None:
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True)
        self._headers = {
            "accept": "application/json,text/plain,*/*",
            "user-agent": user_agent,
            "referer": "https://www.tickertape.in/",
            "origin": "https://www.tickertape.in",
        }

    def close(self) -> None:
        """Close the underlying HTTP client."""

        self._client.close()

    def __enter__(self) -> TickertapeClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        if self._owns_client:
            self.close()

    # ---- low-level helpers -------------------------------------------------

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | Sequence[Any] | None = None,
    ) -> JSONObject:
        """Perform a raw request and return the unwrapped JSON object."""

        response = self._client.request(
            method,
            url,
            params=params,
            json=json_body,
            headers=self._headers,
        )
        payload = self._parse_json(response)
        if response.status_code >= 400:
            message = self._extract_error(payload) or response.reason_phrase
            raise TickertapeHTTPError(response.status_code, message, payload)
        if payload.get("success") is False:
            raise TickertapeAPIError(self._extract_error(payload) or "Tickertape API error", payload)
        return payload

    def get(self, url: str, *, params: Mapping[str, Any] | None = None) -> JSONObject:
        """Raw GET wrapper for endpoints not yet modeled."""

        return self.request("GET", url, params=params)

    def post(self, url: str, *, json_body: Mapping[str, Any] | Sequence[Any] | None = None) -> JSONObject:
        """Raw POST wrapper for endpoints not yet modeled."""

        return self.request("POST", url, json_body=json_body)

    def _data(self, method: str, url: str, **kwargs: Any) -> JSON:
        payload = self.request(method, url, **kwargs)
        return cast(JSON, payload.get("data", payload))

    @staticmethod
    def _parse_json(response: httpx.Response) -> JSONObject:
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise TickertapeAPIError("Tickertape returned non-JSON response", response.text) from exc
        if not isinstance(payload, dict):
            raise TickertapeAPIError("Tickertape returned unexpected JSON shape", payload)
        return payload

    @staticmethod
    def _extract_error(payload: Mapping[str, Any]) -> str | None:
        for key in ("error", "message", "errorType"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        return None

    @staticmethod
    def _csv(values: Sequence[str] | str) -> str:
        if isinstance(values, str):
            return values
        return ",".join(values)

    # ---- market and quotes -------------------------------------------------

    def market_status(self, market: Market = "IN") -> JSON:
        """Return exchange status for a market (``IN`` or ``US``).

        Useful fields include ``isOpen``, ``isHoliday``, ``currentWindow``,
        ``nextWindow`` and ``reason``. Times are UTC ISO strings.
        """

        return self._data("GET", f"{self.gms_base}/market/{market}/status")

    def india_quotes(self, sids: Sequence[str] | str) -> JSON:
        """Return latest Indian stock/index quotes for Tickertape SIDs.

        Example SIDs: ``RELI`` for Reliance, ``.NSEI`` for Nifty 50.
        """

        return self._data("GET", f"{self.quotes_base}/quotes", params={"sids": self._csv(sids)})

    def quote_token(self) -> JSON:
        """Return the quote token endpoint payload used by the web app."""

        return self._data("GET", f"{self.quotes_base}/token")

    def us_latest_quotes(self, tickers: Sequence[str] | str) -> JSON:
        """Return latest US stock/index quotes.

        Examples: ``IXIC``, ``GSPC``, ``DJI``, ``AXP``, ``AAPL``.
        """

        return self._data(
            "GET",
            f"{self.gms_base}/quotes/US/latest",
            params={"tickers": self._csv(tickers)},
        )

    def forex_latest(self, tickers: Sequence[str] | str = "USDINR") -> JSON:
        """Return latest FX quotes, e.g. ``USDINR``."""

        return self._data(
            "GET",
            f"{self.gms_base}/quotes/FOREX/latest",
            params={"tickers": self._csv(tickers)},
        )

    # ---- search ------------------------------------------------------------

    def search(self, text: str) -> JSON:
        """Search Tickertape instruments and brands."""

        return self._data("GET", f"{self.api_base}/search", params={"text": text})

    def suggest(self, text: str) -> JSON:
        """Return search suggestions."""

        return self._data("GET", f"{self.api_base}/search/suggest", params={"text": text})

    # ---- Indian stocks, ETFs, indices -------------------------------------

    def stock_info(self, sid: str) -> JSON:
        return self._data("GET", f"{self.api_base}/stocks/info/{sid}")

    def stock_summary(self, sid: str) -> JSON:
        return self._data("GET", f"{self.api_base}/stocks/summary/{sid}")

    def stock_intra_chart(self, sid: str) -> JSON:
        return self._data("GET", f"{self.api_base}/stocks/charts/intra/{sid}")

    def stock_inter_chart(self, sid: str, *, start: int | None = None, end: int | None = None) -> JSON:
        params = {k: v for k, v in {"start": start, "end": end}.items() if v is not None}
        return self._data("GET", f"{self.api_base}/stocks/charts/inter/{sid}", params=params)

    def stock_news(self, sid: str) -> JSON:
        return self._data("GET", f"{self.api_base}/stocks/news/{sid}")

    def stock_checklists(self, sid: str) -> JSON:
        return self._data("GET", f"{self.api_base}/stocks/investmentChecklists/{sid}")

    def stock_financials(
        self,
        sid: str,
        statement: str = "income",
        period: str = "annual",
        view: str = "normal",
    ) -> JSON:
        return self._data(
            "GET", f"{self.api_base}/stocks/financials/{statement}/{sid}/{period}/{view}"
        )

    def etf_info(self, sid: str) -> JSON:
        return self._data("GET", f"{self.api_base}/etfs/info/{sid}")

    def etf_summary(self, sid: str) -> JSON:
        return self._data("GET", f"{self.api_base}/etfs/summary/{sid}")

    def index_info(self, sid: str) -> JSON:
        return self._data("GET", f"{self.api_base}/indices/info/{sid}")

    def index_constituents(self, sid: str) -> JSON:
        return self._data("GET", f"{self.api_base}/indices/constituents/{sid}")

    # ---- US securities -----------------------------------------------------

    def us_security_chart(self, ticker: str, duration: str = "1y") -> JSON:
        """Return US security historical chart data.

        Observed durations include ``1m``, ``6m``, ``1y`` and likely ``5y``.
        """

        return self._data(
            "GET",
            f"{self.gms_base}/US/securities/{ticker}/charts/inter",
            params={"duration": duration},
        )

    # ---- market mood / product widgets ------------------------------------

    def mmi_now(self) -> JSON:
        """Return Tickertape Market Mood Index current payload."""

        return self._data("GET", f"{self.api_base}/mmi/now")

    def product_tape(self) -> JSON:
        return self._data("GET", f"{self.api_base}/product/tape")

    def product_banners(self) -> JSON:
        return self._data("GET", f"{self.api_base}/product/banners")

    # ---- screeners ---------------------------------------------------------

    def screener_filters(self) -> JSON:
        return self._data("GET", f"{self.api_base}/screener/filters")

    def screener_prebuilt(self) -> JSON:
        return self._data("GET", f"{self.api_base}/screener/prebuilt")

    def screener_query(self, query: Mapping[str, Any]) -> JSON:
        """Run stock screener query. Some queries may require auth server-side."""

        return self._data("POST", f"{self.api_base}/screener/query", json_body=query)

    # ---- mutual funds ------------------------------------------------------

    def mutual_funds_list(self) -> JSON:
        """Return the public mutual-fund universe list.

        The response contains a ``universe`` list. Each row includes ``mfId``,
        ISIN, slug, name, fullName, sector, subsector and option.
        """

        return self._data("GET", f"{self.api_base}/mutualfunds/list")

    def mutual_fund_info(self, mf_id: str) -> JSON:
        return self._data("GET", f"{self.api_base}/mutualfunds/{mf_id}/info")

    def mutual_fund_summary(self, mf_id: str) -> JSON:
        return self._data("GET", f"{self.api_base}/mutualfunds/{mf_id}/summary")

    def mutual_fund_holdings(self, mf_id: str) -> JSON:
        """Return a fund portfolio/holdings payload.

        The useful field is ``currentAllocation``. Equity rows include fields
        like ``title``, ``ticker``, ``sid``, ``slug``, ``latest`` (weight %) and
        ``change3m``. The payload also includes allocation history and sector /
        asset-class breakdowns when available.
        """

        return self._data("GET", f"{self.api_base}/mutualfunds/{mf_id}/holdings")

    def mutual_fund_chart(self, mf_id: str, duration: str = "1y") -> JSON:
        return self._data(
            "GET",
            f"{self.api_base}/mutualfunds/{mf_id}/charts/inter",
            params={"duration": duration},
        )

    def mutual_fund_sip_chart(self, mf_id: str) -> JSON:
        return self._data("GET", f"{self.api_base}/mutualfunds/{mf_id}/charts/sip")

    def mutual_fund_fund_managers(self, mf_id: str) -> JSON:
        return self._data("GET", f"{self.api_base}/mutualfunds/{mf_id}/fundmanagers")

    def mutual_fund_checklists(self, mf_id: str) -> JSON:
        return self._data("GET", f"{self.api_base}/mutualfunds/{mf_id}/investmentChecklists")

    def mutual_fund_widget(self, mf_id: str) -> JSON:
        return self._data("GET", f"{self.api_base}/mutualfunds/{mf_id}/widget")

    def mutual_fund_screener_filters(self) -> JSON:
        return self._data("GET", f"{self.api_base}/mf-screener/filters")

    def mutual_fund_screener_prebuilt(self) -> JSON:
        return self._data("GET", f"{self.api_base}/mf-screener/prebuilt")

    def mutual_fund_screener(self, query: Mapping[str, Any]) -> JSON:
        """Run mutual-fund screener query. Some queries may require auth server-side."""

        return self._data("POST", f"{self.api_base}/mf-screener/query", json_body=query)

    # ---- smallcase/platform -----------------------------------------------

    def platform_smallcase_widget(self, types: Sequence[str] | str = ("fd", "smallcases")) -> JSON:
        return self._data(
            "GET",
            f"{self.platform_base}/widget/smallcase",
            params={"types": self._csv(types)},
        )
