"""Shared credential-file reading with multi-account support."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CREDENTIALS_PATH = Path.home() / ".config" / "tickertape-api-client" / "credentials.json"


def read_credentials_file(
    path: str | os.PathLike[str] | None = None,
    *,
    account: str | None = None,
) -> dict[str, Any]:
    """Read Tickertape credentials from a JSON file with optional account selection.

    Supports two formats:

    1. **Flat keys** (backward compatible)::

        {"cookie_header": "...", "cookie_dict": {...}, "auth_token": "..."}

    2. **Named accounts** (multi-account)::

        {
          "accounts": {
            "sahil": {"cookie_header": "...", "cookie_dict": {...}},
            "dad":   {"cookie_header": "...", "cookie_dict": {...}}
          }
        }

    When ``"accounts"`` is present, *account* selects the named entry.
    If *account* is ``None``, the ``TICKERTAPE_ACCOUNT`` environment variable
    is consulted, then falls back to the first key in ``"accounts"``.
    When ``"accounts"`` is absent, the top-level keys are returned directly
    regardless of *account* (backward compatible).

    Returns:
        A dict of credential keys for the selected account, or an empty dict
        if the file doesn't exist.
    """
    credentials_path = (
        Path(path).expanduser() if path else DEFAULT_CREDENTIALS_PATH
    )
    if not credentials_path.exists():
        return {}

    try:
        payload = json.loads(credentials_path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(payload, dict):
        return {}

    accounts = payload.get("accounts")
    if isinstance(accounts, dict) and accounts:
        # --- multi-account mode ---
        if account is None:
            account = os.getenv("TICKERTAPE_ACCOUNT")
        if account is None:
            account = next(iter(accounts))
        if account not in accounts:
            raise KeyError(
                f"Account {account!r} not found in credentials file. "
                f"Available: {sorted(accounts)}"
            )
        entry = accounts[account]
        if not isinstance(entry, dict):
            raise TypeError(
                f"Account {account!r} entry must be a JSON object, got {type(entry).__name__}"
            )
        return dict(entry)

    # --- backward-compatible flat mode ---
    return dict(payload)


def list_accounts(
    path: str | os.PathLike[str] | None = None,
) -> list[str]:
    """Return all account names from the credentials file.

    Returns an empty list when the file is in flat format (no ``"accounts"`` key).
    """
    credentials_path = (
        Path(path).expanduser() if path else DEFAULT_CREDENTIALS_PATH
    )
    if not credentials_path.exists():
        return []
    try:
        payload = json.loads(credentials_path.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, dict):
        return []
    accounts = payload.get("accounts")
    if isinstance(accounts, dict):
        return sorted(accounts)
    return []


def normalize_credential_keys(raw: dict[str, Any]) -> dict[str, str]:
    """Normalize legacy key names to canonical form.

    Maps ``token`` → ``auth_token``, ``cookie`` → ``cookie_header``.
    Returns a dict with only string values.
    """
    credentials: dict[str, str] = {}
    for source_key, target_key in (
        ("auth_token", "auth_token"),
        ("token", "auth_token"),
        ("cookie_header", "cookie_header"),
        ("cookie", "cookie_header"),
    ):
        value = raw.get(source_key)
        if isinstance(value, str) and value.strip() and target_key not in credentials:
            credentials[target_key] = value.strip()
    return credentials
