import httpx
import pytest
import respx

from tickertape_api import TickertapeClient
from tickertape_api.exceptions import TickertapeAPIError, TickertapeHTTPError


def test_market_status_fetches_public_endpoint():
    with respx.mock(assert_all_called=True) as rsps:
        route = rsps.get("https://gms-api.tickertape.in/market/IN/status").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {"isOpen": False}})
        )
        client = TickertapeClient()
        assert client.market_status("IN") == {"isOpen": False}
        assert route.called


def test_us_latest_quotes_supports_multiple_tickers():
    with respx.mock(assert_all_called=True) as rsps:
        rsps.get("https://gms-api.tickertape.in/quotes/US/latest?tickers=IXIC%2CAXP").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {"IXIC": {"p": 1}}})
        )
        assert TickertapeClient().us_latest_quotes(["IXIC", "AXP"]) == {"IXIC": {"p": 1}}


def test_mutual_fund_holdings_returns_current_allocation():
    payload = {
        "success": True,
        "data": {
            "currentAllocation": [
                {"title": "Reliance Industries Ltd", "ticker": "RELIANCE", "latest": 7.0}
            ]
        },
    }
    with respx.mock(assert_all_called=True) as rsps:
        rsps.get("https://api.tickertape.in/mutualfunds/M_MAHD/holdings").mock(
            return_value=httpx.Response(200, json=payload)
        )
        holdings = TickertapeClient().mutual_fund_holdings("M_MAHD")
        assert holdings["currentAllocation"][0]["ticker"] == "RELIANCE"


def test_screener_query_uses_post_body():
    query = {"match": {"option": ["Growth"]}, "sortBy": "aum", "sortOrder": -1}
    with respx.mock(assert_all_called=True) as rsps:
        route = rsps.post("https://api.tickertape.in/mf-screener/query").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {"results": []}})
        )
        assert TickertapeClient().mutual_fund_screener(query) == {"results": []}
        assert route.calls.last.request.content == b'{"match":{"option":["Growth"]},"sortBy":"aum","sortOrder":-1}'


def test_unsuccessful_payload_raises_api_error():
    with respx.mock(assert_all_called=True) as rsps:
        rsps.get("https://api.tickertape.in/stocks/info/BAD").mock(
            return_value=httpx.Response(200, json={"success": False, "error": "bad sid"})
        )
        with pytest.raises(TickertapeAPIError, match="bad sid"):
            TickertapeClient().stock_info("BAD")


def test_http_error_contains_status_code():
    with respx.mock(assert_all_called=True) as rsps:
        rsps.get("https://api.tickertape.in/stocks/info/BAD").mock(
            return_value=httpx.Response(404, json={"message": "not found"})
        )
        with pytest.raises(TickertapeHTTPError) as exc:
            TickertapeClient().stock_info("BAD")
        assert exc.value.status_code == 404
