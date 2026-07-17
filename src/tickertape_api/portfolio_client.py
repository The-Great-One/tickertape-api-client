"""Authenticated portfolio client using curl_cffi browser impersonation.

These endpoints require a valid logged-in Tickertape session. Unlike the public
``TickertapeClient`` (httpx), this client uses ``curl_cffi`` with Chrome TLS
fingerprint impersonation and cookie-only auth — exactly what the real browser
XHR requests do.
"""

from __future__ import annotations

import contextlib
import json
import os
import typing
from pathlib import Path
from typing import Any, Literal, cast

from .credentials_store import DEFAULT_CREDENTIALS_PATH, list_accounts, read_credentials_file
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
        account: Named account from the credentials file's ``"accounts"`` dict.
            When ``None`` (default), uses ``TICKERTAPE_ACCOUNT`` env var or
            the first entry.  Ignored when the file uses flat keys.
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

    @classmethod
    def iter_accounts(
        cls,
        credentials_file: str | os.PathLike[str] | None = None,
        *,
        impersonate: str = "chrome124",
        timeout: float = 15.0,
    ) -> typing.Iterator[PortfolioClient]:
        """Yield a ``PortfolioClient`` for every account in the credentials file.

        When the file is in flat format (no ``"accounts"`` key), yields a single
        client with ``account=None`` (backward compatible).

        Usage::

            for client in PortfolioClient.iter_accounts():
                print(client.account, client.holdings_status())
        """
        accounts = list_accounts(credentials_file)
        if not accounts:
            # Flat format — yield one client with no account
            yield cls(
                credentials_file=credentials_file,
                account=None,
                impersonate=impersonate,
                timeout=timeout,
            )
        else:
            for name in accounts:
                yield cls(
                    credentials_file=credentials_file,
                    account=name,
                    impersonate=impersonate,
                    timeout=timeout,
                )

    def __init__(
        self,
        *,
        cookie_dict: dict[str, str] | None = None,
        csrf_token: str | None = None,
        credentials_file: str | os.PathLike[str] | None = None,
        account: str | None = None,
        impersonate: str = "chrome124",
        timeout: float = 15.0,
    ) -> None:
        self.impersonate = impersonate
        self.timeout = timeout

        # --- resolve credentials ---
        if cookie_dict is None:
            creds = read_credentials_file(credentials_file, account=account)
            cookie_dict = creds.get("cookie_dict") or {}
            if not cookie_dict:
                # Backwards compat: parse cookie_header
                cookie_dict = self._parse_cookie_header(creds.get("cookie_header", ""))

        self.cookie_dict = dict(cookie_dict)

        # --- CSRF token ---
        if csrf_token is None:
            csrf_token = self._find_csrf_token(self.cookie_dict)
        self.csrf_token = csrf_token

        # --- store for write-back during JWT refresh ---
        self._credentials_file = (
            Path(credentials_file).expanduser()
            if credentials_file
            else DEFAULT_CREDENTIALS_PATH
        )
        self._account = account

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
        """Find the CSRF token in cookie keys.

        Tickertape uses ``x-lp-tk`` / ``x-us-lp-tk`` for CSRF.
        Falls back to any key whose name contains ``csrf`` or ends with ``-tk``.
        """
        # Prefer the dedicated CSRF token cookie (short, API-facing)
        for key in ("x-csrf-token-tickertape-prod", "x-csrf-token"):
            if key in cookies:
                return cookies[key]
        # Next: x-lp-tk / x-us-lp-tk (used as CSRF by some endpoints)
        for key in ("x-lp-tk", "x-us-lp-tk"):
            if key in cookies:
                return cookies[key]
        # Broader search: csrf in name or -tk suffix
        for key, value in cookies.items():
            lowered = key.lower()
            if "csrf" in lowered or lowered.endswith("-tk"):
                return value
        return ""

    # JWT refresh endpoint (curl_cffi works — no WAF on auth.api subdomain)
    _REFRESH_URL = "https://auth.api.tickertape.in/auth/refresh"
    # Refresh when JWT has less than this many seconds remaining
    _REFRESH_THRESHOLD = 43200  # 12 hours — ensures daily cron always refreshes

    def _jwt_expires_in(self) -> float | None:
        """Return seconds until JWT expiry, or None if JWT is missing/unparseable."""
        jwt = self.cookie_dict.get("jwt", "")
        if not jwt:
            return None
        try:
            import base64 as _base64
            parts = jwt.split(".")
            if len(parts) != 3:
                return None
            payload = json.loads(_base64.urlsafe_b64decode(parts[1] + "=="))
            exp = payload.get("exp")
            if not exp:
                return None
            import time as _time
            return float(exp) - _time.time()
        except Exception:
            return None

    def _refresh_jwt_if_needed(self) -> bool:
        """Refresh the JWT via curl_cffi if it's near expiry.

        Calls ``auth.api.tickertape.in/auth/refresh`` with the refreshToken
        from the current JWT payload. The endpoint returns a fresh JWT in
        both the response body and Set-Cookie header.

        Returns True if a refresh was attempted (success or failure),
        False if no refresh was needed.
        """
        expires_in = self._jwt_expires_in()
        if expires_in is None or expires_in > self._REFRESH_THRESHOLD:
            return False

        refresh_token = None
        try:
            import base64 as _base64
            jwt = self.cookie_dict.get("jwt", "")
            parts = jwt.split(".")
            payload = json.loads(_base64.urlsafe_b64decode(parts[1] + "=="))
            refresh_token = payload.get("refreshToken")
        except Exception:
            return False

        if not refresh_token:
            return False

        csrf = self.csrf_token or self.cookie_dict.get("x-csrf-token-tickertape-prod", "")

        try:
            r = self._session.post(
                self._REFRESH_URL,
                cookies=self.cookie_dict,
                headers={
                    "accept": "application/json, text/plain, */*",
                    "content-type": "application/json",
                    "origin": "https://www.tickertape.in",
                    "referer": "https://www.tickertape.in/portfolio/mutualfunds",
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-site",
                    "user-agent": self._DEFAULT_UA,
                    "x-csrf-token": csrf,
                },
                json={"refreshToken": refresh_token},
                impersonate=cast(Any, self.impersonate),
                timeout=self.timeout,
            )
        except Exception:
            return False

        if not r.ok:
            return False

        # Capture Set-Cookie (server sends fresh jwt cookie)
        self._update_cookies_from_response(r)

        # Also check response body for the new JWT
        try:
            json_body = cast(Any, r.json)()
            data: object = json_body
            if isinstance(data, dict) and "jwt" in data:
                new_jwt = data["jwt"]
                if new_jwt and new_jwt != self.cookie_dict.get("jwt", ""):
                    self.cookie_dict["jwt"] = new_jwt
                    self.csrf_token = self._find_csrf_token(self.cookie_dict)
                    self._persist_credentials()
        except Exception:
            pass

        return True

    def _update_cookies_from_response(self, response: Any) -> None:
        """Capture Set-Cookie headers from a response and update our cookie dict.

        Most Tickertape API endpoints do NOT rotate the JWT via Set-Cookie.
        The JWT expires after 24h and must be refreshed via a separate call to
        ``auth.api.tickertape.in/auth/refresh`` (requires a real browser — the
        endpoint is behind a CloudFront WAF that blocks curl_cffi).

        This method still captures any Set-Cookie headers as a best-effort
        mechanism, and persists changes to disk.

        Also re-derives ``self.csrf_token`` if a CSRF-related cookie changed.
        """
        raw_headers = response.headers
        if not raw_headers:
            return

        # curl_cffi headers are case-insensitive dict-like.
        # Multiple Set-Cookie headers may be joined with '\n' or appear as a list.
        set_cookie = raw_headers.get("set-cookie")
        if not set_cookie:
            return

        changed = False
        # Handle both single string and list-of-strings from curl_cffi
        cookie_strings: list[str] = (
            [set_cookie] if isinstance(set_cookie, str) else list(set_cookie)
        )
        for entry in cookie_strings:
            for pair in entry.split(";"):
                pair = pair.strip()
                if "=" in pair and not pair.lower().startswith(
                    ("path=", "domain=", "expires=", "max-age=", "httponly", "secure", "samesite")
                ):
                    name, value = pair.split("=", 1)
                    old = self.cookie_dict.get(name)
                    # NEVER downgrade: if the old value is non-empty and the new is
                    # empty, the server is clearing the cookie (common on 401/403
                    # responses with Set-Cookie: jwt=). Skip the update to preserve
                    # the valid cookie for future session-refresh attempts.
                    if old and not value:
                        continue
                    if old != value:
                        self.cookie_dict[name] = value
                        changed = True

        if changed:
            # Re-derive CSRF token if cookies changed
            self.csrf_token = self._find_csrf_token(self.cookie_dict)
            self._persist_credentials()

    def _persist_credentials(self) -> None:
        """Write current cookie_dict back to the correct account slot."""
        try:
            # Read the full file to preserve other accounts
            full: dict[str, Any] = {}
            if self._credentials_file.exists():
                with contextlib.suppress(OSError, json.JSONDecodeError):
                    full = json.loads(self._credentials_file.read_text())
            if not isinstance(full, dict):
                full = {}

            if self._account:
                # Multi-account: update the named slot
                full.setdefault("accounts", {})
                full["accounts"][self._account] = {
                    "cookie_dict": dict(self.cookie_dict),
                    "cookie_header": "; ".join(
                        f"{k}={v}" for k, v in self.cookie_dict.items()
                    ),
                }
            else:
                # Flat mode: update top-level keys
                full["cookie_dict"] = dict(self.cookie_dict)
                full["cookie_header"] = "; ".join(
                    f"{k}={v}" for k, v in self.cookie_dict.items()
                )

            self._credentials_file.parent.mkdir(parents=True, exist_ok=True)
            os.chmod(self._credentials_file.parent, 0o700)
            self._credentials_file.write_text(json.dumps(full, indent=2) + "\n")
            os.chmod(self._credentials_file, 0o600)
        except (OSError, json.JSONDecodeError):
            pass  # best-effort — don't crash requests if file-write fails

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
        # Auto-refresh JWT if near expiry (uses real browser for WAF-protected endpoint)
        self._refresh_jwt_if_needed()

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
                impersonate=cast(Any, self.impersonate),
                timeout=self.timeout,
            )
        except Exception as exc:
            raise TickertapeAPIError(f"Portfolio request failed: {exc}") from exc

        # Parse JSON
        try:
            json_body = cast(Any, r.json)()
            data = cast(dict[str, Any], json_body)
        except json.JSONDecodeError as err:
            raise TickertapeAPIError(
                f"Tickertape returned non-JSON response ({r.status_code})",
                r.text[:500],
            ) from err

        if not r.ok:
            msg = data.get("error") or data.get("message") or r.reason or "Unknown error"
            # Still try to update cookies even on error — some servers send a fresh
            # jwt in Set-Cookie alongside a 401/403, especially near expiry.
            self._update_cookies_from_response(r)
            raise TickertapeHTTPError(r.status_code, msg, data)

        # Capture Set-Cookie headers from the response and update our cookie dict
        # so the JWT gets refreshed silently (server sends a new jwt cookie on each request).
        self._update_cookies_from_response(r)

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
