# Stock screener filters

This list is generated from `GET https://api.tickertape.in/screener/filters` and documents the `label` values to use in `project`, `match`, and `sortBy` fields for `TickertapeClient.screener_query(...)`.

Notes:

- `premium: yes` means Tickertape currently marks the field as premium/locked. Querying that field without a logged-in session that has access returns a 403 such as `No access for <label>`.
- Use `TickertapeClient.from_env()` with `TICKERTAPE_AUTH_TOKEN`, `TICKERTAPE_COOKIE`, or the persistent credentials file documented in the README for premium fields.
- These are undocumented web-app fields and can change without notice.

## General

- `mrktCapf` — Market Cap; premium: no; locked: no; type: prebuilt
- `sector` — Sector; premium: no; locked: no; type: prebuilt
- `subindustry` — Sub-Sector; premium: no; locked: no; type: prebuilt

## Profitability

- `opmg` — 5Y Avg EBITDA Margin; premium: no; locked: no; type: prebuilt; unit: %; short: 5Y Avg EBITDA margin
- `roe` — Return on Equity; premium: no; locked: no; type: prebuilt; unit: %
- `aopm` — EBITDA Margin; premium: no; locked: no; type: prebuilt; unit: %
- `5YpftMrg` — 5Y Avg Net Profit Margin; premium: no; locked: no; type: prebuilt; unit: %; short: 5Y Avg NPM
- `aroi` — Return on Investment; premium: no; locked: no; type: prebuilt; unit: %
- `5Yroe` — 5Y Avg Return on Equity; premium: no; locked: no; type: prebuilt; unit: %; short: 5Y Avg ROE
- `rtnAsts` — Return on Assets; premium: no; locked: no; type: prebuilt; unit: %
- `5YrtnAsts` — 5Y Avg Return on Assets; premium: no; locked: no; type: prebuilt; unit: %; short: 5Y Avg ROA
- `pftMrg` — Net Profit Margin; premium: no; locked: no; type: prebuilt; unit: %
- `5Yaroi` — 5Y Avg Return on Investment; premium: no; locked: no; type: prebuilt; unit: %; short: 5Y Avg ROI
- `5YcafCfoaMgn` — 5Y Avg Cash Flow Margin; premium: no; locked: no; type: prebuilt; unit: %
- `balCogs` — Cost of Goods Sold; premium: no; locked: no; type: prebuilt; unit: Cr
- `cafCfoaMgn` — Cash Flow Margin; premium: no; locked: no; type: prebuilt; unit: %
- `roce` — ROCE; premium: no; locked: no; type: prebuilt; unit: %

## Growth

- `estrvng` — 1Y Forward Revenue Growth; premium: yes; locked: yes; type: prebuilt; unit: %; short: 1Y Fwd Rev Growth
- `cfog` — 1Y Hist Op. Cash Flow Growth; premium: no; locked: no; type: prebuilt; unit: %; short: 1Y Hist OCF Growth
- `estAvg` — 1Y Forward EBITDA Growth; premium: yes; locked: yes; type: prebuilt; unit: %; short: 1Y Fwd EBITDA Gro
- `epsg` — 1Y Historical EPS Growth; premium: no; locked: no; type: prebuilt; unit: %; short: 1Y Hist EPS Growth
- `rvng` — 1Y Historical Revenue Growth; premium: no; locked: no; type: prebuilt; unit: %; short: 1Y Hist Rev Growth
- `ecfog` — 1Y Fwd Op. Cash Flow Growth; premium: yes; locked: yes; type: prebuilt; unit: %; short: 1Y Fwd OCF Growth
- `earnings` — 5Y Historical EBITDA Growth; premium: no; locked: no; type: prebuilt; unit: %; short: 5Y Hist EBITDA Gro
- `cfotr` — 5Y Hist Op. Cash Flow Growth; premium: no; locked: no; type: prebuilt; unit: %; short: 5Y Hist OCF Growth
- `3YdivGwth` — 3Y Historical Dividend Growth; premium: no; locked: no; type: prebuilt; unit: %; short: 3Y Hist Div Growth
- `epsGwth` — 5Y Historical EPS Growth; premium: no; locked: no; type: prebuilt; unit: %; short: 5Y Hist EPS Growth
- `5YrevChg` — 5Y Historical Revenue Growth; premium: no; locked: no; type: prebuilt; unit: %; short: 5Y Hist Rev Growth
- `ebitg` — 1Y Historical EBITDA Growth; premium: no; locked: no; type: prebuilt; unit: %; short: 1Y Hist EBITDA Gro
- `12mEpsg` — 1Y Forward EPS Growth; premium: yes; locked: yes; type: prebuilt; unit: %; short: 1Y Fwd EPS Growth

