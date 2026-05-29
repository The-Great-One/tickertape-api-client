# Stock screener filters

This list is generated from `GET https://api.tickertape.in/screener/filters` and documents the `label` values to use in `project`, `match`, and `sortBy` fields for `TickertapeClient.screener_query(...)`.

Notes:

- `premium: yes` means Tickertape currently marks the field as premium/locked. Querying that field without a logged-in session that has access returns a 403 such as `No access for <label>`.
- Use `TickertapeClient.from_env()` with `TICKERTAPE_AUTH_TOKEN`, `TICKERTAPE_COOKIE`, or the persistent credentials file documented in the README for premium fields.
- These are undocumented web-app fields and can change without notice.

## General

| Label | Description | Premium | Locked | Type | Unit | Short |
|-------|-------------|---------|--------|------|------|-------|
| `mrktCapf` | Market Cap | no | no | prebuilt | | |
| `sector` | Sector | no | no | prebuilt | | |
| `subindustry` | Sub-Sector | no | no | prebuilt | | |

## Profitability

| Label | Description | Premium | Locked | Type | Unit | Short |
|-------|-------------|---------|--------|------|------|-------|
| `opmg` | 5Y Avg EBITDA Margin | no | no | prebuilt | % | 5Y Avg EBITDA margin |
| `roe` | Return on Equity | no | no | prebuilt | % | |
| `aopm` | EBITDA Margin | no | no | prebuilt | % | |
| `5YpftMrg` | 5Y Avg Net Profit Margin | no | no | prebuilt | % | 5Y Avg NPM |
| `aroi` | Return on Investment | no | no | prebuilt | % | |
| `5Yroe` | 5Y Avg Return on Equity | no | no | prebuilt | % | 5Y Avg ROE |
| `rtnAsts` | Return on Assets | no | no | prebuilt | % | |
| `5YrtnAsts` | 5Y Avg Return on Assets | no | no | prebuilt | % | 5Y Avg ROA |
| `pftMrg` | Net Profit Margin | no | no | prebuilt | % | |
| `5Yaroi` | 5Y Avg Return on Investment | no | no | prebuilt | % | 5Y Avg ROI |
| `5YcafCfoaMgn` | 5Y Avg Cash Flow Margin | no | no | prebuilt | % | |
| `balCogs` | Cost of Goods Sold | no | no | prebuilt | Cr | |
| `cafCfoaMgn` | Cash Flow Margin | no | no | prebuilt | % | |
| `roce` | ROCE | no | no | prebuilt | % | |

## Growth

| Label | Description | Premium | Locked | Type | Unit | Short |
|-------|-------------|---------|--------|------|------|-------|
| `estrvng` | 1Y Forward Revenue Growth | yes | yes | prebuilt | % | 1Y Fwd Rev Growth |
| `cfog` | 1Y Hist Op. Cash Flow Growth | no | no | prebuilt | % | 1Y Hist OCF Growth |
| `estAvg` | 1Y Forward EBITDA Growth | yes | yes | prebuilt | % | 1Y Fwd EBITDA Gro |
| `epsg` | 1Y Historical EPS Growth | no | no | prebuilt | % | 1Y Hist EPS Growth |
| `rvng` | 1Y Historical Revenue Growth | no | no | prebuilt | % | 1Y Hist Rev Growth |
| `ecfog` | 1Y Fwd Op. Cash Flow Growth | yes | yes | prebuilt | % | 1Y Fwd OCF Growth |
| `earnings` | 5Y Historical EBITDA Growth | no | no | prebuilt | % | 5Y Hist EBITDA Gro |
| `cfotr` | 5Y Hist Op. Cash Flow Growth | no | no | prebuilt | % | 5Y Hist OCF Growth |
| `3YdivGwth` | 3Y Historical Dividend Growth | no | no | prebuilt | % | 3Y Hist Div Growth |
| `epsGwth` | 5Y Historical EPS Growth | no | no | prebuilt | % | 5Y Hist EPS Growth |
| `5YrevChg` | 5Y Historical Revenue Growth | no | no | prebuilt | % | 5Y Hist Rev Growth |
| `ebitg` | 1Y Historical EBITDA Growth | no | no | prebuilt | % | 1Y Hist EBITDA Gro |
| `12mEpsg` | 1Y Forward EPS Growth | yes | yes | prebuilt | % | 1Y Fwd EPS Growth |

