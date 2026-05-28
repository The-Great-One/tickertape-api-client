"""Capture full API response bodies via response interception, save to file."""
import json
from pathlib import Path
from cloakbrowser import launch

creds = json.loads(
    Path.home().joinpath(".config/tickertape-api-client/credentials.json").read_text()
)
cookie_header = creds.get("cookie_header", "")

cookies = []
for pair in cookie_header.split("; "):
    if "=" in pair:
        name, _, value = pair.partition("=")
        cookies.append({
            "name": name.strip(), "value": value.strip(),
            "domain": ".tickertape.in", "path": "/",
        })

browser = launch(headless=False, humanize=True)
context = browser.new_context()
context.add_cookies(cookies)
page = context.new_page()

# Store captured responses with full bodies
captured = {}
captured_urls = {}

def handle_response(response):
    url = response.url
    keywords = {
        'mfholdings/commentary': 'mf_commentary',
        'user/mfholdings': 'mf_holdings',
        'holdings/status': 'holdings_status',
        'watchlists?assetClass=SECURITY': 'watchlists_stocks',
        'watchlists?assetClass=MUTUALFUND': 'watchlists_mf',
        'user/basket': 'user_basket',
        'auth/user/v2': 'user_profile',
    }
    for kw, key in keywords.items():
        if kw in url and key not in captured_urls:
            try:
                body = response.text()
                captured[key] = body
                captured_urls[key] = url
                print(f"✓ {response.status} {key} ({len(body)} bytes)")
            except:
                pass

page.on('response', handle_response)

# Load portfolio page
page.goto("https://www.tickertape.in/portfolio/mutualfunds", wait_until="load")
page.wait_for_timeout(12000)  # Let all APIs load

print(f"\nCaptured {len(captured)} endpoints")

# Save to file for analysis
output = {}
for key, body in captured.items():
    try:
        output[key] = json.loads(body)
    except:
        output[key] = {"_raw": body[:500]}

out_path = Path.home() / ".hermes" / "tickertape_portfolio_data.json"
out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
print(f"Saved to {out_path}")

# Print summary
for key, data in output.items():
    print(f"\n--- {key} ---")
    if isinstance(data, dict):
        if 'data' in data:
            d = data['data']
            if isinstance(d, dict):
                print(f"  keys: {list(d.keys())[:10]}")
                # Show first few entries for lists
                for k, v in d.items():
                    if isinstance(v, list) and len(v) > 0:
                        print(f"  {k}: list[{len(v)}], first={json.dumps(v[0], ensure_ascii=False)[:200]}")
                    elif not isinstance(v, (list, dict)):
                        print(f"  {k}: {str(v)[:100]}")
            elif isinstance(d, list):
                print(f"  data: list[{len(d)}]")
                if d:
                    print(f"  first: {json.dumps(d[0], ensure_ascii=False)[:200]}")
        else:
            print(f"  keys: {list(data.keys())[:10]}")
    elif isinstance(data, list):
        print(f"  list[{len(data)}]")

browser.close()
