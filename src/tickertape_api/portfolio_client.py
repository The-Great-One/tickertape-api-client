"""Authenticated portfolio client using curl_cffi browser impersonation.

These endpoints require a valid logged-in Tickertape session. Unlike the public
``TickertapeClient`` (httpx), this client uses ``curl_cffi`` with Chrome TLS
fingerprint impersonation and cookie-only auth — exactly what the real browser
XHR requests do.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

from .exceptions import TickertapeAPIError, TickertapeHTTPError


class PortfolioClient:
    """Authenticated portfolio/wallet client via curl_cffi cookie impersonation.

    Parameters:
        cookie_dict: ``{name: value}`` dict of Tickertape session cookies, or
            ``None`` to load from the credentials file / env.
        csrf_token: Tickertape CSRF token. Auto-extracted from *cookie_dict*
            when not provided (any cookie key containing ``csrf``).
        credentials_file: JSON file path. Defaults to
            ``~/.config/tickertape-api-client/credentials.json``.
        impersonate: curl_cffi browser version to impersonate (default
            ``chrome124`` — the most reliably undetected fingerprint).
        timeout: Per-request timeout in seconds.
    """

    api_base = "https://api.tickertape.in"
    ecosystem_base = "https://ecosystem.api.tickertape.in"
    gms_base = "https://gms-api.tickertape.in"
    quotes_base = "https://quotes-api.tickertape.in"

    _DEFAULT_UA = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        *,
        cookie_dict: dict[str, str] | None = None,
        csrf_token: str | None = None,
        credentials_file: str | os.PathLike[str] | None = None,
        impersonate: str = "chrome124",
        timeout: float = 15.0,
    ) -> None:
        self.impersonate = impersonate
        self.timeout = timeout

        # --- resolve credentials ---
        if cookie_dict is None:
            creds = self._read_credentials_file(credentials_file)
            cookie_dict = creds.get("cookie_dict") or {}
            if not cookie_dict:
                # Backwards compat: parse cookie_header
                cookie_dict = self._parse_cookie_header(creds.get("cookie_header", ""))

        self.cookie_dict = dict(cookie_dict)

        # --- CSRF token ---
        if csrf_token is None:
            csrf_token = self._find_csrf_token(self.cookie_dict)
        self.csrf_token = csrf_token

        # --- lazy import (curl_cffi is an optional dependency) ---
        try:
            from curl_cffi import requests as _curl_requests
        except ImportError as exc:
            raise ImportError(
                "curl_cffi is required for PortfolioClient. "
                "Install with: pip install 'tickertape-api-client[portfolio]' "
                "or: pip install curl-cffi"
            ) from exc
        self._session = _curl_requests

    # ------------------------------------------------------------------
    # credential loading
    # ------------------------------------------------------------------

    @staticmethod
    def _read_credentials_file(
        path: str | os.PathLike[str] | None = None,
    ) -> dict[str, Any]:
        credentials_path = (
            Path(path).expanduser()
            if path
            else Path.home() / ".config" / "tickertape-api-client" / "credentials.json"
        )
        if not credentials_path.exists():
            return {}
        try:
            payload = json.loads(credentials_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise TickertapeAPIError(
                f"Could not read Tickertape credentials file: {credentials_path}", str(exc)
            ) from exc
        if not isinstance(payload, dict):
            raise TickertapeAPIError(
                f"Tickertape credentials file must contain a JSON object: {credentials_path}",
                payload,
            )
        return payload

    @staticmethod
    def _parse_cookie_header(header: str) -> dict[str, str]:
        """Parse a ``Cookie`` header string into a dict."""
        result: dict[str, str] = {}
        for pair in header.split("; "):
            if "=" in pair:
                name, _, value = pair.partition("=")
                result[name.strip()] = value.strip()
        return result

    @staticmethod
    def _find_csrf_token(cookies: dict[str, str]) -> str:
        """Find the CSRF token in cookie keys."""
        for key, value in cookies.items():
            if "csrf" in key.lower():
                return value
        return ""

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _build_headers(
        self, *, referer: str = "https://www.tickertape.in/", extra: dict[str, str] | None = None
    ) -> dict[str, str]:
        h = {
            "accept": "application/json, text/plain, */*",
            "accept-version": "8.14.0",
            "user-agent": self._DEFAULT_UA,
            "x-device-type": "web",
            "referer": referer,
        }
        if self.csrf_token:
            h["x-csrf-token"] = self.csrf_token
        if extra:
            h.update({k.lower(): v for k, v in extra.items()})
        return h

    _Method = Literal["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "TRACE", "PATCH", "QUERY"]

    def _request(
        self,
        method: _Method,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        referer: str = "https://www.tickertape.in/",
        headers: dict[str, str] | None = None,
    ) -> Any:
        hdrs = self._build_headers(referer=referer)
        if headers:
            hdrs.update({k.lower(): v for k, v in headers.items()})

        try:
            r = self._session.request(
                method,
                url,
                params=params,
                json=json_body,
                cookies=self.cookie_dict,
                headers=hdrs,
                impersonate=self.impersonate,  # type: ignore[arg-type]
                timeout=self.timeout,
            )
        except Exception as exc:
            raise TickertapeAPIError(f"Portfolio request failed: {exc}") from exc

        # Parse JSON
        try:
            data = r.json()  # type: ignore[no-untyped-call]
        except json.JSONDecodeError as err:
            raise TickertapeAPIError(
                f"Tickertape returned non-JSON response ({r.status_code})",
                r.text[:500],
            ) from err

        if not r.ok:
            msg = data.get("error") or data.get("message") or r.reason or "Unknown error"
            raise TickertapeHTTPError(r.status_code, msg, data)

        return data

    def _get(self, url: str, *, params: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        return self._request("GET", url, params=params, **kwargs)

    def _post(
        self, url: str, *, json_body: Any = None, params: dict[str, Any] | None = None, **kwargs: Any
    ) -> Any:
        return self._request("POST", url, json_body=json_body, params=params, **kwargs)

    def _get_data(self, url: str, *, params: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        payload = self._get(url, params=params, **kwargs)
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

    # ------------------------------------------------------------------
    # Mutual Fund Portfolio
    # ------------------------------------------------------------------

    def mf_holdings(self) -> Any:
        """Return the user's mutual fund portfolio holdings.

        Returns the full JSON response from ``/user/mfholdings``. Typical data
        includes ``mfHoldings`` (list of holdings with fund info, quantity, nav,
        current value, returns) and ``mfFolios``.
        """
        return self._get_data(f"{self.api_base}/user/mfholdings")

    # ------------------------------------------------------------------
    # Portfolio v3 (includes US stocks)
    # ------------------------------------------------------------------

    def holdings_status(self) -> Any:
        """Return portfolio holdings status from ecosystem API (v3).

        Returns the ``/portfolio/v3/holdings/status`` payload. Includes
        ``STOCK`` (Indian equities via linked gateway), ``MUTUALFUND``, and
        ``US_STOCK`` (Tickertape native US trading) positions with current
        holdings, P&L, and portfolio health indicators.
        """
        return self._get_data(
            f"{self.ecosystem_base}/portfolio/v3/holdings/status",
            referer="https://www.tickertape.in/portfolio/mutualfunds",
        )

    def us_holdings(self) -> Any:
        """Return US stock holdings only.

        Convenience wrapper that calls :meth:`holdings_status` and extracts
        the ``US_STOCK`` asset status entry. Returns ``None`` if no US stocks
        are held.
        """
        status = self.holdings_status()
        for asset in status.get("assetsStatus", []):
            if asset.get("type") == "US_STOCK":
                return asset
        return None

    # ------------------------------------------------------------------
    # Watchlists
    # ------------------------------------------------------------------

    def watchlists(
        self,
        *,
        asset_class: str = "SECURITY",
        market: str = "IN,US",
    ) -> Any:
        """Return the user's watchlists.

        Args:
            asset_class: Usually ``SECURITY``. Other values may include ``MF``.
            market: Comma-separated market codes, e.g. ``IN,US``.

        Returns the watchlists payload — list of watchlists with their stock
        entries, identifiers, and watchlist metadata.
        """
        return self._get_data(
            f"{self.ecosystem_base}/watchlists",
            params={"assetClass": asset_class, "market": market},
            referer="https://www.tickertape.in/watchlists",
        )

    # ------------------------------------------------------------------
    # Stock Portfolio (discovery candidates)
    # ------------------------------------------------------------------

    def stock_holdings(self) -> Any:
        """Return the user's stock/equity portfolio holdings.

        Calls ``/user/holdings`` — the same endpoint the web app uses for the
        "Stocks" tab in Portfolio.
        """
        return self._get_data(
            f"{self.api_base}/user/holdings",
            referer="https://www.tickertape.in/portfolio/stocks",
        )

    def portfolio_summary(self) -> Any:
        """Return the user's portfolio summary.

        Calls ``/portfolio/v2/holdings/status`` (same as
        :meth:`holdings_status`) and enriches with MF + stock holdings.

        Returns a dict with keys ``holdings_status``, ``mf_holdings``,
        ``stock_holdings``, and ``watchlists``.
        """
        return {
            "holdings_status": self.holdings_status(),
            "mf_holdings": self.mf_holdings(),
            "stock_holdings": self.stock_holdings(),
            "watchlists": self.watchlists(),
        }

    # ------------------------------------------------------------------
    # Convenience: quotes for portfolio holdings
    # ------------------------------------------------------------------

    def quote_portfolio(self) -> Any:
        """Return live quotes for all stocks in the user's portfolio.

        Fetches stock holdings, extracts SIDs, and returns latest quotes
        via the public quotes endpoint.
        """
        try:
            holdings = self.stock_holdings()
        except TickertapeHTTPError:
            return {"error": "Could not fetch stock holdings"}

        sids: list[str] = []
        # holdings structure: list of {..., "sid": "...", ...}
        if isinstance(holdings, list):
            sids = [h["sid"] for h in holdings if isinstance(h, dict) and h.get("sid")]
        elif isinstance(holdings, dict):
            items = holdings.get("holdings") or holdings.get("data") or []
            if isinstance(items, list):
                sids = [h["sid"] for h in items if isinstance(h, dict) and h.get("sid")]

        if not sids:
            return {"sids": sids, "quotes": []}

        # Use public quotes endpoint (no auth needed)
        # We make a raw request to quotes-api since it's public
        params = {"sids": ",".join(sids)}
        return self._get_data(
            f"{self.quotes_base}/quotes",
            params=params,
            referer="https://www.tickertape.in/portfolio/stocks",
        )

    def close(self) -> None:
        """No-op — curl_cffi has no persistent connection pool to close."""
        pass

    def __enter__(self) -> PortfolioClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