## Valuation

- `pbd` — PB Premium vs Sector; premium: yes; locked: yes; type: prebuilt; unit: %
- `divSec` — Dividend Yield vs Sector; premium: yes; locked: yes; type: prebuilt; unit: %; short: Div Yield vs Sector
- `pbr` — PB Ratio; premium: no; locked: no; type: prebuilt
- `psfs` — PS Premium vs Sector; premium: yes; locked: yes; type: prebuilt; unit: %
- `ps` — PS Ratio; premium: no; locked: no; type: prebuilt
- `evebitd` — EV/EBITDA Ratio; premium: no; locked: no; type: prebuilt
- `apef` — PE Ratio; premium: no; locked: no; type: prebuilt
- `pef` — Forward PE Ratio; premium: yes; locked: yes; type: prebuilt; short: Fwd PE Ratio
- `psf` — Forward PS Ratio; premium: yes; locked: yes; type: prebuilt; short: Fwd PS Ratio
- `divDps` — Dividend Yield; premium: no; locked: no; type: prebuilt; unit: %; short: Div Yield
- `ped` — PE Premium vs Sector; premium: yes; locked: yes; type: prebuilt; unit: %
- `evebit` — EV / EBIT Ratio; premium: no; locked: no; type: prebuilt
- `psPremSi` — PS Premium vs Sub-sector; premium: yes; locked: yes; type: prebuilt; unit: %
- `evByRev` — EV / Revenue Ratio; premium: no; locked: no; type: prebuilt
- `pePremSi` — PE Premium vs Sub-sector; premium: yes; locked: yes; type: prebuilt; unit: %
- `lcpCafFcf` — Price / Free Cash Flow; premium: no; locked: no; type: prebuilt
- `evByIc` — EV / Invested Capital; premium: no; locked: no; type: prebuilt
- `evCafFcf` — EV / Free Cash Flow; premium: no; locked: no; type: prebuilt
- `ev` — Enterprise Value; premium: no; locked: no; type: prebuilt; unit: Cr
- `pbPremSi` — PB Premium vs Sub-sector; premium: yes; locked: yes; type: prebuilt; unit: %
- `priceCfoR` — Price / CFO; premium: no; locked: no; type: prebuilt
- `priceBySales` — Price / Sales; premium: no; locked: no; type: prebuilt
- `dyPremSs` — Dividend Yield vs Sub-sector; premium: yes; locked: yes; type: prebuilt; unit: %; short: Div Yield vs Sub-sector
- `inddy` — Sector Dividend Yield; premium: no; locked: no; type: prebuilt; short: Sector Div Yield
- `indpb` — Sector PB; premium: no; locked: no; type: prebuilt
- `indpe` — Sector PE; premium: no; locked: no; type: prebuilt
- `ttmPe` — TTM PE Ratio; premium: no; locked: no; type: prebuilt

## Ownership

