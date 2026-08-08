#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_dashboard.py

Reads "portfolio.xlsx" (sheets: instrumentos, config, tx-usd,
tx-cedears, tx-merval, tx-rsu, tx-bonds), fetches current prices through the
PPI (Portfolio Personal Inversiones) API and generates "Portfolio
Dashboard.html": an interactive dashboard with one tab per instrument type (US
Stocks, Cedears, Acciones Merval, RSU, Bonos) plus a general one, each showing:

  - average purchase price, current price, invested amount, current value,
    P&L $ and P&L % -- ALL of it in pesos (ARS) and dollars (USD) at once.
  - sales handling: units sold, cost of sales, income from sales, realized
    P&L $ and %, also in both currencies.
  - a search box, a sector filter, an instrument type filter (Stock/ETF), a
    purchase year filter and a display currency filter, columns sortable by
    click, and charts.

  The year filter is present in every tab and only lists years that actually
  had purchases. It does NOT hide rows: it recomputes the whole portfolio using
  only that year's trades. Picking 2025 makes the units, average cost, invested
  amount and P&L of every position come only from what was traded in 2025 -- if
  you bought SPY in 2025 and in 2026, the 2025 slice shows only the 2025 part.

  The cost of sales is computed the same way, walking the WHOLE history in
  chronological order, so a 2026 sale of units bought in 2025 is valued at the
  real cost of those units. Practical consequence: what each year shows adds up
  exactly to the total of the full portfolio.

  RSU is treated exactly like the other portfolios (same average cost, P&L and
  dual-currency logic); the only difference is that the source sheet is
  "tx-rsu" instead of "tx-usd".

HOW ARS AND USD ARE CONVERTED
    Cost, invested amount and sales are computed per TRADE, using the real
    amount recorded in each currency:
    - Cedears: tx-cedears always carries the real amount in ARS (@Local, what
      trades on BYMA) and in USD (@Origin) for every trade.
    - Merval: tx-merval always carries "Total amount (ARS)", and "Total amount
      (USD)" when you recorded it -- computed with the exchange rate of the DAY
      of that trade, exactly as it was in the original spreadsheet.
    - USD: tx-usd always carries "Total amount (@Origin, USD)", and "Total
      amount (ARS)" when you recorded it. Old trades never had that value, so
      for those there is no way to know the historical ARS amount.
    When a single trade has no amount recorded in the other currency, THAT ONE
    trade (not the whole position) is converted at TODAY's exchange rate as an
    approximation, and the position is flagged in the dashboard so you know
    part of it is approximate.

    The current price and the market value are "as of today" by definition, so
    those always use today's exchange rate in both currencies.

    Today's exchange rate is obtained by first trying the MEP dollar through
    PPI (AL30 in ARS / AL30D in USD, the same pair PPI uses as the example for
    its real-time feed). If PPI is unavailable, the manual value from the
    "config" sheet is used.

REQUIREMENTS
    pip install openpyxl ppi-client yfinance

    yfinance is optional: without it the script still works, it simply loses
    the Yahoo Finance fallback (see below).

PPI CREDENTIALS
    1. Go to your PPI account -> Gestiones -> Gestion de servicio API -> enable.
    2. You will get a Public Key and a Private Key.
    3. Expose the credentials as environment variables before running:

        export PPI_PUBLIC_KEY="your_public_key"
        export PPI_PRIVATE_KEY="your_private_key"

    Fallback order for each instrument's price:
    1. Live PPI.
    2. If it is a USD instrument (US Stocks or RSU) and PPI returned nothing
       (no credentials, a ticker PPI does not trade, or simply no data because
       the US market is closed right now) -> Yahoo Finance, which needs no API
       key and returns the last available price even when the market is
       closed. This does NOT apply to Cedears (the price of the Cedear on BYMA
       is not the price of the underlying stock in USD -- using Yahoo there
       would give a wrong number).
    3. The manual price from the "Precio Manual" column of the instrumentos sheet.
    4. "no disponible" when none of the above worked.

USAGE
    python3 generate_dashboard.py "portfolio.xlsx" --out-html "Portfolio Dashboard.html"

CODE
    This file is only the entry point. The implementation lives in the
    portfolio_dashboard/ package:

      settings.py                 credentials and request limits (environment)
      market.py                   the instrument types and their sheets
      app.py                      assembles the dependencies
      cli.py / console_summary.py command line and closing summary
      marketdata/                 PPI/Yahoo prices, exchange rate, fallbacks
      workbook/                   spreadsheet reading
      portfolio/                  positions, metrics and reports
      output/                     HTML dashboard (assets/) and Excel workbook
"""

import sys

from portfolio_dashboard.cli import main

if __name__ == "__main__":
    sys.exit(main())
