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
# auth-login CLI tests (failing until auth-login subcommand is implemented)
# ---------------------------------------------------------------------------


def test_auth_login_requires_phone_number():
    """auth-login with no phone number should exit with error."""
    with __import__("pytest").raises(SystemExit):
        cli.main(["auth-login"])


def test_auth_login_accepts_phone(tmp_path, monkeypatch, capsys):
    """auth-login with just a phone number should be valid."""
    from tickertape_api import auth_capture

    out = tmp_path / "credentials.json"

    def fake_login(*, phone, country_code, otp, output_path, headless=False):
        return auth_capture.write_credentials_file(
            output_path, auth_token="fake-token", cookie_header="sid=fake"
        )

    monkeypatch.setattr(auth_capture, "capture_credentials_via_otp", fake_login)

    exit_code = cli.main(["auth-login", "+919876543210", "--out", str(out)])

    assert exit_code == 0
    assert "Saved Tickertape credentials" in capsys.readouterr().out
    assert json.loads(out.read_text()) == {"auth_token": "fake-token", "cookie_header": "sid=fake"}


def test_auth_login_accepts_otp_flag(tmp_path, monkeypatch):
    """auth-login should accept --otp for non-interactive OTP entry."""
    from tickertape_api import auth_capture

    out = tmp_path / "credentials.json"
    received_otp: list[str] = []

    def fake_login(*, phone, country_code, otp, output_path, headless=False):
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

    def fake_login(*, phone, country_code, otp, output_path, headless=False):
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

    def fake_login(*, phone, country_code, otp, output_path, headless=False):
        received_cc.append(country_code)
        return auth_capture.write_credentials_file(
            output_path, auth_token="t", cookie_header="c=x"
        )

    monkeypatch.setattr(auth_capture, "capture_credentials_via_otp", fake_login)

    cli.main(["auth-login", "9876543210", "--otp", "222222", "--out", str(out)])

    assert received_cc == ["+91"]