- `instown` — Mutual Fund Holding; premium: no; locked: no; type: prebuilt; unit: %; short: MF Holding
- `domInstHldng` — Domestic Institutional Holding; premium: no; locked: no; type: prebuilt; unit: %; short: DII Holding
- `chMutHldng6M` —  MF Holding Change – 6M; premium: no; locked: no; type: prebuilt; unit: %; short: MF Holding - 6M 
- `strown3` — Promoter Holding Change – 3M; premium: no; locked: no; type: prebuilt; unit: %; short: Promoter Holding - 3M
- `forInstHldng` — Foreign Institutional Holding; premium: no; locked: no; type: prebuilt; unit: %; short: FII Holding
- `domInstHldng6M` — DII Holding Change – 6M; premium: no; locked: no; type: prebuilt; unit: %; short: DII Holding - 6M 
- `forInstHldng6M` — FII Holding Change – 6M; premium: no; locked: no; type: prebuilt; unit: %; short: FII Holding - 6M
- `domInstHldng3M` — DII Holding Change – 3M; premium: no; locked: no; type: prebuilt; unit: %; short: DII Holding - 3M 
- `chPromHldng6M` — Promoter Holding Change – 6M ; premium: no; locked: no; type: prebuilt; unit: %; short: Promoter Holding - 6M
- `instown3` — MF Holding Change – 3M; premium: no; locked: no; type: prebuilt; unit: %; short: MF Holding - 3M 
- `strown` — Promoter Holding; premium: no; locked: no; type: prebuilt; unit: %; short: Promoter Holding 
- `promShrPled` — Pledged Promoter Holdings; premium: no; locked: no; type: prebuilt; unit: %; short: Promoter Pledges
- `forInstHldng3M` — FII Holding Change – 3M; premium: no; locked: no; type: prebuilt; unit: %; short: FII Holding - 3M
- `insiderCml1M` — Insider Trades - 1M Cumulative; premium: yes; locked: yes; type: prebuilt; unit: %
- `insiderCml3M` — Insider Trades - 3M Cumulative; premium: yes; locked: yes; type: prebuilt; unit: %
- `retailHolding` — Retail Investor Holding; premium: no; locked: no; type: prebuilt; unit: %
- `bulkCml1M` — Bulk Deals - 1M Cumulative; premium: yes; locked: yes; type: prebuilt; unit: %
- `bulkCml6M` — Bulk Deals - 6M Cumulative; premium: yes; locked: yes; type: prebuilt; unit: %
- `insHolding` — Insurance Firms Holding; premium: no; locked: no; type: prebuilt; unit: %
- `bulkCml3M` — Bulk Deals - 3M Cumulative; premium: yes; locked: yes; type: prebuilt; unit: %
- `insiderCml6M` — Insider Trades - 6M Cumulative; premium: yes; locked: yes; type: prebuilt; unit: %
- `nShareholders` — No. of Shareholders; premium: no; locked: no; type: prebuilt; unit: Cr

## Futures & Options

- `ftls` — Lot Size; premium: no; locked: no; type: prebuilt
- `ftcp` — Future Close Price; premium: no; locked: no; type: prebuilt; unit: Rs
- `fair` — Fair Value; premium: yes; locked: yes; type: prebuilt; unit: Rs
- `1Dfoi` — 1D Change in Future OI; premium: yes; locked: yes; type: prebuilt; unit: %; short: 1D Change in Fut OI
- `rolc` — Rollover Cost; premium: yes; locked: yes; type: prebuilt; unit: %
- `phstr` — Highest Put OI Strike; premium: yes; locked: yes; type: prebuilt; short: High Put OI Strike
- `1Dvol` — 1D Change in Future Volume; premium: yes; locked: yes; type: prebuilt; unit: %; short: 1D Change in Fut Vol
- `ftbas` — Basis; premium: no; locked: no; type: prebuilt
- `putcall` — Put Call Ratio; premium: yes; locked: yes; type: prebuilt
- `ccrp` — Cash & Carry Profit; premium: yes; locked: yes; type: prebuilt; unit: Rs
- `1Wpoi` — 1W Change in Put OI; premium: yes; locked: yes; type: prebuilt; unit: %
- `ftoi` — Future Open Interest; premium: no; locked: no; type: prebuilt
- `1Dceoi` — Highest 1D OI Change CE Strike; premium: yes; locked: yes; type: prebuilt; short: High 1D CE OI Change
- `1Dpeoi` — Highest 1D OI Change PE Strike; premium: yes; locked: yes; type: prebuilt; short: High 1D PE OI Change
- `1Wceoi` — Highest 1W OI Change CE Strike; premium: yes; locked: yes; type: prebuilt; short: High 1W CE OI Change
- `1Wvol` — 1W Change in Future Volume; premium: yes; locked: yes; type: prebuilt; unit: %; short: 1W Change in Fut Vol
- `1Wfoi` — 1W Change in Future OI; premium: yes; locked: yes; type: prebuilt; unit: %; short: 1W Change in Fut OI
- `fairsp` — Fair Value Spread; premium: yes; locked: yes; type: prebuilt
- `ftvol` — Future Volume; premium: no; locked: no; type: prebuilt
- `chstr` — Highest Call OI Strike; premium: yes; locked: yes; type: prebuilt; short: High Call OI Strike
- `1Wpeoi` — Highest 1W OI Change PE Strike; premium: yes; locked: yes; type: prebuilt; short: High 1W PE OI Change
- `1Dcoi` — 1 D Change in Call OI; premium: yes; locked: yes; type: prebuilt; unit: %; short: 1D Change in Call OI
- `1DPoi` — 1D Change in Put OI; premium: yes; locked: yes; type: prebuilt; unit: %
- `opcoi` — Call Open Interest; premium: no; locked: no; type: prebuilt
- `1Wcoi` — 1W Change in Call OI; premium: yes; locked: yes; type: prebuilt; unit: %
- `rolp` — Percentage Rollover; premium: yes; locked: yes; type: prebuilt; unit: %
- `csprd` — Calendar Spread; premium: yes; locked: yes; type: prebuilt
- `oppoi` — Put Open Interest; premium: no; locked: no; type: prebuilt