## Valuation

| Label | Description | Premium | Locked | Type | Unit | Short |
|-------|-------------|---------|--------|------|------|-------|
| `pbd` | PB Premium vs Sector | yes | yes | prebuilt | % | |
| `divSec` | Dividend Yield vs Sector | yes | yes | prebuilt | % | Div Yield vs Sector |
| `pbr` | PB Ratio | no | no | prebuilt | | |
| `psfs` | PS Premium vs Sector | yes | yes | prebuilt | % | |
| `ps` | PS Ratio | no | no | prebuilt | | |
| `evebitd` | EV/EBITDA Ratio | no | no | prebuilt | | |
| `apef` | PE Ratio | no | no | prebuilt | | |
| `pef` | Forward PE Ratio | yes | yes | prebuilt | | Fwd PE Ratio |
| `psf` | Forward PS Ratio | yes | yes | prebuilt | | Fwd PS Ratio |
| `divDps` | Dividend Yield | no | no | prebuilt | % | Div Yield |
| `ped` | PE Premium vs Sector | yes | yes | prebuilt | % | |
| `evebit` | EV / EBIT Ratio | no | no | prebuilt | | |
| `psPremSi` | PS Premium vs Sub-sector | yes | yes | prebuilt | % | |
| `evByRev` | EV / Revenue Ratio | no | no | prebuilt | | |
| `pePremSi` | PE Premium vs Sub-sector | yes | yes | prebuilt | % | |
| `lcpCafFcf` | Price / Free Cash Flow | no | no | prebuilt | | |
| `evByIc` | EV / Invested Capital | no | no | prebuilt | | |
| `evCafFcf` | EV / Free Cash Flow | no | no | prebuilt | | |
| `ev` | Enterprise Value | no | no | prebuilt | Cr | |
| `pbPremSi` | PB Premium vs Sub-sector | yes | yes | prebuilt | % | |
| `priceCfoR` | Price / CFO | no | no | prebuilt | | |
| `priceBySales` | Price / Sales | no | no | prebuilt | | |
| `dyPremSs` | Dividend Yield vs Sub-sector | yes | yes | prebuilt | % | Div Yield vs Sub-sector |
| `inddy` | Sector Dividend Yield | no | no | prebuilt | | Sector Div Yield |
| `indpb` | Sector PB | no | no | prebuilt | | |
| `indpe` | Sector PE | no | no | prebuilt | | |
| `ttmPe` | TTM PE Ratio | no | no | prebuilt | | |

## Ownership

| Label | Description | Premium | Locked | Type | Unit | Short |
|-------|-------------|---------|--------|------|------|-------|
| `instown` | Mutual Fund Holding | no | no | prebuilt | % | MF Holding |
| `domInstHldng` | Domestic Institutional Holding | no | no | prebuilt | % | DII Holding |
| `chMutHldng6M` | MF Holding Change – 6M | no | no | prebuilt | % | MF Holding - 6M |
| `strown3` | Promoter Holding Change – 3M | no | no | prebuilt | % | Promoter Holding - 3M |
| `forInstHldng` | Foreign Institutional Holding | no | no | prebuilt | % | FII Holding |
| `domInstHldng6M` | DII Holding Change – 6M | no | no | prebuilt | % | DII Holding - 6M |
| `forInstHldng6M` | FII Holding Change – 6M | no | no | prebuilt | % | FII Holding - 6M |
| `domInstHldng3M` | DII Holding Change – 3M | no | no | prebuilt | % | DII Holding - 3M |
| `chPromHldng6M` | Promoter Holding Change – 6M | no | no | prebuilt | % | Promoter Holding - 6M |
| `instown3` | MF Holding Change – 3M | no | no | prebuilt | % | MF Holding - 3M |
| `strown` | Promoter Holding | no | no | prebuilt | % | Promoter Holding |
| `promShrPled` | Pledged Promoter Holdings | no | no | prebuilt | % | Promoter Pledges |
| `forInstHldng3M` | FII Holding Change – 3M | no | no | prebuilt | % | FII Holding - 3M |
| `insiderCml1M` | Insider Trades - 1M Cumulative | yes | yes | prebuilt | % | |
| `insiderCml3M` | Insider Trades - 3M Cumulative | yes | yes | prebuilt | % | |
| `retailHolding` | Retail Investor Holding | no | no | prebuilt | % | |
| `bulkCml1M` | Bulk Deals - 1M Cumulative | yes | yes | prebuilt | % | |
| `bulkCml6M` | Bulk Deals - 6M Cumulative | yes | yes | prebuilt | % | |
| `insHolding` | Insurance Firms Holding | no | no | prebuilt | % | |
| `bulkCml3M` | Bulk Deals - 3M Cumulative | yes | yes | prebuilt | % | |
| `insiderCml6M` | Insider Trades - 6M Cumulative | yes | yes | prebuilt | % | |
| `nShareholders` | No. of Shareholders | no | no | prebuilt | Cr | |

