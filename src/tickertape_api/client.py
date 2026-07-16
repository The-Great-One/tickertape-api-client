"""Synchronous client for public Tickertape web endpoints.

These endpoints are reverse-engineered from Tickertape's public web application.
They are undocumented and may change without notice. This package intentionally
ships with conservative defaults: timeouts, browser-like headers, clear errors,
and optional user-supplied auth forwarding for endpoints that require a
legitimate logged-in/premium session.
"""

from __future__ import annotations

import functools
import json
import os
import threading
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal, cast

import httpx

from .credentials_store import normalize_credential_keys, read_credentials_file
from .exceptions import TickertapeAPIError, TickertapeHTTPError
from .ohlc import Candle, synthesize_ohlc, ohlc_to_list, group_intraday
from .rate_limiter import RateLimiter
from .types import JSON, JSONObject

Market = Literal["IN", "US"]


class TickertapeClient:
    """Client for useful public Tickertape endpoints.

    Parameters:
        timeout: Per-request timeout in seconds.
        client: Optional preconfigured ``httpx.Client`` for testing or advanced use.
        user_agent: User-Agent header sent with each request.
        auth_token: Optional user-supplied Tickertape bearer token for endpoints
            that require a logged-in/premium session. The client never obtains or
            refreshes this token itself.
        cookie_header: Optional raw ``Cookie`` header copied from a legitimate
            logged-in Tickertape browser session.
        extra_headers: Optional additional headers to merge into each request.
    """

    api_base = "https://api.tickertape.in"
    gms_base = "https://gms-api.tickertape.in"
    quotes_base = "https://quotes-api.tickertape.in"
    platform_base = "https://platform-ecosystem.api.tickertape.in"
    auth_base = "https://auth.api.tickertape.in"
    community_base = "https://community.api.tickertape.in"
    channels_base = "https://channels.api.tickertape.in"
    analyze_base = "https://analyze.api.tickertape.in"
    gold_base = "https://gold.api.tickertape.in"
    ecosystem_base = "https://ecosystem.api.tickertape.in"
    payments_base = "https://payments.api.tickertape.in"

    def __init__(
        self,
        *,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
        user_agent: str = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 Chrome/125 Safari/537.36 tickertape-api-client/0.1"
        ),
        auth_token: str | None = None,
        cookie_header: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
        rate_limit: float = 5.0,
        rate_period: float = 1.0,
        cache_ttl: float = 60.0,
    ) -> None:
        self._owns_client = client is None
        self._client = client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        self._headers = {
            "accept": "application/json,text/plain,*/*",
            "user-agent": user_agent,
            "referer": "https://www.tickertape.in/",
            "origin": "https://www.tickertape.in",
        }
        if auth_token:
            token = auth_token.strip()
            self._headers["authorization"] = token if token.lower().startswith("bearer ") else f"Bearer {token}"
        if cookie_header:
            self._headers["cookie"] = cookie_header.strip()
        if extra_headers:
            self._headers.update({key.lower(): value for key, value in extra_headers.items()})
        # Rate limiter — 5 req/s by default, configurable
        self._rate_limiter = RateLimiter(max_calls=rate_limit, period=rate_period)
        # Simple in-memory TTL cache for GET requests
        self._cache: dict[str, tuple[float, JSON]] = {}
        self._cache_ttl = cache_ttl
        self._cache_lock = threading.Lock()

    @classmethod
    def from_env(cls, *, account: str | None = None, **kwargs: Any) -> TickertapeClient:
        """Create a client using optional auth material from environment variables.

        Supported variables:
        - ``TICKERTAPE_AUTH_TOKEN``: bearer token from a legitimate logged-in session.
        - ``TICKERTAPE_COOKIE``: raw Cookie header from a logged-in browser session.
        - ``TICKERTAPE_CREDENTIALS_FILE``: optional JSON file path. Defaults to
          ``~/.config/tickertape-api-client/credentials.json`` when present.
        - ``TICKERTAPE_ACCOUNT``: named account to use from the credentials file's
          ``"accounts"`` dict.

        The credentials file may contain ``auth_token`` and ``cookie_header``
        keys at the top level (flat mode) or under ``"accounts"`` → ``<name>``
        (multi-account mode). Environment variables override file values.
        Keyword arguments override both environment and file values.
        """

        raw_credentials = read_credentials_file(
            os.getenv("TICKERTAPE_CREDENTIALS_FILE"), account=account
        )
        credentials = normalize_credential_keys(raw_credentials)
        kwargs.setdefault(
            "auth_token", os.getenv("TICKERTAPE_AUTH_TOKEN") or credentials.get("auth_token")
        )
        kwargs.setdefault(
            "cookie_header", os.getenv("TICKERTAPE_COOKIE") or credentials.get("cookie_header")
        )
        return cls(**kwargs)

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
        """Perform a raw request and return the unwrapped JSON object.

        GET requests are cached for ``cache_ttl`` seconds (default 60s).
        All requests are rate-limited to respect Tickertape's request limits.
        """

        cache_key = ""
        if method.upper() == "GET":
            cache_key = f"{url}?{sorted(params.items()) if params else ''}"
            with self._cache_lock:
                if cache_key in self._cache:
                    ts, cached = self._cache[cache_key]
                    if time.monotonic() - ts < self._cache_ttl:
                        return cast(JSONObject, cached)

        # Respect rate limits
        self._rate_limiter.acquire()

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
        # Cache successful GET responses
        if cache_key:
            with self._cache_lock:
                self._cache[cache_key] = (time.monotonic(), cast(JSON, payload))
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

    def stock_inter_chart(self, sid: str, *, duration: str = "1y") -> JSON:
        """Return Indian stock inter-day chart data.

        Parameters:
            sid: Tickertape stock SID (e.g. ``RELI``).
            duration: Chart duration — ``1w``, ``1m``, ``3m``, ``6m``, ``1y``,
                ``5y``, ``max``. Default ``1y``.
        """
        return self._data(
            "GET", f"{self.api_base}/stocks/charts/inter/{sid}",
            params={"duration": duration},
        )

    def stock_ohlc(
        self, sid: str, *, duration: str = "1y", frequency: str = "1D",
        adjust_splits: bool = True,
    ) -> list[dict[str, Any]]:
        """Return Indian stock OHLC candles.

        Uses the inter-day chart endpoint. For durations >= 1m, Tickertape
        returns one price point per day (the close), so O=H=L=C for daily
        candles. For ``1w`` duration, Tickertape returns 5-minute intraday
        data, which produces true OHLC with distinct open/high/low/close.

        Parameters:
            sid: Tickertape stock SID (e.g. ``RELI``).
            duration: Chart duration — ``1w``, ``1m``, ``3m``, ``6m``, ``1y``,
                ``5y``, ``max``. Default ``1y``. Use ``1w`` for true intraday OHLC.
            frequency: Candle frequency — ``1D`` (daily), ``1W`` (weekly),
                ``1M`` (monthly). Default ``1D``.
            adjust_splits: If True (default), detect stock splits and adjust
                pre-split prices so the entire series is on a post-split basis.

        Returns:
            List of dicts with ``timestamp``, ``open``, ``high``, ``low``,
            ``close``, ``volume``.
        """
        raw = self.stock_inter_chart(sid, duration=duration)
        candles = synthesize_ohlc(raw, frequency=frequency, adjust_splits=adjust_splits)
        return ohlc_to_list(candles)

    def stock_ohlc_with_splits(
        self, sid: str, *, duration: str = "1y", frequency: str = "1D",
        adjust_splits: bool = True,
    ) -> dict[str, Any]:
        """Return Indian stock OHLC candles with split metadata.

        Like :meth:`stock_ohlc` but also returns detected stock split events.

        Returns:
            Dict with ``candles`` (list of OHLC dicts) and ``splits``
            (list of split events with ``date``, ``ratio``, ``old_price``,
            ``new_price``).
        """
        from .ohlc import synthesize_ohlc_with_splits
        raw = self.stock_inter_chart(sid, duration=duration)
        result = synthesize_ohlc_with_splits(raw, frequency=frequency, adjust_splits=adjust_splits)
        return result.as_dict()

    def stock_intraday_ohlc(self, sid: str, *, adjust_splits: bool = True) -> list[dict[str, Any]]:
        """Return today's intraday OHLC candles (5-minute granularity).

        Fetches the intraday chart and groups by 5-minute intervals to
        produce candles with distinct open/high/low/close within the session.

        Parameters:
            sid: Tickertape stock SID.
            adjust_splits: If True (default), detect and adjust for stock splits.
        """
        raw = self.stock_intra_chart(sid)
        candles = group_intraday(raw, interval_minutes=5, adjust_splits=adjust_splits)
        return ohlc_to_list(candles)

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

    def us_asset_info(
        self, tickers: Sequence[str] | str, *, asset_type: Literal["securities", "etfs"] = "securities"
    ) -> JSON:
        """Return bulk US asset metadata for stocks/securities or ETFs."""

        return self._data(
            "GET",
            f"{self.gms_base}/US/{asset_type}/info",
            params={"ticker": self._csv(tickers)},
        )

    def us_stock_overview(self, ticker: str) -> JSON:
        """Return US stock overview: profile, metrics, labels, holdings and peers."""

        return self._data("GET", f"{self.gms_base}/US/securities/{ticker}/overview")

    def us_etf_overview(self, ticker: str) -> JSON:
        """Return US ETF overview, including top holdings and peers when available."""

        return self._data("GET", f"{self.gms_base}/US/etfs/{ticker}/overview")

    def us_financials(
        self,
        ticker: str,
        statement: Literal["income", "balancesheet", "cashflow"] = "income",
        *,
        view: str = "normal",
    ) -> JSON:
        """Return US stock financial statements.

        Working statement values observed from the web app are ``income``,
        ``balancesheet`` and ``cashflow``.
        """

        return self._data(
            "GET",
            f"{self.gms_base}/US/securities/{ticker}/financials/{statement}",
            params={"view": view},
        )

    def us_filters(self) -> JSON:
        """Return available US screener/filter metric definitions."""

        return self._data("GET", f"{self.gms_base}/US/filters")

    def us_chart(
        self,
        ticker: str,
        range_: Literal["1D", "1W", "1M", "1Y", "5Y", "MAX"] = "1Y",
        *,
        asset_type: Literal["securities", "etfs"] = "securities",
    ) -> JSON:
        """Return a US stock/ETF chart using Tickertape's UI ranges.

        ``1D`` maps to ``charts/intra?duration=1d``. Other ranges map to
        ``charts/inter`` with lower-case durations: ``1w``, ``1m``, ``1y``,
        ``5y`` and ``max``.
        """

        mapping = {
            "1D": ("intra", "1d"),
            "1W": ("inter", "1w"),
            "1M": ("inter", "1m"),
            "1Y": ("inter", "1y"),
            "5Y": ("inter", "5y"),
            "MAX": ("inter", "max"),
        }
        chart_type, duration = mapping[range_]
        return self._data(
            "GET",
            f"{self.gms_base}/US/{asset_type}/{ticker}/charts/{chart_type}",
            params={"duration": duration},
        )

    def us_security_chart(self, ticker: str, duration: str = "1y") -> JSON:
        """Return US security historical chart data.

        Prefer :meth:`us_chart` for UI-style ranges. This method is retained for
        backwards compatibility and calls ``charts/inter`` directly.
        """

        return self._data(
            "GET",
            f"{self.gms_base}/US/securities/{ticker}/charts/inter",
            params={"duration": duration},
        )

    def us_ohlc(
        self, ticker: str, *, duration: str = "1y", frequency: str = "1D",
        asset_type: Literal["securities", "etfs"] = "securities",
        adjust_splits: bool = True,
    ) -> list[dict[str, Any]]:
        """Return US stock/ETF OHLC candles.

        Fetches the inter-day chart and synthesizes OHLC candles client-side.

        Parameters:
            ticker: US ticker (e.g. ``AAPL``).
            duration: Chart duration — ``1w``, ``1m``, ``1y``, ``5y``, ``max``.
            frequency: Candle frequency — ``1D``, ``1W``, ``1M``.
            asset_type: ``securities`` or ``etfs``.
            adjust_splits: If True (default), detect stock splits and adjust
                pre-split prices so the entire series is on a post-split basis.
        """
        raw = self._data(
            "GET",
            f"{self.gms_base}/US/{asset_type}/{ticker}/charts/inter",
            params={"duration": duration},
        )
        candles = synthesize_ohlc(raw, frequency=frequency, adjust_splits=adjust_splits)
        return ohlc_to_list(candles)

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

    def screener_v2_prebuilt(self) -> JSON:
        """Return v2 prebuilt screens (newer version used by the web app)."""
        return self._data("GET", f"{self.api_base}/screener/v2/prebuilt")

    def screener_query(self, query: Mapping[str, Any]) -> JSON:
        """Run stock screener query. Some queries may require auth server-side."""
        return self._data("POST", f"{self.api_base}/screener/query", json_body=query)

    def screener_export(self, query: Mapping[str, Any]) -> JSON:
        """Export screener results. Requires auth."""
        return self._data("POST", f"{self.api_base}/screener/export", json_body=query)

    def screener_export_limit(self) -> JSON:
        """Return screener export row limit for the current user."""
        return self._data("GET", f"{self.api_base}/screener/exportLimit")

    # Screener — custom filters / universes (auth-required)
    def screener_custom_filters(self) -> JSON:
        """List user's custom screener filters. Requires auth."""
        return self._data("GET", f"{self.api_base}/screener/customFilters")

    def screener_custom_filter(self, filter_id: str) -> JSON:
        """Get a specific custom filter. Requires auth."""
        return self._data("GET", f"{self.api_base}/screener/customFilters/{filter_id}")

    def screener_custom_filter_bounds(self) -> JSON:
        """Return bounds/range info for custom filters. Requires auth."""
        return self._data("GET", f"{self.api_base}/screener/customFilters/bounds")

    def screener_custom_universes(self) -> JSON:
        """List user's custom universes. Requires auth."""
        return self._data("GET", f"{self.api_base}/screener/customUniverses")

    def screener_custom_universe(self, universe_id: str) -> JSON:
        """Get a specific custom universe. Requires auth."""
        return self._data("GET", f"{self.api_base}/screener/customUniverses/{universe_id}")

    def screener_universes(self) -> JSON:
        """Return available screener universes."""
        return self._data("GET", f"{self.api_base}/screener/universes")

    # Screener — saved screens (auth-required)
    def screener_screens(self) -> JSON:
        """List user's saved screener screens. Requires auth."""
        return self._data("GET", f"{self.api_base}/screener/screens")

    def screener_screen(self, screen_id: str) -> JSON:
        """Get a specific saved screen. Requires auth."""
        return self._data("GET", f"{self.api_base}/screener/screens/{screen_id}")

    def screener_screen_load(self, screen_id: str) -> JSON:
        """Load and execute a saved screen. Requires auth."""
        return self._data("GET", f"{self.api_base}/screener/screens/load/{screen_id}")

    def screener_load_default_screen(self) -> JSON:
        """Load the default saved screen. Requires auth."""
        return self._data("GET", f"{self.api_base}/screener/screens/load/default")

    def screener_screen_metadata(self) -> JSON:
        """Return metadata for saved screens. Requires auth."""
        return self._data("GET", f"{self.api_base}/screener/screens/metadata")

    def screener_user_screens(self, handle: str) -> JSON:
        """Return screens shared by a specific user. Requires auth."""
        return self._data("GET", f"{self.api_base}/screener/screens/user/{handle}")

    def screener_all_equity_screens(self) -> JSON:
        """Return all equity screens. Requires auth."""
        return self._data("GET", f"{self.api_base}/screener/equity/allscreens")

    def screener_home_equity(self) -> JSON:
        """Return equity screener homepage data (top screens, popular filters)."""
        return self._data("GET", f"{self.api_base}/screener/home/equity")

    def screener_home_mutual_fund(self) -> JSON:
        """Return MF screener homepage data."""
        return self._data("GET", f"{self.api_base}/screener/home/mutual-fund")

    def screener_external(self) -> JSON:
        """Return external/embedded screener data."""
        return self._data("GET", f"{self.api_base}/screener/external")

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

    def mutual_fund_ohlc(
        self, mf_id: str, *, duration: str = "1y", frequency: str = "1D",
        adjust_splits: bool = True,
    ) -> list[dict[str, Any]]:
        """Return mutual fund OHLC candles.

        Fetches the inter-day NAV chart and synthesizes OHLC candles client-side.

        Parameters:
            mf_id: Tickertape mutual fund ID.
            duration: Chart duration — ``1w``, ``1m``, ``3m``, ``6m``, ``1y``,
                ``5y``, ``max``.
            frequency: Candle frequency — ``1D``, ``1W``, ``1M``.
            adjust_splits: If True (default), detect and adjust for stock splits.
                Note: MF NAV data rarely has splits, but the adjustment is
                applied for consistency.
        """
        raw = self.mutual_fund_chart(mf_id, duration=duration)
        candles = synthesize_ohlc(raw, frequency=frequency, adjust_splits=adjust_splits)
        return ohlc_to_list(candles)

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

    def mutual_fund_screener_v2_prebuilt(self) -> JSON:
        """Return v2 prebuilt MF screens."""
        return self._data("GET", f"{self.api_base}/mf-screener/v2/prebuilt")

    def mutual_fund_screener(self, query: Mapping[str, Any]) -> JSON:
        """Run mutual-fund screener query. Some queries may require auth server-side."""
        return self._data("POST", f"{self.api_base}/mf-screener/query", json_body=query)

    def mutual_fund_screener_export(self, query: Mapping[str, Any]) -> JSON:
        """Export MF screener results. Requires auth."""
        return self._data("POST", f"{self.api_base}/mf-screener/export", json_body=query)

    def mutual_fund_screener_export_limit(self) -> JSON:
        """Return MF screener export row limit."""
        return self._data("GET", f"{self.api_base}/mf-screener/exportLimit")

    # MF Screener — custom filters / universes (auth-required)
    def mf_screener_custom_filters(self) -> JSON:
        return self._data("GET", f"{self.api_base}/mf-screener/customFilters")

    def mf_screener_custom_filter(self, filter_id: str) -> JSON:
        return self._data("GET", f"{self.api_base}/mf-screener/customFilters/{filter_id}")

    def mf_screener_custom_filter_bounds(self) -> JSON:
        return self._data("GET", f"{self.api_base}/mf-screener/customFilters/bounds")

    def mf_screener_custom_universes(self) -> JSON:
        return self._data("GET", f"{self.api_base}/mf-screener/customUniverses")

    def mf_screener_custom_universe(self, universe_id: str) -> JSON:
        return self._data("GET", f"{self.api_base}/mf-screener/customUniverses/{universe_id}")

    def mf_screener_universes(self) -> JSON:
        return self._data("GET", f"{self.api_base}/mf-screener/universes")

    # MF Screener — saved screens (auth-required)
    def mf_screener_screens(self) -> JSON:
        return self._data("GET", f"{self.api_base}/mf-screener/screens")

    def mf_screener_screen(self, screen_id: str) -> JSON:
        return self._data("GET", f"{self.api_base}/mf-screener/screens/{screen_id}")

    def mf_screener_screen_load(self, screen_id: str) -> JSON:
        return self._data("GET", f"{self.api_base}/mf-screener/screens/load/{screen_id}")

    def mf_screener_load_default_screen(self) -> JSON:
        return self._data("GET", f"{self.api_base}/mf-screener/screens/load/default")

    def mf_screener_screen_metadata(self) -> JSON:
        return self._data("GET", f"{self.api_base}/mf-screener/screens/metadata")

    def mf_screener_user_screens(self, handle: str) -> JSON:
        return self._data("GET", f"{self.api_base}/mf-screener/screens/user/{handle}")

    def mf_screener_all_screens(self) -> JSON:
        """Return all MF screens."""
        return self._data("GET", f"{self.api_base}/screener/mutual-fund/allscreens")

    # ---- portfolio (auth-required) ----------------------------------------

    def portfolio_equity(self) -> JSON:
        """Return equity portfolio data. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/equity")

    def portfolio_mutual_funds(self) -> JSON:
        """Return MF portfolio data. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/mutualfunds")

    def portfolio_mf_contribution(self) -> JSON:
        """Return MF portfolio contribution data. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/mutualfunds/contribution")

    def portfolio_us_stocks(self) -> JSON:
        """Return US stocks portfolio data. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/us-stocks")

    def portfolio_us_contribution(self) -> JSON:
        """Return US stocks contribution data. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/useq/contribution")

    def portfolio_metrics(self) -> JSON:
        """Return portfolio metrics. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/metrics")

    def portfolio_scores(self) -> JSON:
        """Return portfolio scores. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/scores")

    def portfolio_scores_v2(self, portfolio_id: str) -> JSON:
        """Return portfolio v2 scores for a specific portfolio. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/v2/scores/{portfolio_id}")

    def portfolio_diversification_score(self) -> JSON:
        """Return portfolio diversification score. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/insights/diversificationScore")

    def portfolio_forecast(self) -> JSON:
        """Return portfolio forecast. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/insights/forecast")

    def portfolio_redflags(self) -> JSON:
        """Return portfolio red flags. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/redflags")

    def portfolio_holdings_status(self) -> JSON:
        """Return holdings import status. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/holdings/status")

    def portfolio_holdings_v2(self, portfolio_id: str) -> JSON:
        """Return v2 holdings for a specific portfolio. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/v2/holdings/{portfolio_id}")

    def portfolio_holdings_v2_status(self) -> JSON:
        """Return v2 holdings status. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/v2/holdings/status")

    def portfolio_holdings_v3_status(self) -> JSON:
        """Return v3 holdings status. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/v3/holdings/status")

    def portfolio_mf_holdings_init(self) -> JSON:
        """Return MF holdings gateway init. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/holdings/gateway/mutualFunds/init")

    def portfolio_brokers_config(self) -> JSON:
        """Return broker config widget for portfolio. Requires auth."""
        return self._data("GET", f"{self.api_base}/portfolio/widget/brokers/config")

    def homepage_portfolio(self) -> JSON:
        """Return homepage portfolio data. Requires auth."""
        return self._data("GET", f"{self.api_base}/homepage/portfolio")

    def homepage_portfolio_v2(self) -> JSON:
        """Return v2 homepage portfolio data. Requires auth."""
        return self._data("GET", f"{self.api_base}/homepage/portfolio/v2")

    # ---- market movers & homepage -----------------------------------------

    def home_indices(self) -> JSON:
        """Return homepage indices widget data."""
        return self._data("GET", f"{self.api_base}/homepage/indices")

    def home_stocks(self) -> JSON:
        """Return homepage stocks widget data."""
        return self._data("GET", f"{self.api_base}/homepage/stocks")

    def home_events(self) -> JSON:
        """Return homepage events widget data."""
        return self._data("GET", f"{self.api_base}/homepage/events")

    def home_events_v2(self) -> JSON:
        """Return v2 homepage events widget data."""
        return self._data("GET", f"{self.api_base}/v2/homepage/events")

    def home_mmi(self) -> JSON:
        """Return homepage MMI widget data."""
        return self._data("GET", f"{self.api_base}/homepage/mmi")

    def market_movers_deals(self) -> JSON:
        """Return market movers deals data."""
        return self._data("GET", f"{self.api_base}/market-movers/deals")

    def market_movers_insights(self, insight_type: str) -> JSON:
        """Return market movers insights for a given type. Requires auth."""
        return self._data("GET", f"{self.api_base}/market-movers/insights/{insight_type}")

    # ---- stock feed v2 ----------------------------------------------------

    def stock_feed(self, sid: str) -> JSON:
        """Return stock feed (v1)."""
        return self._data("GET", f"{self.api_base}/stocks/feed/{sid}")

    def stock_feed_v2(self, sid: str) -> JSON:
        """Return stock feed v2 (richer data than v1)."""
        return self._data("GET", f"{self.api_base}/v2/stocks/feed/{sid}")

    def stock_summary_v2(self, sid: str) -> JSON:
        """Return stock summary v2."""
        return self._data("GET", f"{self.api_base}/v2/stocks/summary/{sid}")

    # ---- watchlists (auth-required) ---------------------------------------

    def watchlists(self) -> JSON:
        """List user's watchlists. Requires auth."""
        return self._data("GET", f"{self.api_base}/watchlists")

    def watchlist(self, watchlist_id: str) -> JSON:
        """Get a specific watchlist. Requires auth."""
        return self._data("GET", f"{self.api_base}/watchlists/{watchlist_id}")

    def watchlist_constituents(self, watchlist_id: str) -> JSON:
        """Get watchlist constituents. Requires auth."""
        return self._data("GET", f"{self.api_base}/watchlists/{watchlist_id}/constituents")

    def watchlist_add_to_basket(self, watchlist_id: str) -> JSON:
        """Add watchlist items to basket. Requires auth."""
        return self._data("POST", f"{self.api_base}/watchlists/{watchlist_id}/addToBasket")

    def watchlists_data(self) -> JSON:
        """Return watchlist aggregated data. Requires auth."""
        return self._data("GET", f"{self.api_base}/watchlists/data")

    def watchlists_tabs(self) -> JSON:
        """Return watchlist tabs/config. Requires auth."""
        return self._data("GET", f"{self.api_base}/watchlists/tabs")

    def watchlists_tab(self, tab_key: str) -> JSON:
        """Return a specific watchlist tab. Requires auth."""
        return self._data("GET", f"{self.api_base}/watchlists/tabs/{tab_key}")

    # ---- user / holdings (auth-required) ---------------------------------

    def user_profile(self) -> JSON:
        """Return user profile. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/profile")

    def user_status(self) -> JSON:
        """Return user status (subscription tier, features). Requires auth."""
        return self._data("GET", f"{self.api_base}/user/status")

    def user_subscription(self) -> JSON:
        """Return user subscription details. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/subscription")

    def user_holdings(self) -> JSON:
        """Return user stock holdings. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/holdings")

    def user_holding(self, sid: str) -> JSON:
        """Return holding for a specific stock. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/holdings/{sid}")

    def user_mf_holdings(self) -> JSON:
        """Return user MF holdings. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/mfholdings")

    def user_mf_diversification_score(self) -> JSON:
        """Return MF diversification score for user. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/mfHoldings/insights/diversificationScore")

    def user_holdings_report(self) -> JSON:
        """Return holdings report. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/holdings/report")

    def user_mf_holdings_report(self) -> JSON:
        """Return MF holdings report. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/mfholdings/report")

    def user_holdings_commentary(self) -> JSON:
        """Return holdings commentary. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/holdings/commentary")

    def user_mf_holdings_commentary(self) -> JSON:
        """Return MF holdings commentary. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/mfholdings/commentary")

    def user_holdings_contribution(self) -> JSON:
        """Return holdings contribution analysis. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/holdings/contribution")

    def user_basket(self) -> JSON:
        """Return user basket. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/basket")

    def user_basket_securities(self, sid: str) -> JSON:
        """Return basket for a specific security. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/basket/securities/{sid}")

    def user_flags(self) -> JSON:
        """Return user feature flags. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/flags")

    def user_config(self) -> JSON:
        """Return user config. Requires auth."""
        return self._data("GET", f"{self.api_base}/users/config")

    def user_search_history(self) -> JSON:
        """Return user search history. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/searchHistory")

    def user_dismissed(self) -> JSON:
        """Return user dismissed items/settings. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/dismissed")

    def user_credit_summary(self) -> JSON:
        """Return user credit summary. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/credit/summary")

    def user_credit_combined_v3(self) -> JSON:
        """Return v3 combined credit data. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/credit/combined/v3")

    def user_key_ratios(self) -> JSON:
        """Return user key ratios. Requires auth."""
        return self._data("GET", f"{self.api_base}/user/keyRatios")

    # ---- auth / gateway (auth-required) ----------------------------------

    def auth_user_v2(self) -> JSON:
        """Return authenticated user data v2. Requires auth."""
        return self._data("GET", f"{self.auth_base}/auth/user/v2")

    def auth_extend_session(self) -> JSON:
        """Extend user session. Requires auth."""
        return self._data("POST", f"{self.auth_base}/auth/extendSession")

    def gateway_holdings_init(self) -> JSON:
        """Initialize gateway holdings connection. Requires auth."""
        return self._data("POST", f"{self.api_base}/gateway/holdings/init")

    def gateway_holdings_init_id(self, gw_id: str) -> JSON:
        """Initialize gateway holdings for a specific ID. Requires auth."""
        return self._data("POST", f"{self.api_base}/gateway/holdings/init/{gw_id}")

    def gateway_connect_init(self) -> JSON:
        """Initialize gateway broker connection. Requires auth."""
        return self._data("POST", f"{self.api_base}/gateway/connect/init")

    def gateway_token(self) -> JSON:
        """Get gateway token. Requires auth."""
        return self._data("GET", f"{self.api_base}/gateway/token")

    def gateway_token_id(self, gw_id: str) -> JSON:
        """Get gateway token for a specific ID. Requires auth."""
        return self._data("GET", f"{self.api_base}/gateway/token/{gw_id}")

    # ---- trading (auth-required) -----------------------------------------

    def trades(self) -> JSON:
        """List trades. Requires auth."""
        return self._data("GET", f"{self.api_base}/api/v1/trades")

    def trade(self, trade_id: str) -> JSON:
        """Get a specific trade. Requires auth."""
        return self._data("GET", f"{self.api_base}/api/v1/trades/{trade_id}")

    def trade_cancel(self, trade_id: str) -> JSON:
        """Cancel a trade. Requires auth."""
        return self._data("POST", f"{self.api_base}/api/v1/trades/{trade_id}/cancel")

    def trade_preview(self, order: Mapping[str, Any]) -> JSON:
        """Preview a trade/order. Requires auth."""
        return self._data("POST", f"{self.api_base}/api/v1/trades/preview", json_body=order)

    def trade_config(self) -> JSON:
        """Return trading config. Requires auth."""
        return self._data("GET", f"{self.api_base}/api/v1/trades/config")

    def remittances(self) -> JSON:
        """List remittances. Requires auth."""
        return self._data("GET", f"{self.api_base}/api/v1/remittances")

    def broker_application_status(self) -> JSON:
        """Return broker application status. Requires auth."""
        return self._data("GET", f"{self.api_base}/api/v1/broker/application/status")

    # ---- social / community (auth-required) ------------------------------

    def feeds_v3(self) -> JSON:
        """Return v3 community feed. Requires auth."""
        return self._data("GET", f"{self.community_base}/v3/feeds")

    def posts_v2(self) -> JSON:
        """List community posts v2. Requires auth."""
        return self._data("GET", f"{self.community_base}/v2/posts")

    def posts_v3(self) -> JSON:
        """List community posts v3. Requires auth."""
        return self._data("GET", f"{self.community_base}/v3/posts")

    def post_v3(self, post_id: str) -> JSON:
        """Get a specific community post v3. Requires auth."""
        return self._data("GET", f"{self.community_base}/v3/posts/{post_id}")

    def comments_v2(self) -> JSON:
        """List comments v2. Requires auth."""
        return self._data("GET", f"{self.community_base}/v2/comments")

    def comment_v2(self, comment_id: str) -> JSON:
        """Get a specific comment v2. Requires auth."""
        return self._data("GET", f"{self.community_base}/v2/comments/{comment_id}")

    def polls_v2(self) -> JSON:
        """List polls v2. Requires auth."""
        return self._data("GET", f"{self.community_base}/v2/polls")

    def poll_v2(self, poll_id: str) -> JSON:
        """Get a specific poll v2. Requires auth."""
        return self._data("GET", f"{self.community_base}/v2/polls/{poll_id}")

    # ---- smallcase/platform -----------------------------------------------

    def platform_smallcase_widget(self, types: Sequence[str] | str = ("fd", "smallcases")) -> JSON:
        return self._data(
            "GET",
            f"{self.platform_base}/widget/smallcase",
            params={"types": self._csv(types)},
        )