## Price and Volume

- `vol1mAvg` — 1M Average Volume; premium: no; locked: no; type: prebuilt
- `4wpct` — 1M Return; premium: no; locked: no; type: prebuilt; unit: %
- `acVol` — Daily Volume; premium: no; locked: no; type: prebuilt
- `12mpctN` — 1Y Return vs Nifty; premium: no; locked: no; type: prebuilt; unit: %
- `lastPrice` — Close Price; premium: no; locked: no; type: prebuilt; unit: Rs
- `4wpctN` — 1M Return vs Nifty; premium: no; locked: no; type: prebuilt; unit: %
- `vol1wChPct` — 1W Change in Volume; premium: no; locked: no; type: prebuilt; unit: %
- `vol3mAvg` — 3M Average Volume; premium: no; locked: no; type: prebuilt
- `pr1w` — 1W Return; premium: no; locked: no; type: prebuilt; unit: %
- `6mpctN` — 6M Return vs Nifty; premium: no; locked: no; type: prebuilt; unit: %
- `52whd` — % Away From 52W High; premium: no; locked: no; type: prebuilt
- `pr1d` — 1D Return; premium: no; locked: no; type: prebuilt; unit: %
- `26wpct` — 6M Return; premium: no; locked: no; type: prebuilt; unit: %
- `52wpct` — 1Y Return; premium: no; locked: no; type: prebuilt; unit: %
- `pr1wN` — 1W Return vs Nifty; premium: no; locked: no; type: prebuilt; unit: %
- `vol1dChPct` — 1D Change in Volume; premium: no; locked: no; type: prebuilt; unit: %
- `52wld` — % Away From 52W Low; premium: no; locked: no; type: prebuilt
- `faceValue` — Face value; premium: no; locked: no; type: prebuilt; unit: Rs.
- `5yCagrPct` — 5Y CAGR; premium: no; locked: no; type: prebuilt; unit: %

## Financial Ratios

- `qcur` — Current Ratio; premium: no; locked: no; type: prebuilt
- `ccnc` — Cash Conversion Cycle; premium: no; locked: no; type: prebuilt
- `ldbtEqt` — Long Term Debt to Equity; premium: no; locked: no; type: prebuilt; unit: %; short: Lt Debt to Equity
- `aint` — Interest Coverage Ratio; premium: no; locked: no; type: prebuilt; short: Int Coverage Ratio
- `dbtEqt` — Debt to Equity; premium: no; locked: no; type: prebuilt; unit: %
- `aqui` — Quick Ratio; premium: no; locked: no; type: prebuilt
- `netIncByLbl` — Net Income / Liabilities; premium: no; locked: no; type: prebuilt; unit: %
- `wcTurnR` — Working Capital Turnover Ratio; premium: no; locked: no; type: prebuilt; short: Working Capital Turnover
- `invTurnR` — Inventory Turnover Ratio; premium: no; locked: no; type: prebuilt
- `asstTurnR` — Asset Turnover Ratio; premium: no; locked: no; type: prebuilt
- `daysOfInvOstndng` — Days of Inventory Outstanding; premium: yes; locked: yes; type: prebuilt
- `daysSalesOstndng` — Days of Sales Outstanding; premium: yes; locked: yes; type: prebuilt; short: Days Sales Outstanding
- `erngPwrR` — Earning Power; premium: no; locked: no; type: prebuilt; unit: %
- `daysPayOstndng` — Days Payable Outstanding; premium: yes; locked: yes; type: prebuilt

