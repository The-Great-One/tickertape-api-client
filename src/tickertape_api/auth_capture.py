"""Browser-assisted helpers for capturing a user's own Tickertape session.

Opens Tickertape in a real browser (CloakBrowser or Playwright), drives the
phone-number OTP login flow, and exports session cookies into the credentials
file used by :meth:`tickertape_api.client.TickertapeClient.from_env`.

Supports optional PyPasser reCAPTCHA token generation to bypass reCAPTCHA
Enterprise checks during the OTP flow without relying on the browser's widget.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

try:
    from curl_cffi import requests as _requests
except ImportError:
    import requests as _requests  # type: ignore[no-redef]

DEFAULT_CREDENTIALS_PATH = Path.home() / ".config" / "tickertape-api-client" / "credentials.json"
TICKERTAPE_LOGIN_URL = "https://www.tickertape.in/"
OTP_BASE_URL = "https://otp.smallcase.com"
TICKERTAPE_CLIENT_ID = "tickertape-frontend"


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



def write_credentials_file(
    path: str | Path = DEFAULT_CREDENTIALS_PATH,
    *,
    auth_token: str | None = None,
    cookie_header: str | None = None,
    cookie_dict: dict[str, str] | None = None,
    account: str | None = None,
) -> Path:
    """Persist credentials with private filesystem permissions.

    When *account* is provided, writes to the ``"accounts"`` → ``<account>``
    slot in the JSON file, preserving other accounts.  When *account* is
    ``None`` (default), writes to the top-level keys (backward compatible).
    """

    credentials_path = Path(path).expanduser()
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(credentials_path.parent, 0o700)

    # Build the entry for this account
    entry = {
        key: value
        for key, value in {
            "auth_token": auth_token,
            "cookie_header": cookie_header,
            "cookie_dict": cookie_dict,
        }.items()
        if value
    }

    if account:
        # Multi-account: read existing file, update the named slot
        full: dict[str, Any] = {}
        if credentials_path.exists():
            try:
                full = json.loads(credentials_path.read_text())
            except (OSError, json.JSONDecodeError):
                pass
        if not isinstance(full, dict):
            full = {}
        full.setdefault("accounts", {})
        full["accounts"][account] = entry
        credentials_path.write_text(json.dumps(full, indent=2) + "\n")
    else:
        # Flat mode: write top-level keys
        credentials_path.write_text(json.dumps(entry, indent=2) + "\n")

    os.chmod(credentials_path, 0o600)
    return credentials_path


# ---------------------------------------------------------------------------
# Browserless HTTP helpers (no browser needed for auth/token step)
# ---------------------------------------------------------------------------

def get_auth_token(
    phone: str,
    *,
    country_code: str = "+91",
    client_id: str = TICKERTAPE_CLIENT_ID,
    timeout: float = 10.0,
) -> str:
    """Get an auth token from otp.smallcase.com — pure HTTP, no browser.

    Uses the ``x-client-id`` header (discovered 2026-05-31) instead of
    pre-login browser cookies.  This replaces the old cookie-dependent
    ``auth/token`` call that required a browser.

    Args:
        phone: Phone number (digits only, without country code).
        country_code: Country code (default ``"+91"``).
        client_id: The ``x-client-id`` header value.
        timeout: HTTP request timeout in seconds.

    Returns:
        The auth token string (JWT) to use as ``x-auth-jwt`` header.

    Raises:
        RuntimeError: If the API returns an error.
        Exception: On network failure.
    """
    resp = _requests.post(
        f"{OTP_BASE_URL}/auth/token",
        json={
            "phone": phone,
            "phoneCountryCode": country_code,
        },
        headers={
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": TICKERTAPE_LOGIN_URL,
            "Referer": TICKERTAPE_LOGIN_URL,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "x-client-id": client_id,
        },
        timeout=timeout,
        impersonate="chrome124",
    )
    if resp.status_code == 403 or (resp.status_code == 200 and not resp.text.strip()):
        # CloudFront may 403 with certain TLS fingerprints.  Retry
        # without impersonate to fall back to default TLS.
        resp = _requests.post(
            f"{OTP_BASE_URL}/auth/token",
            json={
                "phone": phone,
                "phoneCountryCode": country_code,
            },
            headers={
                "Content-Type": "application/json",
                "x-client-id": client_id,
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            },
            timeout=timeout,
        )
    body = resp.json()
    if not body.get("success"):
        errors = body.get("errors", ["unknown error"])
        raise RuntimeError(f"auth/token failed: {errors}")
    token: str = body["data"]["authToken"]
    return token


def capture_credentials_via_hybrid(
    phone: str,
    *,
    country_code: str = "+91",
    otp: str | None = None,
    output_path: str | Path = DEFAULT_CREDENTIALS_PATH,
    headless: bool = False,
    client_id: str = TICKERTAPE_CLIENT_ID,
    account: str | None = None,
) -> Path:
    """Browserless auth/token + lightweight browser for reCAPTCHA-bound steps.

    Hybrid approach (2026-05-31):
    1. **Pure HTTP**: ``auth/token`` via ``x-client-id`` header — no browser needed.
    2. **Browser**: Load tickertape.in to get a reCAPTCHA Enterprise widget token.
    3. **Browser JS**: Call ``auth/otp`` and ``auth/verify`` via ``fetch()`` from
       within the page (same origin, so reCAPTCHA token is valid).
    4. **Extract cookies**: After successful login, grab cookies from the browser
       context and persist to the credentials file.

    This is simpler and more robust than the full-UI flow because:
    - No need to click buttons or fill DOM inputs
    - No dependency on login modal selectors
    - No maintenance-mode edge cases
    - auth/token is instant (no browser)
    - Only ~2s of browser time vs ~15-30s for the full UI flow

    Args:
        phone: Phone number (digits only, without country code).
        country_code: Country code (default ``"+91"``).
        otp: The 4-digit OTP code. If ``None`` (default), prompts interactively
             on stdin after sending the OTP.
        output_path: Where to write the credentials JSON file.
        headless: Whether to run the browser in headless mode.
        client_id: The ``x-client-id`` header value.

    Returns:
        The path to the credentials file that was written.

    Requires ``playwright`` (``pip install 'tickertape-api-client[auth]'``).
    """
    import sys as _sys

    # Step 1: Get authToken via pure HTTP
    print("Step 1: Getting auth token (browserless HTTP)...")
    auth_token = get_auth_token(phone, country_code=country_code, client_id=client_id)
    print(f"  OK authToken ({len(auth_token)} chars)")

    # Step 2: Open browser, load tickertape.in, get reCAPTCHA widget token
    browser, context, page = _launch_browser(headless=headless)
    try:
        print("Step 2: Opening browser for reCAPTCHA...")
        page.goto(TICKERTAPE_LOGIN_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        page.wait_for_selector(
            'iframe[src*="recaptcha/enterprise/anchor"]', timeout=15_000
        )

        widget_id: int = page.evaluate(
            "() => parseInt(Object.keys(window.___grecaptcha_cfg.clients)[0])"
        )
        print(f"  reCAPTCHA widget ID: {widget_id}")

        def _fresh_recaptcha() -> str:
            return page.evaluate(
                f"() => grecaptcha.enterprise.execute({widget_id})"
            )

        # Step 3: Send OTP via fetch() from within the browser
        print("Step 3: Sending OTP...")
        recaptcha1 = _fresh_recaptcha()
        otp_result: dict[str, Any] = page.evaluate(
            """async ({authToken, recaptchaToken}) => {
                const resp = await fetch('https://otp.smallcase.com/auth/otp', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'x-client-id': 'tickertape-frontend',
                        'x-auth-jwt': authToken,
                    },
                    body: JSON.stringify({recaptchaToken: recaptchaToken}),
                });
                return await resp.json();
            }""",
            {"authToken": auth_token, "recaptchaToken": recaptcha1},
        )
        if not otp_result.get("success"):
            errors = otp_result.get("errors", ["unknown"])
            err_code = otp_result.get("errorCode", "")
            raise RuntimeError(f"auth/otp failed: {err_code} {errors}")
        print("  OK OTP sent")

        # Get OTP interactively if not provided
        if otp is None:
            if _sys.stdin.isatty():
                otp = input("Enter the OTP sent to your phone: ").strip()
                if not otp:
                    raise RuntimeError("No OTP entered.")
            else:
                _stdin_data = _sys.stdin.read().strip()
                if _stdin_data:
                    otp = _stdin_data
                else:
                    raise RuntimeError(
                        "OTP required. Pipe it via stdin or pass --otp."
                    )

        # Step 4: Verify OTP
        print("Step 4: Verifying OTP...")
        recaptcha2 = _fresh_recaptcha()
        verify_result: dict[str, Any] = page.evaluate(
            """async ({authToken, otpCode, recaptchaToken}) => {
                const resp = await fetch('https://otp.smallcase.com/auth/verify', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'x-client-id': 'tickertape-frontend',
                        'x-auth-jwt': authToken,
                    },
                    body: JSON.stringify({otp: otpCode, recaptchaToken: recaptchaToken}),
                });
                return await resp.json();
            }""",
            {"authToken": auth_token, "otpCode": otp, "recaptchaToken": recaptcha2},
        )
        if not verify_result.get("success"):
            errors = verify_result.get("errors", ["unknown"])
            raise RuntimeError(f"auth/verify failed: {errors}")

        # Navigate to set cookies
        redirect_url: str | None = verify_result.get("data", {}).get("redirectUrl")
        if redirect_url:
            page.goto(redirect_url, wait_until="domcontentloaded")
        else:
            page.goto(TICKERTAPE_LOGIN_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Step 5: Extract cookies
        print("Step 5: Extracting cookies...")
        cookies = context.cookies()
        cookie_header = build_cookie_header(cookies)
        cookie_dict_ = build_cookie_dict(cookies)

        has_jwt = bool(cookie_dict_.get("jwt"))
        is_logged_in = cookie_dict_.get("x-tickertape-user-state") == "logged-in"
        if not (has_jwt or is_logged_in):
            raise RuntimeError(
                "Login succeeded but no jwt cookie/logged-in state found. "
                "Cookies: " + ", ".join(cookie_dict_.keys())
            )
        print(f"  OK jwt cookie + {len(cookie_dict_)} total cookies")
    finally:
        browser.close()

    return write_credentials_file(
        output_path, cookie_header=cookie_header, cookie_dict=cookie_dict_, account=account
    )


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


# ---------------------------------------------------------------------------
# PyPasser reCAPTCHA helpers
# ---------------------------------------------------------------------------

def _extract_recaptcha_anchor_url(page: Any) -> str | None:
    """Extract the reCAPTCHA Enterprise anchor URL from the current page.

    Returns the ``src`` of the first reCAPTCHA iframe found, or ``None``
    if no reCAPTCHA widget is present on the page.
    """
    result: str | None = page.evaluate(
        """() => {
            const iframe = document.querySelector(
                'iframe[src*="recaptcha/enterprise/anchor"], '
                + 'iframe[src*="recaptcha/api2/anchor"]'
            );
            return iframe ? iframe.src : null;
        }"""
    )
    return result


def _solve_recaptcha_with_pypasser(
    anchor_url: str,
    *,
    timeout: float = 15.0,
) -> str:
    """Solve a reCAPTCHA V3 / Enterprise challenge via PyPasser.

    Args:
        anchor_url: The anchor URL extracted from the page's reCAPTCHA iframe.
        timeout: HTTP request timeout in seconds (default 15).

    Returns:
        The reCAPTCHA response token string.

    Raises:
        ImportError: If PyPasser is not installed.
    """
    try:
        from pypasser import reCaptchaV3  # type: ignore[import-untyped]
    except ImportError:
        raise ImportError(
            "PyPasser is required for automatic reCAPTCHA solving. "
            "Install it with: pip install PyPasser"
        ) from None

    return reCaptchaV3(anchor_url, timeout=timeout)


def _setup_pypasser_interceptor(page: Any, token: str) -> None:
    """Intercept ``otp.smallcase.com`` POST requests and inject a PyPasser token.

    The browser's JavaScript sends ``recaptchaToken`` in the POST body to
    ``otp.smallcase.com/auth/otp`` and ``otp.smallcase.com/auth/verify``.
    This route handler replaces that field with the supplied PyPasser token
    so the request carries a valid token regardless of the browser widget.
    """
    import json as _json

    def _handle_route(route: Any) -> None:
        request = route.request
        if request.method != "POST":
            route.continue_()
            return

        try:
            body = _json.loads(request.post_data or "{}")
        except (ValueError, _json.JSONDecodeError):
            route.continue_()
            return

        if "recaptchaToken" not in body:
            route.continue_()
            return

        body["recaptchaToken"] = token
        route.continue_(post_data=_json.dumps(body))

    page.route("**/otp.smallcase.com/auth/otp", _handle_route)
    page.route("**/otp.smallcase.com/auth/verify", _handle_route)


def _refresh_pypasser_token(
    page: Any,
    *,
    timeout: float = 15.0,
) -> str:
    """Extract the anchor URL from *page* and generate a fresh PyPasser token.

    Raises:
        RuntimeError: If no reCAPTCHA iframe is found on the page.
        ImportError: If PyPasser is not installed.
    """
    anchor_url = _extract_recaptcha_anchor_url(page)
    if not anchor_url:
        raise RuntimeError(
            "No reCAPTCHA iframe found on the page. "
            "Make sure the login modal is open before calling this."
        )
    return _solve_recaptcha_with_pypasser(anchor_url, timeout=timeout)


def capture_credentials_interactively(
    *,
    output_path: str | Path = DEFAULT_CREDENTIALS_PATH,
    login_url: str = TICKERTAPE_LOGIN_URL,
    headless: bool = False,
    account: str | None = None,
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
        cookies = context.cookies()
        cookie_header = build_cookie_header(cookies)
        cookie_dict_ = build_cookie_dict(cookies)
    finally:
        browser.close()

    return write_credentials_file(
        output_path, cookie_header=cookie_header, cookie_dict=cookie_dict_, account=account
    )


def capture_credentials_via_otp(
    *,
    phone: str,
    country_code: str = "+91",
    otp: str | None = None,
    output_path: str | Path = DEFAULT_CREDENTIALS_PATH,
    headless: bool = False,
    use_pypasser: bool = False,
    skip_send_otp: bool = False,
    account: str | None = None,
) -> Path:
    """Log in to Tickertape via phone-number OTP flow and persist session credentials.

    This automates the full login: opens Tickertape, clicks the login button to
    open the modal, enters phone + country code, requests OTP, enters the OTP,
    and captures cookies / auth token after a successful login.

    When ``use_pypasser=True``, reCAPTCHA Enterprise tokens are generated via
    PyPasser and injected into the ``otp.smallcase.com`` API calls via route
    interception, bypassing the browser's reCAPTCHA widget entirely.

    When ``skip_send_otp=True``, the function assumes the OTP has already been
    sent (e.g. from a previous run) and skips the "Get OTP" button click.
    The browser will still open and fill the phone number, but it expects the
    OTP entry screen to already be active.  Use this when picking up from a
    prior partial login attempt.

    Args:
        phone: The phone number to log in with (digits only, without country code).
        country_code: The country code (default ``"+91"``).
        otp: The OTP code. If ``None`` (default), the function reads the OTP
             interactively from stdin (useful for SMS-delivered codes).
        output_path: Where to write the credentials JSON file.
        headless: Whether to run the browser in headless mode.
        use_pypasser: If ``True``, use PyPasser to generate reCAPTCHA tokens
            instead of relying on the browser widget. Requires ``pip install PyPasser``.
        skip_send_otp: If ``True``, skip the "Get OTP" button click (OTP already sent).

    Returns:
        The path to the credentials file that was written.

    Requires ``playwright`` (``pip install 'tickertape-api-client[auth]'``).
    """
    browser, context, page = _launch_browser(headless=headless)

    try:
        # Step 1: Navigate to Tickertape and open the login modal.
        # The `#login-init` hash no longer auto-opens the modal (the site
        # changed its routing).  We navigate to the homepage and click the
        # "Sign Up / Login" button ourselves.
        page.goto("https://www.tickertape.in/", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        # Click the login button — use JS eval to avoid stale-element / overlay
        # issues that plague Playwright's high-level `click()` with SPAs.
        _btn_clicked = page.evaluate(
            """() => {
                const buttons = document.querySelectorAll('button');
                const matches = [];
                for (const btn of buttons) {
                    const txt = btn.textContent || '';
                    if (/sign\\s*up|login/i.test(txt)) {
                        btn.click();
                        return 'clicked:' + txt.trim();
                    }
                    if (txt.trim()) matches.push(txt.trim().substring(0,30));
                }
                return 'not found. Buttons: ' + JSON.stringify(matches.slice(0,10));
            }"""
        )
        if not _btn_clicked.startswith("clicked:"):
            # Fallback: try Playwright's built-in click
            try:
                _btn = page.wait_for_selector("button:has-text('Sign Up')", timeout=5000)
                if _btn:
                    _btn.click()
                    _btn_clicked = "clicked:fallback"
            except Exception:
                raise RuntimeError(f"Login button not found. Page buttons: {_btn_clicked}")
        page.wait_for_timeout(2000)

        # Step 2: Set country code (if different from default) and fill phone number.
        # Tickertape uses a select/dropdown near the phone input for country code.
        if country_code and country_code != "+91":
            page.evaluate(
                """() => {
                    const ccSelectors = [
                        'select[aria-label*="country" i]',
                        'select[aria-label*="code" i]',
                        'select[name*="country" i]',
                        'select[name*="code" i]',
                        'select[id*="country" i]',
                        '#countryCode',
                        'input[id*="country" i]',
                        'input[name*="country" i]',
                    ];
                    for (const sel of ccSelectors) {
                        const el = document.querySelector(sel);
                        if (!el) continue;
                        const codeValue = '""" + json.dumps(country_code) + """';
                        const nativeSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 'value'
                        ).set;
                        nativeSetter.call(el, codeValue);
                        el.dispatchEvent(new Event('input', {bubbles: true}));
                        el.dispatchEvent(new Event('change', {bubbles: true}));
                        break;
                    }
                }"""
            )
            page.wait_for_timeout(500)

        phone_input = page.wait_for_selector(
            "#phoneNumber", timeout=10_000
        )
        if phone_input is None:
            raise RuntimeError("Phone number input (#phoneNumber) not found on login modal")
        phone_input.fill("")
        phone_input.type(phone, delay=80)
        page.wait_for_timeout(500)

        # ---- PyPasser: intercept reCAPTCHA tokens before "Get OTP" ----
        if use_pypasser and not skip_send_otp:
            _pypasser_token = _refresh_pypasser_token(page)
            _setup_pypasser_interceptor(page, _pypasser_token)

        # Step 3: Click "Get OTP".  Use JS eval so the modal backdrop doesn't
        # intercept the click.
        if not skip_send_otp:
            page.evaluate(
                """() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    if (/get\\s*otp/i.test(btn.textContent || '')) {
                        btn.click(); return;
                    }
                }
                throw new Error('"Get OTP" button not found');
            }"""
            )
            page.wait_for_timeout(3000)

        # ---- Read OTP AFTER the "Get OTP" click, so the SMS has been sent ----
        if otp is None and not skip_send_otp:
            import sys as _sys

            if _sys.stdin.isatty():
                otp = input("Enter the OTP sent to your phone: ").strip()
                if not otp:
                    raise RuntimeError("No OTP entered.") from None
            else:
                # Non-interactive (piped stdin) — read OTP from stdin
                _stdin_data = _sys.stdin.read().strip()
                if _stdin_data:
                    otp = _stdin_data
                else:
                    raise RuntimeError(
                        "OTP required. Re-run with: "
                        "tickertape auth-login <phone> --otp <code>"
                    ) from None

        # Step 4: Enter the OTP digits.  Tickertape uses separate
        # `<input maxlength="1">` fields inside the modal OTP screen
        # (typically 4 fields for 4-digit OTPs).
        # We also handle the single-field fallback for older UI layouts.
        page.evaluate(
            f"""(otpCode) => {{
                // Individual digit inputs (current UI — 4 fields for 4-digit OTP)
                const digitInputs = document.querySelectorAll('input[maxlength="1"]');
                if (digitInputs.length >= 4) {{
                    const digits = String(otpCode);
                    for (let i = 0; i < digitInputs.length && i < digits.length; i++) {{
                        const nativeSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 'value'
                        ).set;
                        nativeSetter.call(digitInputs[i], digits[i]);
                        digitInputs[i].dispatchEvent(new Event('input', {{bubbles: true}}));
                        digitInputs[i].dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                    return;
                }}
                // Fallback: single OTP input field
                const single = document.querySelector(
                    'input[placeholder*="OTP"], '
                    + 'input[placeholder*="otp"], '
                    + 'input[placeholder*="code"]'
                );
                if (single) {{
                    const nativeSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    nativeSetter.call(single, String(otpCode));
                    single.dispatchEvent(new Event('input', {{bubbles: true}}));
                    single.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
            }}""",
            otp,
        )
        page.wait_for_timeout(1000)

        # ---- PyPasser: refresh token before OTP verification ----
        if use_pypasser:
            _pypasser_token = _refresh_pypasser_token(page)
            _setup_pypasser_interceptor(page, _pypasser_token)

        # Step 5: Submit the OTP form.  Look for the verify/submit button.
        page.evaluate(
            """() => {
                const buttons = document.querySelectorAll('button');
                const re = /verify|submit|login|continue|proceed|done/i;
                for (const btn of buttons) {
                    if (re.test(btn.textContent || '')) {
                        btn.click();
                        return;
                    }
                }
            }"""
        )

        # Step 6: Wait for login to succeed.
        # Tickertape sets x-lp-auth / x-us-lp-auth on the login modal itself,
        # BEFORE OTP submission — they are NOT a login-success signal.
        # The real post-login indicators are:
        #   - jwt cookie appears
        #   - URL redirects away from login/auth page
        #   - x-tickertape-user-state becomes "logged-in"
        import time as _time

        _deadline = _time.time() + 30.0
        while _time.time() < _deadline:
            page.wait_for_timeout(1500)
            cookies = context.cookies()
            cookie_dict_ = build_cookie_dict(cookies)
            has_jwt = bool(cookie_dict_.get("jwt"))
            is_logged_in = cookie_dict_.get("x-tickertape-user-state") == "logged-in"
            current_url = page.url
            on_main_page = "login" not in current_url.lower() and "auth" not in current_url.lower()

            if has_jwt and (is_logged_in or on_main_page):
                break
            # Fallback: URL redirect + user-state cookie confirm login
            if on_main_page and is_logged_in:
                page.wait_for_timeout(2000)  # give jwt time to settle
                cookies = context.cookies()
                cookie_dict_ = build_cookie_dict(cookies)
                break
        else:
            error_el = page.query_selector('[class*="error"], [class*="Error"]')
            error_text = error_el.text_content() if error_el else "no error message found"
            raise RuntimeError(
                f"Login failed — no auth cookies appeared after 30s. "
                f"Page error: {error_text}. The OTP may be incorrect or expired."
            )

        cookie_header = build_cookie_header(cookies)
        cookie_dict_ = build_cookie_dict(cookies)
    finally:
        browser.close()

    return write_credentials_file(
        output_path, cookie_header=cookie_header, cookie_dict=cookie_dict_, account=account
    )
