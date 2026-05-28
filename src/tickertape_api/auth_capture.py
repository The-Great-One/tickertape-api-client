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
        from playwright.sync_api import sync_playwright
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
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "Install auth capture dependencies with: pip install 'tickertape-api-client[auth]' "
            "and then run: python -m playwright install chromium"
        ) from exc

    if otp is None:
        otp = input("Enter the 6-digit OTP sent to your phone: ").strip()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        page.goto(TICKERTAPE_LOGIN_URL, wait_until="domcontentloaded")

        # --- Step 1: Open the login modal ---
        page.click('button:has-text("Sign Up")')
        page.wait_for_selector('text=Enter your phone number', timeout=10_000)

        # --- Step 2: Select country code if needed ---
        cc_button = page.query_selector(".phone-input-wrapper [role=\"combobox\"], "
                                        "div:has(> select) >> text=\\+91, "
                                        "[class*=\"country\" i]")
        if cc_button:
            cc_button.click()
            option = page.query_selector(f"text={country_code}")
            if option:
                option.click()
            else:
                # Fallback: try clicking the default dropdown and picking from options
                page.wait_for_timeout(500)
                page.evaluate(
                    f"""
                    () => {{
                        const selects = document.querySelectorAll('select');
                        for (const s of selects) {{
                            if (s.textContent.includes('India')) {{
                                s.value = '{country_code}';
                                s.dispatchEvent(new Event('change', {{bubbles: true}}));
                            }}
                        }}
                    }}
                    """
                )

        # --- Step 3: Enter phone number ---
        phone_input = page.query_selector(
            'input[type="tel"], input[placeholder*="Phone"], '
            "input:not([type=\"hidden\"]):below(:text(\"Enter your phone number\"))"
        )
        if phone_input:
            phone_input.fill(phone)
        else:
            # Fallback: find any visible text input in the modal
            page.fill(
                "[role=\"dialog\"] input:not([type=\"hidden\"]), "
                "text=Enter your phone number >> xpath=../..//input",
                phone,
            )

        # --- Step 4: Click "Get OTP" ---
        page.click('button:has-text("Get OTP")')
        page.wait_for_timeout(2000)

        # --- Step 5: Enter OTP ---
        otp_input = page.query_selector(
            'input[type="tel"], input[placeholder*="OTP"], '
            'input[inputmode="numeric"][maxlength="6"]'
        )
        if otp_input:
            otp_input.fill(otp)
        else:
            page.fill("[role=\"dialog\"] input:not([type=\"hidden\"])", otp)

        # --- Step 6: Submit OTP ---
        page.click('button:has-text("Verify"), button:has-text("Submit"), button:has-text("Login")')
        page.wait_for_timeout(3000)

        # If there's a "Continue" or "Proceed" button after OTP verification, click it
        try:
            page.click(
                'button:has-text("Continue"), button:has-text("Proceed"), '
                'button:has-text("Done")',
                timeout=3000,
            )
            page.wait_for_timeout(2000)
        except Exception:
            pass  # No additional step needed

        # --- Step 7: Capture credentials ---
        storage = _read_page_storage(page)
        cookies = context.cookies()
        auth_token = choose_auth_token(storage)
        cookie_header = build_cookie_header(cookies)
        browser.close()

    return write_credentials_file(output_path, auth_token=auth_token, cookie_header=cookie_header)