## Tickertape Special

- `prmr` — Price Momentum Rank; premium: yes; locked: yes; type: prebuilt
- `fundamental` — Fundamental Score; premium: yes; locked: yes; type: prebuilt
- `valr` — Value Momentum Rank; premium: yes; locked: yes; type: prebuilt
- `erqr` — Earnings Quality Rank; premium: yes; locked: yes; type: prebuilt
- `ptir` — Price to Intrinsic Value Rank; premium: yes; locked: yes; type: prebuilt; short: Price to IV Rank

## Analyst Ratings

- `upside` — Percentage Upside; premium: yes; locked: yes; type: prebuilt; unit: %
- `breco` — Percentage Buy Reco’s; premium: yes; locked: yes; type: prebuilt; unit: %; short: Percentage Buy Reco
- `nBreco` — No. of analysts with buy reco; premium: yes; locked: yes; type: prebuilt
- `pctSelReco` — Percentage Sell Reco's; premium: yes; locked: yes; type: prebuilt; unit: %; short: Percentage Sell Reco
- `pctHldReco` — Percentage Hold Reco's; premium: yes; locked: yes; type: prebuilt; unit: %; short: Percentage Hold Reco
- `totalAnalysts` — Total no. of analysts; premium: yes; locked: yes; type: prebuilt

## Technical Indicators

- `percentChangeObv` — 1W Change in On Balance Volume; premium: yes; locked: yes; type: prebuilt; unit: %; short: 1W Change in OBV
- `14dRsi` — RSI – 14D; premium: yes; locked: yes; type: prebuilt; short: RSI - 14D
- `prAvMonthEVA` — % Price above 1M EMA; premium: no; locked: no; type: prebuilt
- `beta` — Beta; premium: no; locked: no; type: prebuilt
- `relVol` — Relative Volume; premium: no; locked: no; type: prebuilt
- `12mVol` — Volatility; premium: no; locked: no; type: prebuilt; unit: %
- `priceUBB` — % From Upper Bollinger Band; premium: yes; locked: yes; type: prebuilt; short: % From Up Bollinger Band
- `stochasticK` — Stochastic %K; premium: yes; locked: yes; type: prebuilt
- `14adx` — ADX Rating – Trend Strength; premium: yes; locked: yes; type: prebuilt; short: ADX Rating - Trend
- `percentChangeADL` — 1W Change in AD Line; premium: yes; locked: yes; type: prebuilt; unit: %
- `williamR` — William %R; premium: yes; locked: yes; type: prebuilt; short: Willian %R
- `vWAP` — VWAP; premium: no; locked: no; type: prebuilt
- `pab12Mma` — % Price above 1Y SMA; premium: no; locked: no; type: prebuilt; short: % Price Above 1Y SMA
- `3Ywal` — Alpha; premium: no; locked: no; type: prebuilt
- `1mac` — MACD Line 1 – Trend Indicator; premium: yes; locked: yes; type: prebuilt; short: MACD Line 1
- `2mac` — MACD Line 2 – Signal Line Comp; premium: yes; locked: yes; type: prebuilt; short: MACD Line 2
- `parabolSAR` — % From Parabolic SAR; premium: yes; locked: yes; type: prebuilt
- `priceLBB` — % From Lower Bollinger Band; premium: yes; locked: yes; type: prebuilt; short: % From Lw Bollinger Band
- `12mVolN` — Volatility vs Nifty; premium: no; locked: no; type: prebuilt; unit: %
- `superTrend` — Super Trend; premium: yes; locked: yes; type: prebuilt
- `pab1Mma` — % Price above 1M SMA; premium: no; locked: no; type: prebuilt; short: % Price Above 1M SMA
- `3Ywsh` — Sharpe Ratio; premium: no; locked: no; type: prebuilt
- `14ersi` — RSI Exponential – 14D; premium: yes; locked: yes; type: prebuilt; short: RSI Exponential - 14D
- `stochasticD` — Stochastic %D; premium: yes; locked: yes; type: prebuilt
- `sma200d` — 200D SMA; premium: no; locked: no; type: prebuilt
- `ema50d` — 50D EMA; premium: no; locked: no; type: prebuilt
- `ema100d` — 100D EMA; premium: no; locked: no; type: prebuilt
- `sma100d` — 100D SMA; premium: no; locked: no; type: prebuilt
- `ema10d` — 10D EMA; premium: no; locked: no; type: prebuilt
- `ema200d` — 200D EMA; premium: no; locked: no; type: prebuilt
- `sma10d` — 10D SMA; premium: no; locked: no; type: prebuilt
- `sma50d` — 50D SMA; premium: no; locked: no; type: prebuilt
- `maxDrawdown` — 1Y Max Loss; premium: no; locked: no; type: prebuilt; unit: %

