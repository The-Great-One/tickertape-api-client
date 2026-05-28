import json
import stat

from tickertape_api.auth_capture import (
    build_cookie_header,
    choose_auth_token,
    write_credentials_file,
)


def test_build_cookie_header_includes_tickertape_cookie_domains_only():
    cookies = [
        {"name": "session", "value": "abc", "domain": ".tickertape.in"},
        {"name": "quote", "value": "xyz", "domain": "quotes-api.tickertape.in"},
        {"name": "other", "value": "nope", "domain": "example.com"},
    ]

    assert build_cookie_header(cookies) == "session=abc; quote=xyz"


def test_choose_auth_token_prefers_jwt_like_values_from_storage():
    storage = {
        "theme": "dark",
        "accessToken": "not-a-jwt",
        "authToken": "eyJhbGciOiJIUzI1NiJ9.payload.signature",
    }

    assert choose_auth_token(storage) == "eyJhbGciOiJIUzI1NiJ9.payload.signature"


def test_write_credentials_file_uses_private_permissions(tmp_path):
    path = tmp_path / "credentials.json"

    write_credentials_file(path, auth_token="token", cookie_header="sid=abc")

    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert json.loads(path.read_text()) == {"auth_token": "token", "cookie_header": "sid=abc"}
