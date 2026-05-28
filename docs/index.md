# tickertape-api-client

`tickertape-api-client` is a typed Python wrapper around useful public Tickertape web endpoints.

See the repository README for complete examples and endpoint notes.

## Install

```bash
pip install tickertape-api-client
```

## Minimal example

```python
from tickertape_api import TickertapeClient

with TickertapeClient() as tt:
    print(tt.market_status("IN"))
    print(tt.us_latest_quotes(["IXIC", "AXP"]))
    print(tt.mutual_fund_holdings("M_MAHD")["currentAllocation"][:10])
```