## Balance Sheet & Cash Flow

- `balApic` — Additional Paid–in Capital; premium: no; locked: no; type: prebuilt; unit: Cr; short: Add. Paid-in Capital
- `cafNcic` — Net Change in Cash; premium: no; locked: no; type: prebuilt; unit: Cr
- `balTotl` — Total Liabilities; premium: no; locked: no; type: prebuilt; unit: Cr
- `cafCfia` — Investing Cash Flow; premium: no; locked: no; type: prebuilt; unit: Cr
- `balNetl` — Loans & Advances; premium: no; locked: no; type: prebuilt; unit: Cr
- `cafCffa` — Financing Cash Flow; premium: no; locked: no; type: prebuilt; unit: Cr
- `balLti` — Long Term Investments; premium: no; locked: no; type: prebuilt; unit: Cr
- `cafTcdp` — Total Cash Dividend Paid; premium: no; locked: no; type: prebuilt; unit: Cr; short: Cash Dividend Paid
- `balRtne` — Reserves & Surplus; premium: no; locked: no; type: prebuilt; unit: Cr
- `cafCexp` — Capital Expenditure; premium: no; locked: no; type: prebuilt; unit: Cr
- `balNppe` — Net Property,Plant & Equipment; premium: no; locked: no; type: prebuilt; unit: Cr; short: Net PP & E
- `cafCfoa` — Operating Cash Flow; premium: no; locked: no; type: prebuilt; unit: Cr
- `balGint` — Goodwill & Intangibles; premium: no; locked: no; type: prebuilt; unit: Cr
- `balTca` — Total Current Assets; premium: no; locked: no; type: prebuilt; unit: Cr; short: Current Assets
- `cafCiwc` — Change in Working Capital; premium: no; locked: no; type: prebuilt; unit: Cr; short: Working Capital Change
- `balTdeb` — Total Debt; premium: no; locked: no; type: prebuilt; unit: Cr
- `balAccp` — Accounts Payable; premium: no; locked: no; type: prebuilt; unit: Cr
- `balTltd` — Long Term Debt; premium: no; locked: no; type: prebuilt; unit: Cr
- `balTcso` — Common Shares Outstanding; premium: no; locked: no; type: prebuilt; unit: Cr; short: Shares Outstanding
- `balDit` — Deferred Tax Liabilities (Net); premium: no; locked: no; type: prebuilt; unit: Cr
- `balTeq` — Total Equity; premium: no; locked: no; type: prebuilt; unit: Cr
- `balTrec` — Total Receivables; premium: no; locked: no; type: prebuilt; unit: Cr
- `balTota` — Total Assets; premium: no; locked: no; type: prebuilt; unit: Cr
- `balTcl` — Total Current Liabilities; premium: no; locked: no; type: prebuilt; unit: Cr; short: Current Liabilities
- `balMint` — Minority Interest; premium: no; locked: no; type: prebuilt; unit: Cr
- `balComs` — Share Capital; premium: no; locked: no; type: prebuilt; unit: Cr
- `balCsti` — Cash and Equivalent; premium: no; locked: no; type: prebuilt; unit: Cr
- `balTinv` — Total Inventory; premium: no; locked: no; type: prebuilt; unit: Cr
- `balTdep` — Total Deposits – Banks; premium: no; locked: no; type: prebuilt; unit: Cr; short: Total Deposits
- `balDta` — Deferred Tax Assets (Net); premium: no; locked: no; type: prebuilt; unit: Cr
- `balNca` — Non Current Assets; premium: no; locked: no; type: prebuilt; unit: Cr
- `cafFcf` — Free Cash Flow; premium: no; locked: no; type: prebuilt; unit: Cr
- `balNcl` — Non Current Liabilties; premium: no; locked: no; type: prebuilt; unit: Cr
- `bookValue` — Book Value; premium: no; locked: no; type: prebuilt; unit: Cr
- `balOcl` — Other Current Liabilities; premium: no; locked: no; type: prebuilt; unit: Cr
- `balOca` — Other Current Assets; premium: no; locked: no; type: prebuilt; unit: Cr
- `balOthl` — Other Liabilities; premium: no; locked: no; type: prebuilt; unit: Cr
- `balOtha` — Other Assets; premium: no; locked: no; type: prebuilt; unit: Cr

