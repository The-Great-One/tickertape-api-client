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
