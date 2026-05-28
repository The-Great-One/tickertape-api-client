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


def test_us_asset_info_supports_stocks_and_etfs():
    with respx.mock(assert_all_called=True) as rsps:
        rsps.get("https://gms-api.tickertape.in/US/securities/info?ticker=AAPL%2CMSFT").mock(
            return_value=httpx.Response(
                200,
                json={"success": True, "data": {"assets": [{"ticker": "AAPL"}]}},
            )
        )
        rsps.get("https://gms-api.tickertape.in/US/etfs/info?ticker=VOO").mock(
            return_value=httpx.Response(
                200,
                json={"success": True, "data": {"assets": [{"ticker": "VOO"}]}},
            )
        )

        client = TickertapeClient()
        assert client.us_asset_info(["AAPL", "MSFT"])["assets"][0]["ticker"] == "AAPL"
        assert client.us_asset_info("VOO", asset_type="etfs")["assets"][0]["ticker"] == "VOO"


def test_us_overview_financials_filters_and_chart_helpers():
    with respx.mock(assert_all_called=True) as rsps:
        rsps.get("https://gms-api.tickertape.in/US/securities/AAPL/overview").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {"ticker": "AAPL"}})
        )
        rsps.get("https://gms-api.tickertape.in/US/etfs/VOO/overview").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {"ticker": "VOO"}})
        )
        rsps.get(
            "https://gms-api.tickertape.in/US/securities/AAPL/financials/income?view=normal"
        ).mock(
            return_value=httpx.Response(200, json={"success": True, "data": {"financials": {}}})
        )
        rsps.get("https://gms-api.tickertape.in/US/filters").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {"filters": []}})
        )
        rsps.get("https://gms-api.tickertape.in/US/securities/AAPL/charts/intra?duration=1d").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {"points": []}})
        )
        rsps.get("https://gms-api.tickertape.in/US/securities/AAPL/charts/inter?duration=5y").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {"points": []}})
        )

        client = TickertapeClient()
        assert client.us_stock_overview("AAPL")["ticker"] == "AAPL"
        assert client.us_etf_overview("VOO")["ticker"] == "VOO"
        assert client.us_financials("AAPL", "income") == {"financials": {}}
        assert client.us_filters() == {"filters": []}
        assert client.us_chart("AAPL", "1D") == {"points": []}
        assert client.us_chart("AAPL", "5Y") == {"points": []}


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


def test_stock_screener_query_uses_post_body():
    query = {"match": {}, "sortBy": "mrktCapf", "sortOrder": -1, "offset": 0, "count": 5}
    with respx.mock(assert_all_called=True) as rsps:
        route = rsps.post("https://api.tickertape.in/screener/query").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {"results": []}})
        )
        assert TickertapeClient().screener_query(query) == {"results": []}
        assert route.calls.last.request.content == (
            b'{"match":{},"sortBy":"mrktCapf","sortOrder":-1,"offset":0,"count":5}'
        )


def test_auth_token_and_cookie_header_are_sent_to_premium_endpoints():
    with respx.mock(assert_all_called=True) as rsps:
        route = rsps.post("https://api.tickertape.in/screener/query").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {"results": []}})
        )
        TickertapeClient(auth_token="abc123", cookie_header="sessionid=s1").screener_query(
            {"project": ["premiumMetric"]}
        )
        request = route.calls.last.request
        assert request.headers["authorization"] == "Bearer abc123"
        assert request.headers["cookie"] == "sessionid=s1"


def test_from_env_reads_auth_token_and_cookie_header(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TICKERTAPE_AUTH_TOKEN", "env-token")
    monkeypatch.setenv("TICKERTAPE_COOKIE", "sessionid=env-session")
    with respx.mock(assert_all_called=True) as rsps:
        route = rsps.get("https://api.tickertape.in/screener/filters").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {}})
        )
        TickertapeClient.from_env().screener_filters()
        request = route.calls.last.request
        assert request.headers["authorization"] == "Bearer env-token"
        assert request.headers["cookie"] == "sessionid=env-session"


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