## ETFs

- `expenseRatio` — Expense Ratio; premium: no; locked: no; type: prebuilt; unit: %
- `trackErr` — Tracking Error; premium: no; locked: no; type: prebuilt; unit: %

## Income Statement

- `incEbi` — EBITDA; premium: no; locked: no; type: prebuilt; unit: Cr
- `incNinc` — Net Income; premium: no; locked: no; type: prebuilt; unit: Cr
- `incPyr` — Payout Ratio; premium: no; locked: no; type: prebuilt
- `incEps` — Earnings Per Share; premium: no; locked: no; type: prebuilt; unit: Rs; short: EPS
- `incToi` — Taxes & Other Items; premium: no; locked: no; type: prebuilt; unit: Cr; short: Taxes
- `incDps` — Dividend Per Share; premium: no; locked: no; type: prebuilt; unit: Rs; short: DPS
- `incPbi` — PBIT; premium: no; locked: no; type: prebuilt; unit: Cr
- `incIoi` — Interest & Other Items; premium: no; locked: no; type: prebuilt; unit: Cr; short: Interest
- `incTrev` — Total Revenue; premium: no; locked: no; type: prebuilt; unit: Cr
- `incDep` — Depreciation & Amortization; premium: no; locked: no; type: prebuilt; unit: Cr; short: Depr. & Amortization
- `incPbt` — PBT; premium: no; locked: no; type: prebuilt; unit: Cr
- `incPfc` — Power & Fuel Cost; premium: no; locked: no; type: prebuilt; unit: Cr
- `incRaw` — Raw Materials; premium: no; locked: no; type: prebuilt; unit: Cr
- `incOpe` — Operating & Other expenses; premium: no; locked: no; type: prebuilt; unit: Cr
- `incEpc` — Employee Cost; premium: no; locked: no; type: prebuilt; unit: Cr
- `incSga` — Selling & Administrative Expenses; premium: no; locked: no; type: prebuilt; unit: Cr
- `qIncNincK` — Net Income (Q); premium: no; locked: no; type: prebuilt; unit: Cr
- `qIncTrevK` — Total revenue (Q); premium: no; locked: no; type: prebuilt; unit: Cr
- `qIncEpsK` — EPS (Q); premium: no; locked: no; type: prebuilt; unit: Rs
- `qIncEbiK` — EBITDA (Q); premium: no; locked: no; type: prebuilt; unit: Cr
- `qIncOpeK` — Operating and Other Expenses (Q); premium: no; locked: no; type: prebuilt; unit: Cr; short: Op and Other Expenses (Q)
- `qIncPbiK` — PBIT (Q); premium: no; locked: no; type: prebuilt; unit: Cr
- `qIncPbtK` — PBT (Q); premium: no; locked: no; type: prebuilt; unit: Cr