## Futures & Options

| Label | Description | Premium | Locked | Type | Unit | Short |
|-------|-------------|---------|--------|------|------|-------|
| `ftls` | Lot Size | no | no | prebuilt | | |
| `ftcp` | Future Close Price | no | no | prebuilt | Rs | |
| `fair` | Fair Value | yes | yes | prebuilt | Rs | |
| `1Dfoi` | 1D Change in Future OI | yes | yes | prebuilt | % | 1D Change in Fut OI |
| `rolc` | Rollover Cost | yes | yes | prebuilt | % | |
| `phstr` | Highest Put OI Strike | yes | yes | prebuilt | | High Put OI Strike |
| `1Dvol` | 1D Change in Future Volume | yes | yes | prebuilt | % | 1D Change in Fut Vol |
| `ftbas` | Basis | no | no | prebuilt | | |
| `putcall` | Put Call Ratio | yes | yes | prebuilt | | |
| `ccrp` | Cash & Carry Profit | yes | yes | prebuilt | Rs | |
| `1Wpoi` | 1W Change in Put OI | yes | yes | prebuilt | % | |
| `ftoi` | Future Open Interest | no | no | prebuilt | | |
| `1Dceoi` | Highest 1D OI Change CE Strike | yes | yes | prebuilt | | High 1D CE OI Change |
| `1Dpeoi` | Highest 1D OI Change PE Strike | yes | yes | prebuilt | | High 1D PE OI Change |
| `1Wceoi` | Highest 1W OI Change CE Strike | yes | yes | prebuilt | | High 1W CE OI Change |
| `1Wvol` | 1W Change in Future Volume | yes | yes | prebuilt | % | 1W Change in Fut Vol |
| `1Wfoi` | 1W Change in Future OI | yes | yes | prebuilt | % | 1W Change in Fut OI |
| `fairsp` | Fair Value Spread | yes | yes | prebuilt | | |
| `ftvol` | Future Volume | no | no | prebuilt | | |
| `chstr` | Highest Call OI Strike | yes | yes | prebuilt | | High Call OI Strike |
| `1Wpeoi` | Highest 1W OI Change PE Strike | yes | yes | prebuilt | | High 1W PE OI Change |
| `1Dcoi` | 1 D Change in Call OI | yes | yes | prebuilt | % | 1D Change in Call OI |
| `1DPoi` | 1D Change in Put OI | yes | yes | prebuilt | % | |
| `opcoi` | Call Open Interest | no | no | prebuilt | | |
| `1Wcoi` | 1W Change in Call OI | yes | yes | prebuilt | % | |
| `rolp` | Percentage Rollover | yes | yes | prebuilt | % | |
| `csprd` | Calendar Spread | yes | yes | prebuilt | | |
| `oppoi` | Put Open Interest | no | no | prebuilt | | |

## Price and Volume

