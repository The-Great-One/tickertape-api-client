import json

from tickertape_api import cli


def test_auth_set_writes_credentials_from_cli_args(tmp_path, capsys):
    out = tmp_path / "credentials.json"

    exit_code = cli.main([
        "auth-set",
        "--token",
        "token-123",
        "--cookie",
        "sid=abc",
        "--out",
        str(out),
    ])

    assert exit_code == 0
    assert json.loads(out.read_text()) == {"auth_token": "token-123", "cookie_header": "sid=abc"}
    assert "Saved Tickertape credentials" in capsys.readouterr().out


def test_auth_set_can_read_cookie_from_stdin(tmp_path, monkeypatch):
    out = tmp_path / "credentials.json"
    monkeypatch.setattr("sys.stdin.read", lambda: "sid=stdin-cookie\n")

    exit_code = cli.main(["auth-set", "--cookie-stdin", "--out", str(out)])

    assert exit_code == 0
    assert json.loads(out.read_text()) == {"cookie_header": "sid=stdin-cookie"}


def test_auth_status_reports_credentials_file_presence(tmp_path, capsys):
    out = tmp_path / "credentials.json"
    out.write_text(json.dumps({"auth_token": "token", "cookie_header": "sid=abc"}))

    exit_code = cli.main(["auth-status", "--path", str(out)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "exists: yes" in output
    assert "auth_token: yes" in output
    assert "cookie_header: yes" in output


# ---------------------------------------------------------------------------
# auth-login CLI tests
# ---------------------------------------------------------------------------


def test_auth_login_requires_phone_number():
    """auth-login with no phone number should exit with error."""
    with __import__("pytest").raises(SystemExit):
        cli.main(["auth-login"])


def test_auth_login_accepts_phone(tmp_path, monkeypatch, capsys):
    """auth-login with just a phone number should be valid."""
    from tickertape_api import auth_capture

    out = tmp_path / "credentials.json"

    def fake_login(*, phone, country_code, otp, output_path, headless=False,
                   use_pypasser=False, skip_send_otp=False, account=None):
        return auth_capture.write_credentials_file(
            output_path, auth_token="fake-token", cookie_header="sid=fake"
        )

    monkeypatch.setattr(auth_capture, "capture_credentials_via_otp", fake_login)

    exit_code = cli.main(["auth-login", "+919****3210", "--out", str(out)])

    assert exit_code == 0
    assert "Saved Tickertape credentials" in capsys.readouterr().out
    assert json.loads(out.read_text()) == {"auth_token": "fake-token", "cookie_header": "sid=fake"}


def test_auth_login_accepts_otp_flag(tmp_path, monkeypatch):
    """auth-login should accept --otp for non-interactive OTP entry."""
    from tickertape_api import auth_capture

    out = tmp_path / "credentials.json"
    received_otp: list[str] = []

    def fake_login(*, phone, country_code, otp, output_path, headless=False,
                   use_pypasser=False, skip_send_otp=False, account=None):
        received_otp.append(otp)
        return auth_capture.write_credentials_file(
            output_path, auth_token="t", cookie_header="c=x"
        )

    monkeypatch.setattr(auth_capture, "capture_credentials_via_otp", fake_login)

    exit_code = cli.main(["auth-login", "+919****3210", "--otp", "123456", "--out", str(out)])

    assert exit_code == 0
    assert received_otp == ["123456"]


def test_auth_login_accepts_country_code(tmp_path, monkeypatch):
    """auth-login should accept --country-code (default +91)."""
    from tickertape_api import auth_capture

    out = tmp_path / "credentials.json"
    received_cc: list[str] = []

    def fake_login(*, phone, country_code, otp, output_path, headless=False,
                   use_pypasser=False, skip_send_otp=False, account=None):
        received_cc.append(country_code)
        return auth_capture.write_credentials_file(
            output_path, auth_token="t", cookie_header="c=x"
        )

    monkeypatch.setattr(auth_capture, "capture_credentials_via_otp", fake_login)

    exit_code = cli.main(
        ["auth-login", "9876543210", "--country-code", "+1", "--otp", "111111", "--out", str(out)]
    )

    assert exit_code == 0
    assert received_cc == ["+1"]


def test_auth_login_country_code_defaults_to_91(tmp_path, monkeypatch):
    """auth-login --country-code should default to +91 when omitted."""
    from tickertape_api import auth_capture

    out = tmp_path / "credentials.json"
    received_cc: list[str] = []

    def fake_login(*, phone, country_code, otp, output_path, headless=False,
                   use_pypasser=False, skip_send_otp=False, account=None):
        received_cc.append(country_code)
        return auth_capture.write_credentials_file(
            output_path, auth_token="t", cookie_header="c=x"
        )

    monkeypatch.setattr(auth_capture, "capture_credentials_via_otp", fake_login)

    cli.main(["auth-login", "9876543210", "--otp", "222222", "--out", str(out)])

    assert received_cc == ["+91"]


def test_auth_login_pypasser_flag(tmp_path, monkeypatch):
    """auth-login --pypasser should pass use_pypasser=True."""
    from tickertape_api import auth_capture

    out = tmp_path / "credentials.json"
    received_pypasser: list[bool] = []

    def fake_login(*, phone, country_code, otp, output_path, headless=False,
                   use_pypasser=False, skip_send_otp=False, account=None):
        received_pypasser.append(use_pypasser)
        return auth_capture.write_credentials_file(
            output_path, auth_token="t", cookie_header="c=x"
        )

    monkeypatch.setattr(auth_capture, "capture_credentials_via_otp", fake_login)

    cli.main(["auth-login", "9876543210", "--otp", "3333", "--pypasser", "--out", str(out)])

    assert received_pypasser == [True]


# ---------------------------------------------------------------------------
# Multi-account CLI tests
# ---------------------------------------------------------------------------


def test_auth_set_with_account_writes_to_named_slot(tmp_path, capsys):
    """auth-set --account dad writes to accounts.dad slot."""
    out = tmp_path / "credentials.json"
    exit_code = cli.main([
        "auth-set", "--token", "tok-dad", "--cookie", "sid=dad",
        "--account", "dad", "--out", str(out),
    ])
    assert exit_code == 0
    data = json.loads(out.read_text())
    assert "accounts" in data
    assert data["accounts"]["dad"]["auth_token"] == "tok-dad"
    assert data["accounts"]["dad"]["cookie_header"] == "sid=dad"


def test_auth_set_without_account_still_writes_flat(tmp_path, capsys):
    """auth-set without --account writes flat (backward compat)."""
    out = tmp_path / "credentials.json"
    exit_code = cli.main([
        "auth-set", "--token", "tok", "--cookie", "sid=abc",
        "--out", str(out),
    ])
    assert exit_code == 0
    data = json.loads(out.read_text())
    assert "accounts" not in data
    assert data["auth_token"] == "tok"


def test_auth_set_with_account_preserves_other_accounts(tmp_path, capsys):
    """Writing to one account slot doesn't clobber other accounts."""
    out = tmp_path / "credentials.json"
    # Pre-populate with two accounts
    out.write_text(json.dumps({
        "accounts": {
            "primary": {"auth_token": "tok-primary", "cookie_header": "sid=primary"},
            "dad":   {"auth_token": "tok-dad-old", "cookie_header": "sid=dad-old"},
        }
    }))

    # Update dad's credentials
    exit_code = cli.main([
        "auth-set", "--token", "tok-dad-new", "--cookie", "sid=dad-new",
        "--account", "dad", "--out", str(out),
    ])
    assert exit_code == 0
    data = json.loads(out.read_text())
    # primary's slot untouched
    assert data["accounts"]["primary"]["auth_token"] == "tok-primary"
    # dad's slot updated
    assert data["accounts"]["dad"]["auth_token"] == "tok-dad-new"
    assert data["accounts"]["dad"]["cookie_header"] == "sid=dad-new"
