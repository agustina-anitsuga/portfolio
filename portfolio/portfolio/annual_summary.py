# -*- coding: utf-8 -*-
"""The rows of the "Anual" tab: one per year with purchases."""

import datetime as dt

from ..market import CURRENCIES
from .position import EPSILON


class AnnualSummary:
    """What the trades of each year turned into.

    Per year and currency:
    - invested_gross: what was bought that year.
    - invested_net: the same minus the cost of what was sold that year (the
      "Invertido" of the year filter).
    - close_value: that net position valued at the last close of the year.
      None when a price or the exchange rate of that day is missing: a partial
      total would look real, so it is left empty and `close_missing` says how
      many positions could not be valued.
    - year_pct: close_value against invested_net.
    - gain / gain_pct: today's value of that net position against invested_net.
    - detail: the same figures per instrument, for the expandable year row.

    The current year has no close yet, so its "close" is today's value.
    """

    def __init__(self, reports_by_year, history, today=None):
        self._reports_by_year = reports_by_year
        self._history = history
        self._today = today or dt.date.today()

    def rows(self):
        return [self._row(year, reports) for year, reports in
                sorted(self._reports_by_year.items(), reverse=True)]

    def _row(self, year, reports):
        holdings = [h for report in reports.values() for h in report.holdings]
        row = {"year": year, "positions": len(holdings),
               "close_missing": max((self._missing(year, holdings, c) for c in CURRENCIES), default=0)}
        row["detail"] = [self._detail(year, h) for h in holdings]
        for currency in CURRENCIES:
            row.update(self._figures(year, holdings, currency))
        return row

    def _detail(self, year, holding):
        """The same figures for one instrument: what the year row is made of."""
        row = {"key": holding.instrument.key, "market": holding.market.key,
               "name": holding.instrument.name, "units": holding.units,
               "units_bought": holding.position.units_bought}
        for currency in CURRENCIES:
            row.update(self._figures(year, [holding], currency))
            row[f"close_price_{currency}"] = self._holding_price(year, holding, currency)
        return row

    def _figures(self, year, holdings, currency):
        gross = sum(h.position.cost_bought[currency] for h in holdings)
        net = sum(h.metrics[currency].invested for h in holdings)
        values = [h.metrics[currency].value for h in holdings]
        value_now = None if any(v is None for v in values) else sum(values)
        close = self._close_value(year, holdings, currency)
        return {
            f"invested_gross_{currency}": gross,
            f"invested_net_{currency}": net,
            f"close_value_{currency}": close,
            f"year_pct_{currency}": _pct(close, net),
            f"gain_{currency}": None if value_now is None else value_now - net,
            f"gain_pct_{currency}": None if value_now is None else _pct(value_now, net),
        }

    def _close_value(self, year, holdings, currency):
        closes = [self._holding_close(year, h, currency) for h in holdings if h.units > EPSILON]
        return None if any(c is None for c in closes) else sum(closes)

    def _missing(self, year, holdings, currency):
        return sum(1 for h in holdings
                   if h.units > EPSILON and self._holding_close(year, h, currency) is None)

    def _holding_close(self, year, holding, currency):
        price = self._holding_price(year, holding, currency)
        return None if price is None else price * holding.units

    def _holding_price(self, year, holding, currency):
        """Price of one unit at the close of the year. For a Cedear that is the
        price of the Cedear itself (what PPI quotes and what the units are
        counted in), so the ratio is already inside it."""
        if int(year) >= self._today.year:
            return holding.quote.price(currency)
        date = dt.date(int(year), 12, 31)
        price = self._history.close(holding.market, holding.instrument, date)
        return self._history.convert(price, holding.market.native_currency, currency, date)


def _pct(value, base):
    return ((value - base) / base * 100) if (value is not None and base) else None