| Label | Description | Premium | Locked | Type | Unit | Short |
|-------|-------------|---------|--------|------|------|-------|
| `vol1mAvg` | 1M Average Volume | no | no | prebuilt | | |
| `4wpct` | 1M Return | no | no | prebuilt | % | |
| `acVol` | Daily Volume | no | no | prebuilt | | |
| `12mpctN` | 1Y Return vs Nifty | no | no | prebuilt | % | |
| `lastPrice` | Close Price | no | no | prebuilt | Rs | |
| `4wpctN` | 1M Return vs Nifty | no | no | prebuilt | % | |
| `vol1wChPct` | 1W Change in Volume | no | no | prebuilt | % | |
| `vol3mAvg` | 3M Average Volume | no | no | prebuilt | | |
| `pr1w` | 1W Return | no | no | prebuilt | % | |
| `6mpctN` | 6M Return vs Nifty | no | no | prebuilt | % | |
| `52whd` | % Away From 52W High | no | no | prebuilt | | |
| `pr1d` | 1D Return | no | no | prebuilt | % | |
| `26wpct` | 6M Return | no | no | prebuilt | % | |
| `52wpct` | 1Y Return | no | no | prebuilt | % | |
| `pr1wN` | 1W Return vs Nifty | no | no | prebuilt | % | |
| `vol1dChPct` | 1D Change in Volume | no | no | prebuilt | % | |
| `52wld` | % Away From 52W Low | no | no | prebuilt | | |
| `faceValue` | Face value | no | no | prebuilt | Rs. | |
| `5yCagrPct` | 5Y CAGR | no | no | prebuilt | % | |

## Financial Ratios

| Label | Description | Premium | Locked | Type | Unit | Short |
|-------|-------------|---------|--------|------|------|-------|
| `qcur` | Current Ratio | no | no | prebuilt | | |
| `ccnc` | Cash Conversion Cycle | no | no | prebuilt | | |
| `ldbtEqt` | Long Term Debt to Equity | no | no | prebuilt | % | Lt Debt to Equity |
| `aint` | Interest Coverage Ratio | no | no | prebuilt | | Int Coverage Ratio |
| `dbtEqt` | Debt to Equity | no | no | prebuilt | % | |
| `aqui` | Quick Ratio | no | no | prebuilt | | |
| `netIncByLbl` | Net Income / Liabilities | no | no | prebuilt | % | |
| `wcTurnR` | Working Capital Turnover Ratio | no | no | prebuilt | | Working Capital Turnover |
| `invTurnR` | Inventory Turnover Ratio | no | no | prebuilt | | |
| `asstTurnR` | Asset Turnover Ratio | no | no | prebuilt | | |
| `daysOfInvOstndng` | Days of Inventory Outstanding | yes | yes | prebuilt | | |
| `daysSalesOstndng` | Days of Sales Outstanding | yes | yes | prebuilt | | Days Sales Outstanding |
| `erngPwrR` | Earning Power | no | no | prebuilt | % | |
| `daysPayOstndng` | Days Payable Outstanding | yes | yes | prebuilt | | |

## Tickertape Special

| Label | Description | Premium | Locked | Type | Unit | Short |
|-------|-------------|---------|--------|------|------|-------|
| `prmr` | Price Momentum Rank | yes | yes | prebuilt | | |
| `fundamental` | Fundamental Score | yes | yes | prebuilt | | |
| `valr` | Value Momentum Rank | yes | yes | prebuilt | | |
| `erqr` | Earnings Quality Rank | yes | yes | prebuilt | | |
| `ptir` | Price to Intrinsic Value Rank | yes | yes | prebuilt | | Price to IV Rank |

## Analyst Ratings

| Label | Description | Premium | Locked | Type | Unit | Short |
|-------|-------------|---------|--------|------|------|-------|
| `upside` | Percentage Upside | yes | yes | prebuilt | % | |
| `breco` | Percentage Buy Reco's | yes | yes | prebuilt | % | Percentage Buy Reco |
| `nBreco` | No. of analysts with buy reco | yes | yes | prebuilt | | |
| `pctSelReco` | Percentage Sell Reco's | yes | yes | prebuilt | % | Percentage Sell Reco |
| `pctHldReco` | Percentage Hold Reco's | yes | yes | prebuilt | % | Percentage Hold Reco |
| `totalAnalysts` | Total no. of analysts | yes | yes | prebuilt | | |

## Technical Indicators

