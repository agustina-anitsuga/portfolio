# -*- coding: utf-8 -*-
"""The rows of the "Anual" tab: one per calendar year, chained."""

import datetime as dt

from ..market import CURRENCIES, Market
from .position import EPSILON
from .position_tracker import PositionTracker

# Figures that can be missing (they need a closing price). The rest come
# straight from the trades and are always there.
NULLABLE = ("base_value", "close_value", "unrealized", "result")
ALWAYS = ("bought", "sold", "net_contribution", "realized", "invested")


class AnnualSummary:
    """The whole portfolio, year by year, as it stood at each 31/12.

    Per year and currency:
    - base_value: what the portfolio was worth at the close of the previous
      year (its invested amount plus its unrealized P&L at that date). It is
      the starting point of the year.
    - bought / sold: what was bought that year, and what the sales of that year
      brought in. net_contribution = bought - sold.
    - realized: P&L of the sales of that year, against the real average cost.
    - invested: cost of the units still held at the close of the year.
    - close_value: those units at the last close of the year (the current year
      uses today's price). None when a price or that day's exchange rate is
      missing -- a partial total would look real -- and `close_missing` says
      how many positions could not be valued.
    - unrealized: close_value - invested, i.e. the unrealized P&L at 31/12.
    - result: close_value - base_value - net_contribution, which is the change
      in unrealized P&L during the year plus the realized P&L.
    - result_pct: result over what was at stake (base_value + bought).
    - detail: the same figures per instrument, for the expandable year row.
    """

    def __init__(self, workbook, prices, fx, history, today=None):
        self._workbook = workbook
        self._prices = prices
        self._fx = fx
        self._history = history
        self._today = today or dt.date.today()

    def rows(self):
        rows, previous = [], {}
        for year in self._years():
            details = self._details(year, previous)
            previous = {(d["market"], d["key"]): d for d in details}
            rows.append(self._row(year, details))
        return list(reversed(rows))

    def _years(self):
        years = {int(tx.year) for market in Market.all()
                 for tx in self._workbook.transactions(market) if tx.op and tx.year}
        if not years:
            return []
        return [str(y) for y in range(min(years), max(max(years), self._today.year) + 1)]

    def _details(self, year, previous):
        positions = PositionTracker(self._fx, scope_year=year, until_year=year).track_all(self._workbook)
        details = []
        for market in Market.all():
            for ticker, position in positions[market.key].items():
                before = previous.get((market.key, ticker))
                held = position.held_units > EPSILON
                traded = position.units_bought > EPSILON or position.units_sold > EPSILON
                if held or traded or before:
                    details.append(self._detail(year, market, ticker, position, before))
        return details

    def _detail(self, year, market, ticker, position, before):
        instrument = self._workbook.instrument(ticker)
        units = position.held_units
        row = {"key": ticker, "market": market.key, "name": instrument.name, "units": units}
        for currency in CURRENCIES:
            price = self._price(year, market, instrument, currency) if units > EPSILON else None
            invested = position.held_cost(currency)
            close = (price * units if price is not None else None) if units > EPSILON else 0.0
            base = before[f"close_value_{currency}"] if before else 0.0
            bought = position.cost_bought[currency]
            sold = position.income_from_sales[currency]
            row.update(_figures(currency, {
                "base_value": base, "bought": bought, "sold": sold,
                "net_contribution": bought - sold,
                "realized": sold - position.cost_of_sales[currency],
                "invested": invested, "close_value": close,
                "unrealized": None if close is None else close - invested,
                "result": None if (close is None or base is None) else close - base - (bought - sold),
            }))
            row[f"close_price_{currency}"] = price
        return row

    def _row(self, year, details):
        row = {"year": year, "positions": sum(1 for d in details if d["units"] > EPSILON),
               "detail": details,
               "close_missing": max((sum(1 for d in details if d[f"close_value_{c}"] is None)
                                     for c in CURRENCIES), default=0)}
        for currency in CURRENCIES:
            totals = {k: sum(d[f"{k}_{currency}"] for d in details) for k in ALWAYS}
            for k in NULLABLE:
                values = [d[f"{k}_{currency}"] for d in details]
                totals[k] = None if any(v is None for v in values) else sum(values)
            row.update(_figures(currency, totals))
        return row

    def _price(self, year, market, instrument, currency):
        """Price of one unit at the close of the year. For a Cedear that is the
        price of the Cedear itself (what PPI quotes and what the units are
        counted in), so the ratio is already inside it."""
        if int(year) >= self._today.year:
            return self._prices.quote(market, instrument).price(currency)
        date = dt.date(int(year), 12, 31)
        price = self._history.close(market, instrument, date)
        return self._history.convert(price, market.native_currency, currency, date)


def _figures(currency, values):
    row = {f"{k}_{currency}": v for k, v in values.items()}
    result, base = values["result"], values["base_value"]
    stake = None if base is None else base + values["bought"]
    row[f"result_pct_{currency}"] = (result / stake * 100) if (result is not None and stake) else None
    return row
