import json
from pathlib import Path

from tickertape_api.credentials_store import (
    normalize_credential_keys,
    read_credentials_file,
)


def test_read_flat_credentials_backward_compat(tmp_path: Path):
    p = tmp_path / "creds.json"
    p.write_text(json.dumps({"cookie_header": "sid=abc", "auth_token": "tok"}))
    result = read_credentials_file(p)
    assert result == {"cookie_header": "sid=abc", "auth_token": "tok"}


def test_read_named_account(tmp_path: Path):
    p = tmp_path / "creds.json"
    p.write_text(json.dumps({
        "accounts": {
            "primary": {"cookie_header": "sid=primary", "cookie_dict": {"jwt": "j1"}},
            "dad":   {"cookie_header": "sid=dad",   "cookie_dict": {"jwt": "j2"}},
        }
    }))
    result = read_credentials_file(p, account="primary")
    assert result == {"cookie_header": "sid=primary", "cookie_dict": {"jwt": "j1"}}

    result2 = read_credentials_file(p, account="dad")
    assert result2 == {"cookie_header": "sid=dad", "cookie_dict": {"jwt": "j2"}}


def test_read_default_account_from_dict(tmp_path: Path):
    p = tmp_path / "creds.json"
    p.write_text(json.dumps({
        "accounts": {
            "primary": {"cookie_header": "sid=primary"},
            "dad":   {"cookie_header": "sid=dad"},
        }
    }))
    result = read_credentials_file(p)  # no account specified
    assert result == {"cookie_header": "sid=primary"}  # first key is default


def test_read_env_var_selects_account(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("TICKERTAPE_ACCOUNT", "dad")
    p = tmp_path / "creds.json"
    p.write_text(json.dumps({
        "accounts": {
            "primary": {"cookie_header": "sid=primary"},
            "dad":   {"cookie_header": "sid=dad"},
        }
    }))
    result = read_credentials_file(p)
    assert result == {"cookie_header": "sid=dad"}


def test_read_missing_account_raises(tmp_path: Path):
    p = tmp_path / "creds.json"
    p.write_text(json.dumps({
        "accounts": {"primary": {"cookie_header": "sid=primary"}}
    }))
    import pytest
    with pytest.raises(KeyError, match="Account 'nobody' not found"):
        read_credentials_file(p, account="nobody")


def test_read_missing_file_returns_empty(tmp_path: Path):
    result = read_credentials_file(tmp_path / "nonexistent.json")
    assert result == {}


def test_normalize_legacy_keys():
    raw = {"token": "tok", "cookie": "sid=abc"}
    result = normalize_credential_keys(raw)
    assert result == {"auth_token": "tok", "cookie_header": "sid=abc"}


def test_normalize_prefers_canonical_keys():
    raw = {"auth_token": "canon", "token": "legacy"}
    result = normalize_credential_keys(raw)
    assert result == {"auth_token": "canon"}  # canonical wins