| Label | Description | Premium | Locked | Type | Unit | Short |
|-------|-------------|---------|--------|------|------|-------|
| `percentChangeObv` | 1W Change in On Balance Volume | yes | yes | prebuilt | % | 1W Change in OBV |
| `14dRsi` | RSI – 14D | yes | yes | prebuilt | | RSI - 14D |
| `prAvMonthEVA` | % Price above 1M EMA | no | no | prebuilt | | |
| `beta` | Beta | no | no | prebuilt | | |
| `relVol` | Relative Volume | no | no | prebuilt | | |
| `12mVol` | Volatility | no | no | prebuilt | % | |
| `priceUBB` | % From Upper Bollinger Band | yes | yes | prebuilt | | % From Up Bollinger Band |
| `stochasticK` | Stochastic %K | yes | yes | prebuilt | | |
| `14adx` | ADX Rating – Trend Strength | yes | yes | prebuilt | | ADX Rating - Trend |
| `percentChangeADL` | 1W Change in AD Line | yes | yes | prebuilt | % | |
| `williamR` | William %R | yes | yes | prebuilt | | Willian %R |
| `vWAP` | VWAP | no | no | prebuilt | | |
| `pab12Mma` | % Price above 1Y SMA | no | no | prebuilt | | % Price Above 1Y SMA |
| `3Ywal` | Alpha | no | no | prebuilt | | |
| `1mac` | MACD Line 1 – Trend Indicator | yes | yes | prebuilt | | MACD Line 1 |
| `2mac` | MACD Line 2 – Signal Line Comp | yes | yes | prebuilt | | MACD Line 2 |
| `parabolSAR` | % From Parabolic SAR | yes | yes | prebuilt | | |
| `priceLBB` | % From Lower Bollinger Band | yes | yes | prebuilt | | % From Lw Bollinger Band |
| `12mVolN` | Volatility vs Nifty | no | no | prebuilt | % | |
| `superTrend` | Super Trend | yes | yes | prebuilt | | |
| `pab1Mma` | % Price above 1M SMA | no | no | prebuilt | | % Price Above 1M SMA |
| `3Ywsh` | Sharpe Ratio | no | no | prebuilt | | |
| `14ersi` | RSI Exponential – 14D | yes | yes | prebuilt | | RSI Exponential - 14D |
| `stochasticD` | Stochastic %D | yes | yes | prebuilt | | |
| `sma200d` | 200D SMA | no | no | prebuilt | | |
| `ema50d` | 50D EMA | no | no | prebuilt | | |
| `ema100d` | 100D EMA | no | no | prebuilt | | |
| `sma100d` | 100D SMA | no | no | prebuilt | | |
| `ema10d` | 10D EMA | no | no | prebuilt | | |
| `ema200d` | 200D EMA | no | no | prebuilt | | |
| `sma10d` | 10D SMA | no | no | prebuilt | | |
| `sma50d` | 50D SMA | no | no | prebuilt | | |
| `maxDrawdown` | 1Y Max Loss | no | no | prebuilt | % | |

## Balance Sheet & Cash Flow

