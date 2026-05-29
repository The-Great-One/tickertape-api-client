"""Test: cookie-only auth with exact headers matching browser XHR."""
import json
from pathlib import Path

from curl_cffi import requests as curl_requests

creds_path = Path.home() / ".config" / "tickertape-api-client" / "credentials.json"
creds = json.loads(creds_path.read_text())
cookie_header = creds.get("cookie_header", "")

# Parse ALL cookies
cookies = {}
csrf_token = None
for pair in cookie_header.split("; "):
    if "=" in pair:
        name, _, value = pair.partition("=")
        cookies[name.strip()] = value.strip()
        if "csrf" in name.lower():
            csrf_token = value.strip()

# Exact browser headers (no Authorization!)
headers = {
    "accept": "application/json, text/plain, */*",
    "accept-version": "8.14.0",
    "x-csrf-token": csrf_token,
    "x-device-type": "web",
    "referer": "https://www.tickertape.in/portfolio/mutualfunds",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
}

endpoints = [
    ("MF Holdings", "https://api.tickertape.in/user/mfholdings"),
    ("Holdings Status", "https://ecosystem.api.tickertape.in/portfolio/v2/holdings/status"),
    ("Watchlists Stocks", "https://ecosystem.api.tickertape.in/watchlists?assetClass=SECURITY&market=IN,US"),
]

for impersonate in ["chrome124", "chrome131", "chrome145"]:
    print(f"\n=== impersonate={impersonate} ===")
    ok_count = 0
    for label, url in endpoints:
        try:
            r = curl_requests.get(url, cookies=cookies, headers=headers, impersonate=impersonate, timeout=15)
            ok = "✓" if r.ok else "✗"
            if r.ok:
                body = r.json()
                preview = json.dumps(body, ensure_ascii=False)[:200]
                print(f"  {ok} {r.status_code} {label} -> {preview}")
                ok_count += 1
            else:
                print(f"  {ok} {r.status_code} {label} -> {r.text[:150]}")
        except Exception as e:
            print(f"  ✗ {label}: {e}")
    print(f"  -> {ok_count}/{len(endpoints)} OK")
    if ok_count == len(endpoints):
        print("  *** ALL PASS ***")
        break
