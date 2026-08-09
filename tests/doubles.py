# -*- coding: utf-8 -*-
"""Test doubles and builders.

The tests never touch the network: PPI and Yahoo are always replaced by the
doubles defined here, so a failing test means a real bug and not a closed
market or a missing API key.
"""

import datetime as dt

import openpyxl

from portfolio.market import ARS, USD, Market
from portfolio.marketdata.quote import Quote
from portfolio.marketdata.trend import Trend
from portfolio.portfolio.holding import Holding
from portfolio.portfolio.position import Position
from portfolio.workbook.instrument import Instrument
from portfolio.workbook.transaction import Transaction

USD_MARKET = Market.get("usd")
CEDEARS_MARKET = Market.get("cedears")
MERVAL_MARKET = Market.get("merval")
RSU_MARKET = Market.get("rsu")
BONDS_MARKET = Market.get("bonds")


class FakePpi:
    """Stands in for PpiMarketData. Records what was asked, answers canned."""

    def __init__(self, prices=None, trends=None, mep=(None, "sin mercado")):
        self._prices = prices or {}
        self._trends = trends or {}
        self._mep = mep
        self.price_calls = []
        self.trend_calls = []

    def price(self, ticker, ppi_type, settlement):
        self.price_calls.append((ticker, ppi_type, settlement))
        return self._prices.get(ticker, (None, "sin precio de PPI"))

    def trend(self, ticker, ppi_type, settlement):
        self.trend_calls.append((ticker, ppi_type, settlement))
        return self._trends.get(ticker, Trend.empty())

    def mep_rate(self):
        return self._mep


class FakeYahoo:
    """Stands in for YahooMarketData."""

    def __init__(self, prices=None):
        self._prices = prices or {}
        self.calls = []

    def price(self, ticker):
        self.calls.append(ticker)
        return self._prices.get(ticker, (None, "sin precio de Yahoo"))


class FakeSession:
    """Stands in for PpiSession: runs the request once, with no pacing.

    It keeps the real contract of turning an exception into a reason, because
    callers rely on that to never let a market failure reach the user.
    """

    def __init__(self, client=None, available=True):
        self.client = client
        self.available = available
        self.calls = 0

    def call(self, request):
        self.calls += 1
        if not self.available:
            return None, "sin cliente"
        try:
            return request()
        except Exception as e:
            return None, f"error consultando PPI: {type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# Domain builders
# ---------------------------------------------------------------------------


def make_instrument(key="AAA", **kwargs):
    defaults = dict(name="Alpha Corp", ppi_type="ACCIONES-USA", settlement="A-48HS",
                    ratio=1, sector="Technology", currency="USD", instrument_type="Stock")
    defaults.update(kwargs)
    return Instrument(key=key, **defaults)


def make_transaction(market=USD_MARKET, ticker="AAA", op="BUY", units=10.0,
                     date=dt.datetime(2025, 3, 15), amount_ars=10000.0, amount_usd=10.0):
    return Transaction(market=market, ticker=ticker, op=op, units=units, date=date,
                       amount_ars=amount_ars, amount_usd=amount_usd)


def make_position(units=10.0, cost_ars=10000.0, cost_usd=10.0, year="2025"):
    position = Position()
    position.buy(units, {ARS: cost_ars, USD: cost_usd}, year, in_scope=True)
    return position


def make_quote(price_ars=2000.0, price_usd=2.0, source="PPI (en vivo)", debug_note=None):
    return Quote(price_ars=price_ars, price_usd=price_usd, source=source, debug_note=debug_note)


def make_holding(market=USD_MARKET, instrument=None, position=None, quote=None, trend=None):
    return Holding(
        market=market,
        instrument=instrument or make_instrument(),
        position=position or make_position(),
        quote=quote or make_quote(),
        trend=trend or Trend.empty(),
    )


# ---------------------------------------------------------------------------
# Spreadsheet builder
# ---------------------------------------------------------------------------

HEADERS = {
    "instrumentos": ["Key", "Nombre", "Tipo PPI", "Settlement PPI", "Ratio (cedears)",
                     "Sector", "Moneda Origen", "Precio Manual", "Tipo (Stock/ETF)"],
    "config": ["Parametro", "Valor", "Notas"],
    "tx-usd": ["Key", "Op", "Units", "Date", "Share Price (@Origin)",
               "Total amount (@Origin)", "Total amount (ARS) [opcional]"],
    "tx-cedears": ["Key", "Op", "Units (@Local)", "Date", "Total amount (@Local)",
                   "Share Price (@Origin)", "Total amount (@Origin)", "Ratio"],
    "tx-merval": ["Key", "Op", "Units", "Date", "Share Price (ARS)",
                  "Total amount (ARS)", "Total amount (USD)", "Share Price (USD)"],
    "tx-rsu": ["Key", "Op", "Units", "Date", "Share Price (@Origin)",
               "Total amount (@Origin)", "Total amount (ARS) [opcional]"],
    "tx-bonds": ["Key", "Op", "Units", "Date", "Share Price (ARS)",
                 "Total amount (ARS)", "Total amount (USD)", "Share Price (USD)"],
}


def write_workbook(path, instruments=(), manual_fx=None, sheets=None, skip=(), config_label=None):
    """Builds a spreadsheet with the same layout as the real one.

    `sheets` maps a sheet name to its data rows (already in column order).
    `skip` lists sheets that should not exist at all.
    """
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    sheets = sheets or {}
    for name, headers in HEADERS.items():
        if name in skip:
            continue
        sheet = workbook.create_sheet(name)
        sheet.append(headers)
        if name == "instrumentos":
            for row in instruments:
                sheet.append(list(row))
        elif name == "config":
            sheet.append([config_label or "USD/ARS Manual (respaldo)", manual_fx, "nota"])
        else:
            for row in sheets.get(name, []):
                sheet.append(list(row))
    workbook.save(path)
    return str(path)