| Label | Description | Premium | Locked | Type | Unit | Short |
|-------|-------------|---------|--------|------|------|-------|
| `balApic` | Additional Paid–in Capital | no | no | prebuilt | Cr | Add. Paid-in Capital |
| `cafNcic` | Net Change in Cash | no | no | prebuilt | Cr | |
| `balTotl` | Total Liabilities | no | no | prebuilt | Cr | |
| `cafCfia` | Investing Cash Flow | no | no | prebuilt | Cr | |
| `balNetl` | Loans & Advances | no | no | prebuilt | Cr | |
| `cafCffa` | Financing Cash Flow | no | no | prebuilt | Cr | |
| `balLti` | Long Term Investments | no | no | prebuilt | Cr | |
| `cafTcdp` | Total Cash Dividend Paid | no | no | prebuilt | Cr | Cash Dividend Paid |
| `balRtne` | Reserves & Surplus | no | no | prebuilt | Cr | |
| `cafCexp` | Capital Expenditure | no | no | prebuilt | Cr | |
| `balNppe` | Net Property,Plant & Equipment | no | no | prebuilt | Cr | Net PP & E |
| `cafCfoa` | Operating Cash Flow | no | no | prebuilt | Cr | |
| `balGint` | Goodwill & Intangibles | no | no | prebuilt | Cr | |
| `balTca` | Total Current Assets | no | no | prebuilt | Cr | Current Assets |
| `cafCiwc` | Change in Working Capital | no | no | prebuilt | Cr | Working Capital Change |
| `balTdeb` | Total Debt | no | no | prebuilt | Cr | |
| `balAccp` | Accounts Payable | no | no | prebuilt | Cr | |
| `balTltd` | Long Term Debt | no | no | prebuilt | Cr | |
| `balTcso` | Common Shares Outstanding | no | no | prebuilt | Cr | Shares Outstanding |
| `balDit` | Deferred Tax Liabilities (Net) | no | no | prebuilt | Cr | |
| `balTeq` | Total Equity | no | no | prebuilt | Cr | |
| `balTrec` | Total Receivables | no | no | prebuilt | Cr | |
| `balTota` | Total Assets | no | no | prebuilt | Cr | |
| `balTcl` | Total Current Liabilities | no | no | prebuilt | Cr | Current Liabilities |
| `balMint` | Minority Interest | no | no | prebuilt | Cr | |
| `balComs` | Share Capital | no | no | prebuilt | Cr | |
| `balCsti` | Cash and Equivalent | no | no | prebuilt | Cr | |
| `balTinv` | Total Inventory | no | no | prebuilt | Cr | |
| `balTdep` | Total Deposits – Banks | no | no | prebuilt | Cr | Total Deposits |
| `balDta` | Deferred Tax Assets (Net) | no | no | prebuilt | Cr | |
| `balNca` | Non Current Assets | no | no | prebuilt | Cr | |
| `cafFcf` | Free Cash Flow | no | no | prebuilt | Cr | |
| `balNcl` | Non Current Liabilities | no | no | prebuilt | Cr | |
| `bookValue` | Book Value | no | no | prebuilt | Cr | |
| `balOcl` | Other Current Liabilities | no | no | prebuilt | Cr | |
| `balOca` | Other Current Assets | no | no | prebuilt | Cr | |
| `balOthl` | Other Liabilities | no | no | prebuilt | Cr | |
| `balOtha` | Other Assets | no | no | prebuilt | Cr | |

## ETFs

| Label | Description | Premium | Locked | Type | Unit | Short |
|-------|-------------|---------|--------|------|------|-------|
| `expenseRatio` | Expense Ratio | no | no | prebuilt | % | |
| `trackErr` | Tracking Error | no | no | prebuilt | % | |

## Income Statement

| Label | Description | Premium | Locked | Type | Unit | Short |
|-------|-------------|---------|--------|------|------|-------|
| `incEbi` | EBITDA | no | no | prebuilt | Cr | |
| `incNinc` | Net Income | no | no | prebuilt | Cr | |
| `incPyr` | Payout Ratio | no | no | prebuilt | | |
| `incEps` | Earnings Per Share | no | no | prebuilt | Rs | EPS |
| `incToi` | Taxes & Other Items | no | no | prebuilt | Cr | Taxes |
| `incDps` | Dividend Per Share | no | no | prebuilt | Rs | DPS |
| `incPbi` | PBIT | no | no | prebuilt | Cr | |
| `incIoi` | Interest & Other Items | no | no | prebuilt | Cr | Interest |
| `incTrev` | Total Revenue | no | no | prebuilt | Cr | |
| `incDep` | Depreciation & Amortization | no | no | prebuilt | Cr | Depr. & Amortization |
| `incPbt` | PBT | no | no | prebuilt | Cr | |
| `incPfc` | Power & Fuel Cost | no | no | prebuilt | Cr | |
| `incRaw` | Raw Materials | no | no | prebuilt | Cr | |
| `incOpe` | Operating & Other expenses | no | no | prebuilt | Cr | |
| `incEpc` | Employee Cost | no | no | prebuilt | Cr | |
| `incSga` | Selling & Administrative Expenses | no | no | prebuilt | Cr | |
| `qIncNincK` | Net Income (Q) | no | no | prebuilt | Cr | |
| `qIncTrevK` | Total revenue (Q) | no | no | prebuilt | Cr | |
| `qIncEpsK` | EPS (Q) | no | no | prebuilt | Rs | |
| `qIncEbiK` | EBITDA (Q) | no | no | prebuilt | Cr | |
| `qIncOpeK` | Operating and Other Expenses (Q) | no | no | prebuilt | Cr | Op and Other Expenses (Q) |
| `qIncPbiK` | PBIT (Q) | no | no | prebuilt | Cr | |
| `qIncPbtK` | PBT (Q) | no | no | prebuilt | Cr | |
