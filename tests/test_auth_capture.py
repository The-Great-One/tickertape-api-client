import json
import stat

from tickertape_api.auth_capture import (
    build_cookie_header,
    write_credentials_file,
)


def test_build_cookie_header_includes_tickertape_cookie_domains_only():
    cookies = [
        {"name": "session", "value": "abc", "domain": ".tickertape.in"},
        {"name": "quote", "value": "xyz", "domain": "quotes-api.tickertape.in"},
        {"name": "other", "value": "nope", "domain": "example.com"},
    ]

    assert build_cookie_header(cookies) == "session=abc; quote=xyz"


def test_write_credentials_file_uses_private_permissions(tmp_path):
    path = tmp_path / "credentials.json"

    write_credentials_file(path, cookie_header="sid=abc", cookie_dict={"jwt": "eyJ..."})

    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert json.loads(path.read_text()) == {
        "cookie_header": "sid=abc",
        "cookie_dict": {"jwt": "eyJ..."},
    }
