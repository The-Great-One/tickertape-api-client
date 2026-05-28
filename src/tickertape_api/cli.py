"""Small command-line utility for quick endpoint checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

from .auth_capture import (
    DEFAULT_CREDENTIALS_PATH,
    capture_credentials_interactively,
    write_credentials_file,
)
from .client import TickertapeClient


def _print(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query public Tickertape endpoints")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("market-status", help="Get market status")
    p.add_argument("market", nargs="?", default="IN", choices=["IN", "US"])

    p = sub.add_parser("quote", help="Get India quotes by SID")
    p.add_argument("sids", nargs="+")

    p = sub.add_parser("us-quote", help="Get US latest quotes by ticker")
    p.add_argument("tickers", nargs="+")

    p = sub.add_parser("us-chart", help="Get US security chart")
    p.add_argument("ticker")
    p.add_argument("--duration", default="1y")

    p = sub.add_parser("mf-holdings", help="Get mutual fund holdings by mfId")
    p.add_argument("mf_id")

    p = sub.add_parser("mf-search", help="Search local MF universe from Tickertape list")
    p.add_argument("text")
    p.add_argument("--limit", type=int, default=10)

    p = sub.add_parser(
        "auth-capture",
        help="Open Tickertape in a browser and save logged-in session credentials",
    )
    p.add_argument("--out", default=str(DEFAULT_CREDENTIALS_PATH), help="Credentials JSON path")
    p.add_argument("--headless", action="store_true", help="Run browser headlessly")

    p = sub.add_parser(
        "auth-set",
        help="Save Tickertape auth token/cookie from CLI args or stdin without opening a browser",
    )
    p.add_argument("--token", help="Bearer token copied from a logged-in Tickertape session")
    p.add_argument("--token-stdin", action="store_true", help="Read bearer token from stdin")
    p.add_argument("--cookie", help="Raw Cookie header copied from a logged-in Tickertape session")
    p.add_argument("--cookie-stdin", action="store_true", help="Read raw Cookie header from stdin")
    p.add_argument("--out", default=str(DEFAULT_CREDENTIALS_PATH), help="Credentials JSON path")

    p = sub.add_parser("auth-status", help="Show whether stored Tickertape credentials exist")
    p.add_argument("--path", default=str(DEFAULT_CREDENTIALS_PATH), help="Credentials JSON path")

    args = parser.parse_args(argv)
    if args.cmd == "auth-capture":
        path = capture_credentials_interactively(output_path=args.out, headless=args.headless)
        print(f"Saved Tickertape credentials to {path}")
        return 0
    if args.cmd == "auth-set":
        token = sys.stdin.read().strip() if args.token_stdin else args.token
        cookie = sys.stdin.read().strip() if args.cookie_stdin else args.cookie
        path = write_credentials_file(args.out, auth_token=token, cookie_header=cookie)
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

    with TickertapeClient.from_env() as client:
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
