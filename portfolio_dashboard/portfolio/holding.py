# -*- coding: utf-8 -*-
"""One line of the report: a position with its instrument and its price."""

from ..market import CURRENCIES
from .currency_metrics import CurrencyMetrics


class Holding:
    """Joins what the spreadsheet knows (instrument and position) with what the
    market knows (today's price and trend), and exposes it as the row the HTML
    and the Excel file consume."""

    def __init__(self, market, instrument, position, quote, trend):
        self.market = market
        self.instrument = instrument
        self.position = position
        self.quote = quote
        self.trend = trend
        self.units = position.reported_units
        self.metrics = {c: self._metrics(c) for c in CURRENCIES}
        self._portfolio_share = dict.fromkeys(CURRENCIES)

    def _metrics(self, currency):
        return CurrencyMetrics.compute(self.position, currency, self.units, self.quote.price(currency))

    def value(self, currency):
        return self.metrics[currency].value

    @property
    def unpriced(self):
        return all(self.value(c) is None for c in CURRENCIES)

    def set_portfolio_share(self, currency, share):
        """% this line represents of the total of its tab."""
        self._portfolio_share[currency] = share

    def as_dict(self):
        row = {
            "key": self.instrument.key, "market": self.market.key,
            "name": self.instrument.name, "sector": self.instrument.sector or "-",
            "ratio": self.instrument.ratio or "", "instrument_type": self.instrument.instrument_type or "-",
            "units": self.units, "units_sold": self.position.units_sold,
            "trend_30d": self.trend.pct, "trend_series": self.trend.series,
            "buy_years": self.position.buy_years, "oversold": self.position.oversold,
            "price_source": self.quote.source, "fx_approx": not self.position.dual_real,
            "native_currency": self.market.native_currency,
            "price_debug_note": self.quote.debug_note,
        }
        for currency in CURRENCIES:
            row.update(self.metrics[currency].as_dict(currency))
        for currency in CURRENCIES:
            row[f"pct_portfolio_{currency}"] = self._portfolio_share[currency]
        return row
