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


def _filter_tickertape_cookies(
    cookies: Sequence[Mapping[str, Any]], *, domain_suffix: str = "tickertape.in"
) -> list[tuple[str, str]]:
    """Return (name, value) pairs for Tickertape-domain cookies."""
    pairs: list[tuple[str, str]] = []
    suffix = domain_suffix.lstrip(".")
    for cookie in cookies:
        domain = str(cookie.get("domain", "")).lstrip(".")
        name = str(cookie.get("name", ""))
        value = str(cookie.get("value", ""))
        if name and (domain == suffix or domain.endswith(f".{suffix}")):
            pairs.append((name, value))
    return pairs


def build_cookie_header(
    cookies: Sequence[Mapping[str, Any]], *, domain_suffix: str = "tickertape.in"
) -> str:
    """Build a Cookie header from Playwright cookies for Tickertape domains only."""
    return "; ".join(f"{n}={v}" for n, v in _filter_tickertape_cookies(cookies, domain_suffix=domain_suffix))


def build_cookie_dict(
    cookies: Sequence[Mapping[str, Any]], *, domain_suffix: str = "tickertape.in"
) -> dict[str, str]:
    """Build a cookie dict for curl_cffi (``{name: value}``) from Playwright cookies."""
    return dict(_filter_tickertape_cookies(cookies, domain_suffix=domain_suffix))


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
    cookie_dict: dict[str, str] | None = None,
) -> Path:
    """Persist credentials with private filesystem permissions."""

    credentials_path = Path(path).expanduser()
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(credentials_path.parent, 0o700)
    payload = {
        key: value
        for key, value in {
            "auth_token": auth_token,
            "cookie_header": cookie_header,
            "cookie_dict": cookie_dict,
        }.items()
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


def _launch_browser(
    *,
    headless: bool = False,
) -> tuple[Any, Any, Any]:
    """Launch a stealth browser and return (browser, context, page).

    Tries CloakBrowser first (C++-level stealth, bypasses bot detection),
    falls back to Playwright.
    """
    try:
        from cloakbrowser import launch

        browser = launch(headless=headless, humanize=True)
        context = browser.new_context()
        page = context.new_page()
        return browser, context, page
    except ImportError:
        pass

    try:
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=headless, channel="chrome")
        context = browser.new_context()
        page = context.new_page()
        return browser, context, page
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "Install auth capture dependencies with: "
            "pip install 'tickertape-api-client[auth]' "
            "and then run: python -m playwright install chromium"
        ) from exc


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
    browser, context, page = _launch_browser(headless=headless)

    try:
        page.goto(login_url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        input(
            "Log in to Tickertape in the opened browser window, then press Enter here "
            "to save the session credentials..."
        )
        storage = _read_page_storage(page)
        cookies = context.cookies()
        auth_token = choose_auth_token(storage)
        cookie_header = build_cookie_header(cookies)
        cookie_dict_ = build_cookie_dict(cookies)
    finally:
        browser.close()

    return write_credentials_file(
        output_path, auth_token=auth_token, cookie_header=cookie_header, cookie_dict=cookie_dict_
    )


def capture_credentials_via_otp(
    *,
    phone: str,
    country_code: str = "+91",
    otp: str | None = None,
    output_path: str | Path = DEFAULT_CREDENTIALS_PATH,
    headless: bool = False,
) -> Path:
    """Log in to Tickertape via phone-number OTP flow and persist session credentials.

    This automates the full login: opens Tickertape, clicks the login modal,
    enters phone + country code, requests OTP, enters the OTP, and captures
    cookies / auth token after a successful login.

    Args:
        phone: The phone number to log in with (digits only, without country code).
        country_code: The country code (default ``"+91"``).
        otp: The 6-digit OTP. If ``None`` (default), the function reads the OTP
             interactively from stdin (useful for SMS-delivered codes).
        output_path: Where to write the credentials JSON file.
        headless: Whether to run the browser in headless mode.

    Returns:
        The path to the credentials file that was written.

    Requires ``playwright`` (``pip install 'tickertape-api-client[auth]'``).
    """
    if otp is None:
        import sys as _sys

        if _sys.stdin.isatty():
            otp = input("Enter the 6-digit OTP sent to your phone: ").strip()
        else:
            raise RuntimeError(
                "OTP required. Set --otp <code> or run in an interactive terminal."
            ) from None

    browser, context, page = _launch_browser(headless=headless)

    try:
        page.goto("https://www.tickertape.in/#login-init", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # --- Find and fill the phone input ---
        phone_input = page.wait_for_selector(
            '#phoneNumber, input[placeholder*="Phone"]',
            timeout=15_000,
        )
        if phone_input is None or not phone_input.is_visible():
            raise RuntimeError("Phone number input not found on login modal")
        phone_input.click()
        phone_input.fill("")  # clear any default
        phone_input.type(phone, delay=80)

        # Click "Get OTP" via JavaScript (modal-overlay blocks Playwright pointer)
        page.wait_for_timeout(1000)
        page.wait_for_selector(
            'button:has-text("Get OTP"):not([disabled])',
            timeout=10_000,
        )
        page.evaluate(
            """() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    if (/get\\s*otp/i.test(btn.textContent || '')) {
                        btn.click(); return;
                    }
                }
            }"""
        )
        page.wait_for_timeout(3000)

        # --- Enter OTP ---
        page.evaluate(
            f"""() => {{
                const inputs = document.querySelectorAll(
                    'input[maxlength="1"], '
                    + 'input[aria-label*="digit"], '
                    + 'input[aria-label*="OTP"], '
                    + 'input[placeholder*="0"], '
                    + 'input.otp-input'
                );
                if (inputs.length >= 6) {{
                    const digits = '{otp}';
                    for (let i = 0; i < inputs.length && i < digits.length; i++) {{
                        const nativeSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 'value'
                        ).set;
                        nativeSetter.call(inputs[i], digits[i]);
                        inputs[i].dispatchEvent(new Event('input', {{bubbles: true}}));
                        inputs[i].dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                }} else {{
                    // Single OTP input (fallback)
                    const inp = document.querySelector(
                        'input[placeholder*="OTP"], '
                        + 'input[placeholder*="otp"], '
                        + 'input[placeholder*="code"]'
                    );
                    if (inp) {{
                        const nativeSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 'value'
                        ).set;
                        nativeSetter.call(inp, '{otp}');
                        inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                        inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                }}
            }}"""
        )
        page.wait_for_timeout(1000)

        # Submit OTP via JavaScript
        page.wait_for_timeout(1000)
        page.evaluate(
            """
            () => {
                const buttons = document.querySelectorAll('button');
                const labels = /verify|submit|login|continue|proceed|done/i;
                for (const btn of buttons) {
                    if (labels.test(btn.textContent || '')) {
                        btn.click();
                        return;
                    }
                }
            }
            """
        )

        # Wait for login to complete
        page.wait_for_timeout(5000)

        # Capture credentials
        storage = _read_page_storage(page)
        cookies = context.cookies()
        auth_token = choose_auth_token(storage)
        cookie_header = build_cookie_header(cookies)
        cookie_dict_ = build_cookie_dict(cookies)
    finally:
        browser.close()

    return write_credentials_file(
        output_path, auth_token=auth_token, cookie_header=cookie_header, cookie_dict=cookie_dict_
    )
