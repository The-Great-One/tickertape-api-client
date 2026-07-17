#!/usr/bin/env python3
"""
Generate a reCAPTCHA token via PyPasser and call the Tickertape/Smallcase OTP API.

Usage:
    /opt/homebrew/bin/python3.10 scripts/generate_otp.py

Workflow:
    1. Fetch tickertape.in to get session cookies AND extract reCAPTCHA anchor URL
    2. Pass anchor URL to PyPasser → get reCAPTCHA token
    3. POST token + phone to otp.smallcase.com/auth/otp with session cookies
    4. Print response
"""

import json
import random
import re
import sys
import time

# Try curl_cffi first for anti-bot protection; fall back to plain requests
try:
    import curl_cffi.requests as requests
    print("[*] Using curl_cffi for requests", file=sys.stderr)
    USE_CFFI = True
except ImportError:
    import requests as reqs_mod
    requests = reqs_mod
    print("[*] Using standard requests (curl_cffi not available)", file=sys.stderr)
    USE_CFFI = False

# --- Configuration ---
TICKERTAPE_URL = "https://www.tickertape.in/"
SITE_KEY = "6LfOYXUnAAAAAGSzHVt2ZqEWMGJLSUnIPhqAxKCh"
PHONE = "9920529105"
COUNTRY_CODE = "+91"
OTP_API_URL = "https://otp.smallcase.com/auth/otp"

# Stable anchor URL components (cb is the only rotating param)
ANCHOR_BASE_PARAMS = {
    "ar": "1",
    "k": SITE_KEY,
    "co": "aHR0cHM6Ly93d3cudGlja2VydGFwZS5pbjo0NDM.",
    "hl": "en",
    "v": "hsFBb1u5wWWWkWP4in1ua2cQ",
    "size": "invisible",
    "anchor-ms": "20000",
    "execute-ms": "30000",
}

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


def build_anchor_url(cb: str | None = None) -> str:
    """Build a reCAPTCHA anchor URL with a random cb value."""
    if cb is None:
        cb = str(random.randint(1000000000, 9999999999))
    params = dict(ANCHOR_BASE_PARAMS, cb=cb)
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://www.google.com/recaptcha/enterprise/anchor?{qs}"


