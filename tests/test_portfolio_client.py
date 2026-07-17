import base64
import json
import time
from pathlib import Path
from typing import Any

import pytest

from tickertape_api.exceptions import TickertapeHTTPError
from tickertape_api.portfolio_client import PortfolioClient


def _jwt(exp_offset_seconds: int = 60, **extra: Any) -> str:
    header = {"alg": "none", "typ": "JWT"}
    payload = {"exp": int(time.time()) + exp_offset_seconds, **extra}

    def enc(obj: dict[str, Any]) -> str:
        raw = json.dumps(obj, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    return f"{enc(header)}.{enc(payload)}.sig"


class _Response:
    def __init__(
        self,
        status_code: int,
        *,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        reason: str = "",
    ) -> None:
        self.status_code = status_code
        self._data = data or {}
        self.headers = headers or {}
        self.reason = reason
        self.text = json.dumps(self._data)
        self.ok = 200 <= status_code < 400

    def json(self) -> dict[str, Any]:
        return self._data


class _Session:
    def __init__(self) -> None:
        self.posts: list[dict[str, Any]] = []
        self.requests: list[dict[str, Any]] = []
        self.post_response = _Response(
            200,
            data={"jwt": _jwt(86_400), "csrfToken": "new-csrf", "expire": 86_400},
            headers={"set-cookie": "jwt=set-cookie-jwt; Path=/; HttpOnly"},
        )
        self.request_responses: list[_Response] = []

    def post(self, url: str, **kwargs: Any) -> _Response:
        self.posts.append({"url": url, **kwargs})
        return self.post_response

    def request(self, method: str, url: str, **kwargs: Any) -> _Response:
        self.requests.append({"method": method, "url": url, **kwargs})
        if self.request_responses:
            return self.request_responses.pop(0)
        return _Response(200, data={"success": True, "data": {"ok": True}})


def _client(tmp_path: Path, session: _Session) -> PortfolioClient:
    path = tmp_path / "credentials.json"
    old_jwt = _jwt(-60, refreshToken="legacy-refresh-token")
    path.write_text(
        json.dumps(
            {
                "accounts": {
                    "primary": {
                        "cookie_dict": {
                            "jwt": old_jwt,
                            "x-csrf-token-tickertape-prod": "old-csrf",
                        },
                        "cookie_header": f"jwt={old_jwt}; x-csrf-token-tickertape-prod=old-csrf",
                    },
                    "family": {"cookie_dict": {"jwt": "untouched"}},
                }
            }
        )
    )

    client = PortfolioClient.__new__(PortfolioClient)
    client.impersonate = "chrome124"
    client.timeout = 15.0
    client.cookie_dict = {
        "jwt": old_jwt,
        "x-csrf-token-tickertape-prod": "old-csrf",
    }
    client.csrf_token = "old-csrf"
    client._credentials_file = path
    client._account = "primary"
    client._session = session
    return client


def test_refresh_uses_browser_cookie_shape_and_persists_new_jwt_and_csrf(tmp_path: Path) -> None:
    session = _Session()
    client = _client(tmp_path, session)

    assert client._refresh_jwt_if_needed() is True

    assert len(session.posts) == 1
    post = session.posts[0]
    assert post["url"] == "https://auth.api.tickertape.in/auth/refresh"
    assert "json" not in post
    assert post["cookies"]["jwt"]

    assert client.cookie_dict["jwt"] == session.post_response.json()["jwt"]
    assert client.cookie_dict["x-csrf-token-tickertape-prod"] == "new-csrf"
    assert client.csrf_token == "new-csrf"

    saved = json.loads(client._credentials_file.read_text())
    assert saved["accounts"]["primary"]["cookie_dict"]["jwt"] == session.post_response.json()["jwt"]
    assert saved["accounts"]["primary"]["cookie_dict"]["x-csrf-token-tickertape-prod"] == "new-csrf"
    assert saved["accounts"]["family"] == {"cookie_dict": {"jwt": "untouched"}}


def test_request_refreshes_and_retries_once_after_401(tmp_path: Path) -> None:
    session = _Session()
    session.request_responses = [
        _Response(401, data={"message": "expired"}, reason="Unauthorized"),
        _Response(200, data={"success": True, "data": {"retried": True}}),
    ]
    client = _client(tmp_path, session)
    client.cookie_dict["jwt"] = _jwt(86_400)

    assert client._request("GET", "https://api.tickertape.in/user/profile") == {
        "success": True,
        "data": {"retried": True},
    }

    assert len(session.posts) == 1
    assert len(session.requests) == 2
    assert session.requests[1]["headers"]["x-csrf-token"] == "new-csrf"


def test_request_raises_original_401_when_refresh_fails(tmp_path: Path) -> None:
    session = _Session()
    session.post_response = _Response(401, data={"message": "refresh expired"}, reason="Unauthorized")
    session.request_responses = [
        _Response(401, data={"message": "expired"}, reason="Unauthorized"),
    ]
    client = _client(tmp_path, session)
    client.cookie_dict["jwt"] = _jwt(86_400)

    with pytest.raises(TickertapeHTTPError) as exc:
        client._request("GET", "https://api.tickertape.in/user/profile")

    assert exc.value.status_code == 401
    assert len(session.posts) == 1
    assert len(session.requests) == 1
