"""Small command-line utility for quick endpoint checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

from . import auth_capture
from .auth_capture import (
    DEFAULT_CREDENTIALS_PATH,
    capture_credentials_interactively,
    write_credentials_file,
)
from .client import TickertapeClient
from .portfolio_client import PortfolioClient


def _print(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query public Tickertape endpoints")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Shared parent parser with --account flag for all subcommands
    account_parent = argparse.ArgumentParser(add_help=False)
    account_parent.add_argument(
        "--account", default=None,
        help="Named account from credentials file's 'accounts' dict. "
             "Uses TICKERTAPE_ACCOUNT env var if set, otherwise first entry.",
    )

    p = sub.add_parser("market-status", parents=[account_parent], help="Get market status")
    p.add_argument("market", nargs="?", default="IN", choices=["IN", "US"])

    p = sub.add_parser("quote", parents=[account_parent], help="Get India quotes by SID")
    p.add_argument("sids", nargs="+")

    p = sub.add_parser("us-quote", parents=[account_parent], help="Get US latest quotes by ticker")
    p.add_argument("tickers", nargs="+")

    p = sub.add_parser("us-chart", parents=[account_parent], help="Get US security chart")
    p.add_argument("ticker")
    p.add_argument("--duration", default="1y")

    p = sub.add_parser("mf-holdings", parents=[account_parent], help="Get mutual fund holdings by mfId")
    p.add_argument("mf_id")

    p = sub.add_parser("mf-search", parents=[account_parent], help="Search local MF universe from Tickertape list")
    p.add_argument("text")
    p.add_argument("--limit", type=int, default=10)

    p = sub.add_parser(
        "auth-capture", parents=[account_parent],
        help="Open Tickertape in a browser and save logged-in session credentials",
    )
    p.add_argument("--out", default=str(DEFAULT_CREDENTIALS_PATH), help="Credentials JSON path")
    p.add_argument("--headless", action="store_true", help="Run browser headlessly")

    p = sub.add_parser(
        "auth-set", parents=[account_parent],
        help="Save Tickertape auth token/cookie from CLI args or stdin without opening a browser",
    )
    p.add_argument("--token", help="Bearer token copied from a logged-in Tickertape session")
    p.add_argument("--token-stdin", action="store_true", help="Read bearer token from stdin")
    p.add_argument("--cookie", help="Raw Cookie header copied from a logged-in Tickertape session")
    p.add_argument("--cookie-stdin", action="store_true", help="Read raw Cookie header from stdin")
    p.add_argument("--out", default=str(DEFAULT_CREDENTIALS_PATH), help="Credentials JSON path")

    p = sub.add_parser("auth-status", parents=[account_parent], help="Show whether stored Tickertape credentials exist")
    p.add_argument("--path", default=str(DEFAULT_CREDENTIALS_PATH), help="Credentials JSON path")

    p = sub.add_parser(
        "auth-login", parents=[account_parent],
        help="Log in to Tickertape via phone-number OTP and save credentials",
    )
    p.add_argument("phone", help="Phone number (digits only, without country code)")
    p.add_argument(
        "--country-code", default="+91", help="Country code (default: +91)"
    )
    p.add_argument("--otp", default=None, help="4-digit OTP (reads from stdin if omitted)")
    p.add_argument(
        "--out", default=str(DEFAULT_CREDENTIALS_PATH), help="Credentials JSON path"
    )
    p.add_argument("--headless", action="store_true", help="Run browser headlessly")
    p.add_argument(
        "--pypasser", action="store_true",
        help="Use PyPasser to generate reCAPTCHA tokens (requires: pip install PyPasser)",
    )
    p.add_argument(
        "--skip-send-otp", action="store_true",
        help="Skip 'Get OTP' click — OTP was already sent in a previous run",
    )

    p = sub.add_parser(
        "auth-browserless", parents=[account_parent],
        help="Hybrid auth: browserless token + lightweight browser for reCAPTCHA",
    )
    p.add_argument(
        "phone",
        help="Phone number (digits only). Use 'phone:otp' to pass both at once (e.g. 9876543210:1234)",
    )
    p.add_argument(
        "--country-code", default="+91", help="Country code (default: +91)"
    )
    p.add_argument(
        "--otp", default=None, help="4-digit OTP code (can also be passed as phone:otp)"
    )
    p.add_argument(
        "--out", default=str(DEFAULT_CREDENTIALS_PATH), help="Credentials JSON path"
    )
    p.add_argument("--headless", action="store_true", help="Run browser headlessly")

    # ---- portfolio commands ----
    p = sub.add_parser("portfolio-summary", parents=[account_parent], help="User portfolio summary (MF + stocks + watchlists)")
    p = sub.add_parser("portfolio-mf", parents=[account_parent], help="User mutual fund holdings")
    p = sub.add_parser("portfolio-stocks", parents=[account_parent], help="User stock/equity holdings")
    p = sub.add_parser("portfolio-watchlists", parents=[account_parent], help="User watchlists")
    p = sub.add_parser("portfolio-quotes", parents=[account_parent], help="Live quotes for portfolio stocks")

    p = sub.add_parser(
        "refresh-all", parents=[account_parent],
        help="Refresh portfolio data for ALL accounts and print summary",
    )
    p.add_argument("--out", default=None, help="Optional JSON output path for cache file")

    args = parser.parse_args(argv)
    if args.cmd == "auth-capture":
        path = capture_credentials_interactively(
            output_path=args.out, headless=args.headless, account=args.account
        )
        print(f"Saved Tickertape credentials to {path}")
        return 0
    if args.cmd == "auth-login":
        path = auth_capture.capture_credentials_via_otp(
            phone=args.phone,
            country_code=args.country_code,
            otp=args.otp,
            output_path=args.out,
            headless=args.headless,
            use_pypasser=args.pypasser,
            skip_send_otp=args.skip_send_otp,
            account=args.account,
        )
        print(f"Saved Tickertape credentials to {path}")
        return 0
    if args.cmd == "auth-browserless":
        phone = args.phone
        otp = args.otp
        if ":" in phone:
            phone, otp = phone.rsplit(":", 1)
        path = auth_capture.capture_credentials_via_hybrid(
            phone=phone,
            country_code=args.country_code,
            otp=otp,
            output_path=args.out,
            headless=args.headless,
            account=args.account,
        )
        print(f"Saved Tickertape credentials to {path}")
        return 0
    if args.cmd == "auth-set":
        # Read stdin once if either stdin flag is set; parse both values from it.
        stdin_data: str | None = None
        if args.token_stdin or args.cookie_stdin:
            stdin_data = sys.stdin.read().strip()
        token = stdin_data if args.token_stdin else args.token
        cookie = stdin_data if args.cookie_stdin else args.cookie
        path = write_credentials_file(
            args.out, auth_token=token, cookie_header=cookie, account=args.account
        )
        print(f"Saved Tickertape credentials to {path}")
        return 0
    if args.cmd == "auth-status":
        path = Path(args.path).expanduser()
        exists = path.exists()
        print(f"path: {path}")
        print(f"exists: {'yes' if exists else 'no'}")
        if exists:
            payload = json.loads(path.read_text())
            if not isinstance(payload, dict):
                raise TypeError("Credentials file must contain a JSON object")
            print(f"auth_token: {'yes' if payload.get('auth_token') or payload.get('token') else 'no'}")
            print(
                "cookie_header: "
                f"{'yes' if payload.get('cookie_header') or payload.get('cookie') else 'no'}"
            )
        return 0

    # ---- portfolio commands (authenticated) ----
    if args.cmd == "refresh-all":
        from datetime import datetime, timedelta, timezone
        ist = timezone(timedelta(hours=5, minutes=30))
        cached_at = datetime.now(ist).isoformat()

        all_accounts = {}
        errors = []
        for portfolio_client in PortfolioClient.iter_accounts():
            name = portfolio_client._account or "default"
            try:
                status = portfolio_client.holdings_status()
                mf = portfolio_client.mf_holdings()
                us_assets = [a for a in status.get("assetsStatus", []) if a.get("type") == "US_STOCK"]
                us_count = len(us_assets[0].get("meta", {}).get("constituents", [])) if us_assets else 0
                mf_count = len(mf.get("mfHoldings", [])) if isinstance(mf, dict) else 0
                stock_assets = [a for a in status.get("assetsStatus", []) if a.get("type") == "STOCK"]
                stock_count = len(stock_assets[0].get("meta", {}).get("constituents", [])) if stock_assets else 0
                all_accounts[name] = {
                    "holdings_status": status,
                    "mf_holdings": mf,
                    "cached_at": cached_at,
                }
                print(f"  {name}: {stock_count} stocks, {us_count} US, {mf_count} MF")
            except Exception as e:
                errors.append(f"{name}: {type(e).__name__}: {e}")
                print(f"  {name}: FAILED — {type(e).__name__}: {e}")

        total = len(all_accounts)
        print(f"\n{total}/{total + len(errors)} accounts OK")

        if args.out:
            cache = {
                "accounts": all_accounts,
                "cached_at": cached_at,
                "source": "v3 multi-account",
            }
            out_path = Path(args.out).expanduser()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(cache, indent=2, default=str))
            print(f"Cache written to {out_path}")

        if errors:
            for err in errors:
                print(f"  ⚠️  {err}", file=sys.stderr)
            return 1
        return 0

    if args.cmd.startswith("portfolio"):
        with PortfolioClient(account=args.account) as pc:
            if args.cmd == "portfolio-summary":
                _print(pc.portfolio_summary())
            elif args.cmd == "portfolio-mf":
                _print(pc.mf_holdings())
            elif args.cmd == "portfolio-stocks":
                _print(pc.stock_holdings())
            elif args.cmd == "portfolio-watchlists":
                _print(pc.watchlists())
            elif args.cmd == "portfolio-quotes":
                _print(pc.quote_portfolio())
        return 0

    with TickertapeClient.from_env(account=args.account) as client:
        if args.cmd == "market-status":
            _print(client.market_status(args.market))
        elif args.cmd == "quote":
            _print(client.india_quotes(args.sids))
        elif args.cmd == "us-quote":
            _print(client.us_latest_quotes(args.tickers))
        elif args.cmd == "us-chart":
            _print(client.us_security_chart(args.ticker, args.duration))
        elif args.cmd == "mf-holdings":
            _print(client.mutual_fund_holdings(args.mf_id))
        elif args.cmd == "mf-search":
            text = args.text.lower()
            mf_payload = client.mutual_funds_list()
            if not isinstance(mf_payload, dict):
                raise TypeError("Expected mutual fund list payload to be an object")
            universe = cast(list[dict[str, Any]], mf_payload.get("universe", []))
            matches = [
                row
                for row in universe
                if text in row.get("name", "").lower()
                or text in row.get("fullName", "").lower()
                or text in row.get("mfId", "").lower()
                or text in row.get("isin", "").lower()
            ]
            _print(matches[: args.limit])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
