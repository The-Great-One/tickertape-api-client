"""Browser-assisted helpers for capturing a user's own Tickertape session.

This module does not perform credential stuffing, password submission, CAPTCHA/
2FA bypass, or hidden-login replication. It opens Tickertape in a real browser,
lets the user complete the normal login flow, then exports cookies and any
browser-storage auth token visible to the web app into the credentials file used
by :meth:`tickertape_api.client.TickertapeClient.from_env`.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

DEFAULT_CREDENTIALS_PATH = Path.home() / ".config" / "tickertape-api-client" / "credentials.json"
TICKERTAPE_LOGIN_URL = "https://www.tickertape.in/"


def build_cookie_header(
    cookies: Sequence[Mapping[str, Any]], *, domain_suffix: str = "tickertape.in"
) -> str:
    """Build a Cookie header from Playwright cookies for Tickertape domains only."""

    pairs: list[str] = []
    suffix = domain_suffix.lstrip(".")
    for cookie in cookies:
        domain = str(cookie.get("domain", "")).lstrip(".")
        name = str(cookie.get("name", ""))
        value = str(cookie.get("value", ""))
        if name and (domain == suffix or domain.endswith(f".{suffix}")):
            pairs.append(f"{name}={value}")
    return "; ".join(pairs)


def choose_auth_token(storage: Mapping[str, Any]) -> str | None:
    """Choose the most likely auth token from browser storage values.

    Tickertape may change key names. Prefer keys whose names look auth-related
    and values that look JWT-ish. Return ``None`` if no plausible token exists;
    cookie-only auth can still work for some endpoints.
    """

    candidates: list[tuple[int, str]] = []
    for key, value in storage.items():
        if not isinstance(value, str) or not value.strip():
            continue
        lowered = key.lower()
        if not any(marker in lowered for marker in ("auth", "token", "jwt", "access")):
            continue
        token = value.strip()
        score = len(token)
        if token.startswith("eyJ") or token.count(".") >= 2:
            score += 10_000
        candidates.append((score, token))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def write_credentials_file(
    path: str | Path = DEFAULT_CREDENTIALS_PATH,
    *,
    auth_token: str | None = None,
    cookie_header: str | None = None,
) -> Path:
    """Persist credentials with private filesystem permissions."""

    credentials_path = Path(path).expanduser()
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(credentials_path.parent, 0o700)
    payload = {
        key: value
        for key, value in {"auth_token": auth_token, "cookie_header": cookie_header}.items()
        if value
    }
    credentials_path.write_text(json.dumps(payload, indent=2) + "\n")
    os.chmod(credentials_path, 0o600)
    return credentials_path


def _read_page_storage(page: Any) -> dict[str, str]:
    data = page.evaluate(
        """
        () => {
          const out = {};
          for (const store of [window.localStorage, window.sessionStorage]) {
            for (let i = 0; i < store.length; i++) {
              const key = store.key(i);
              if (key) out[key] = store.getItem(key);
            }
          }
          return out;
        }
        """
    )
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items() if value is not None}


def capture_credentials_interactively(
    *,
    output_path: str | Path = DEFAULT_CREDENTIALS_PATH,
    login_url: str = TICKERTAPE_LOGIN_URL,
    headless: bool = False,
) -> Path:
    """Open a browser, let the user log in, then persist cookies/token.

    Requires optional dependency ``playwright`` and browser installation via
    ``python -m playwright install chromium``.
    """

    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "Install auth capture dependencies with: pip install 'tickertape-api-client[auth]' "
            "and then run: python -m playwright install chromium"
        ) from exc

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        page.goto(login_url, wait_until="domcontentloaded")
        input(
            "Log in to Tickertape in the opened browser window, then press Enter here "
            "to save the session credentials..."
        )
        storage = _read_page_storage(page)
        cookies = context.cookies()
        auth_token = choose_auth_token(storage)
        cookie_header = build_cookie_header(cookies)
        browser.close()

    return write_credentials_file(output_path, auth_token=auth_token, cookie_header=cookie_header)