def fetch_page_and_cookies() -> tuple[str | None, dict[str, str], str | None]:
    """
    Fetch tickertape.in and return:
      - anchor_url from the page HTML (or None)
      - cookies dict from the response
      - csrf token extracted from cookies (or None)
    """
    print(f"[1] Fetching {TICKERTAPE_URL} ...", file=sys.stderr)
    headers = {
        **BASE_HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        if USE_CFFI:
            resp = requests.get(
                TICKERTAPE_URL,
                headers=headers,
                impersonate="chrome124",
                timeout=20,
            )
        else:
            resp = requests.get(TICKERTAPE_URL, headers=headers, timeout=20)
        resp.raise_for_status()
        html = resp.text

        # --- Extract cookies ---
        cookies: dict[str, str] = {}
        csrf_token: str | None = None

        # resp.cookies from curl_cffi might be a dict or RequestsCookieJar
        # Cookie extraction handled below via hasattr check
        # Extract cookies from response
        if hasattr(resp, 'cookies'):
            cj = resp.cookies
            if hasattr(cj, 'get_dict'):
                cookies = cj.get_dict()
            elif hasattr(cj, 'items'):
                cookies = dict(cj.items())
            else:
                # Iterate
                for c in cj:
                    cookies[c.name] = c.value

        # Also check response headers for Set-Cookie
        set_cookie_headers = resp.headers.get("set-cookie", "")
        if set_cookie_headers:
            # Parse simple cookies
            for part in set_cookie_headers.replace("\n", "").split(";"):
                part = part.strip()
                if "=" in part and not part.lower().startswith(("path=", "domain=", "expires=", "max-age=", "secure", "httponly", "samesite")):
                    name, _, value = part.partition("=")
                    if name.strip() and name.strip().lower() not in ("path", "domain", "expires", "max-age", "secure", "httponly", "samesite"):
                        cookies[name.strip()] = value.strip()

        print(f"[1] Got {len(cookies)} initial cookies", file=sys.stderr)
        for name in cookies:
            print(f"    {name}: {cookies[name][:40]}{'...' if len(cookies[name]) > 40 else ''}", file=sys.stderr)
            if "csrf" in name.lower():
                csrf_token = cookies[name]
                print(f"    -> CSRF token found: {csrf_token[:40]}...", file=sys.stderr)

        # --- Extract reCAPTCHA anchor URL from HTML ---
        anchor_url = None
        pattern = r'src="(https://www\.google\.com/recaptcha/enterprise/anchor\?[^"]+)"'
        matches = re.findall(pattern, html)
        if matches:
            anchor_url = matches[0]
            print(f"[1] Found anchor URL in page HTML: {anchor_url[:80]}...", file=sys.stderr)
        else:
            print("[1] No anchor URL found in HTML, will build manually", file=sys.stderr)

        return anchor_url, cookies, csrf_token

    except Exception as e:
        print(f"[1] Failed to fetch page: {e}", file=sys.stderr)
        print("[1] Falling back to constructing anchor URL manually", file=sys.stderr)
        return None, {}, None


def generate_recaptcha_token(anchor_url: str) -> str:
    """Use PyPasser to solve the reCAPTCHA and return the token."""
    print("[2] Generating reCAPTCHA token via PyPasser...", file=sys.stderr)
    print(f"[2] Anchor URL: {anchor_url[:100]}...", file=sys.stderr)

    from pypasser import reCaptchaV3

    t_start = time.time()
    token = reCaptchaV3(anchor_url, timeout=25)
    elapsed = time.time() - t_start
    print(f"[2] Token generated in {elapsed:.1f}s", file=sys.stderr)
    print(f"[2] Token: {token[:80]}...", file=sys.stderr)
    return token


def call_otp_api(recaptcha_token: str, cookies: dict[str, str], csrf_token: str | None) -> dict:
    """POST to the OTP API and return the parsed response."""
    print(f"\n[3] Calling OTP API: {OTP_API_URL}", file=sys.stderr)
    payload = {
        "recaptchaToken": recaptcha_token,
        "phone": PHONE,
    }
    print(f"[3] Payload: {json.dumps(payload)}", file=sys.stderr)

    # Build Cookie header
    cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.tickertape.in",
        "Referer": "https://www.tickertape.in/",
        **BASE_HEADERS,
    }
    if cookie_header:
        headers["Cookie"] = cookie_header
        print(f"[3] Cookie header: {cookie_header[:120]}...", file=sys.stderr)
    if csrf_token:
        headers["x-csrf-token"] = csrf_token
        print(f"[3] x-csrf-token: {csrf_token}", file=sys.stderr)

    try:
        if USE_CFFI:
            resp = requests.post(
                OTP_API_URL,
                json=payload,
                headers=headers,
                impersonate="chrome124",
                timeout=20,
            )
        else:
            resp = requests.post(
                OTP_API_URL,
                json=payload,
                headers=headers,
                timeout=20,
            )

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"  Status Code : {resp.status_code}", file=sys.stderr)
        print("  Response Headers:", file=sys.stderr)
        for k, v in resp.headers.items():
            print(f"    {k}: {v}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)

        try:
            body = resp.json()
        except json.JSONDecodeError:
            body = {"_raw_text": resp.text}

        return {
            "status_code": resp.status_code,
            "body": body,
        }

    except Exception as e:
        print(f"[3] ERROR calling OTP API: {e}", file=sys.stderr)
        return {"status_code": None, "error": str(e)}


def main():
    print("=" * 60)
    print("  Tickertape OTP Generator (PyPasser + Direct API)")
    print(f"  Phone: {COUNTRY_CODE} {PHONE}")
    print("=" * 60)
    print()

    # Step 1: Fetch page + get cookies
    anchor_url, cookies, csrf_token = fetch_page_and_cookies()
    if anchor_url is None:
        anchor_url = build_anchor_url()
        print("[1] Using constructed anchor URL", file=sys.stderr)

    # Step 2: Generate reCAPTCHA token
    recaptcha_token = generate_recaptcha_token(anchor_url)

    # Step 3: Call OTP API
    result = call_otp_api(recaptcha_token, cookies, csrf_token)

    # Step 4: Print full response
    print("\n" + "=" * 60)
    print("  FULL RESPONSE (JSON)")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 60)

    return result


if __name__ == "__main__":
    main()
