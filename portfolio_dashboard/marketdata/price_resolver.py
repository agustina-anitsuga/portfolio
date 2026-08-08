# -*- coding: utf-8 -*-
"""Fallback order for each instrument's price."""

from ..market import USD
from .quote import Quote

PPI_SOURCE = "PPI (en vivo)"
YAHOO_SOURCE = "Yahoo Finance"
MANUAL_SOURCE = "manual"


class PriceResolver:
    """1) live PPI, 2) Yahoo Finance for USD instruments only, 3) the manual
    price from the instruments sheet, 4) no price.

    Yahoo does NOT apply to Cedears: the price of the Cedear on BYMA is not the
    price of the underlying stock in USD, so using it there would give a wrong
    number.

    Caches by (market, ticker) because the dashboard builds one report per year
    on top of the full one, and today's price is the same in all of them.
    """

    def __init__(self, ppi_market_data, yahoo_market_data, fx):
        self._ppi = ppi_market_data
        self._yahoo = yahoo_market_data
        self._fx = fx
        self._quotes = {}
        self._trends = {}

    def quote(self, market, instrument):
        return self._cached(self._quotes, market, instrument, self._resolve_quote)

    def trend(self, market, instrument):
        return self._cached(self._trends, market, instrument, self._resolve_trend)

    def _cached(self, cache, market, instrument, resolve):
        cache_key = (market.key, instrument.key)
        if cache_key not in cache:
            cache[cache_key] = resolve(market, instrument)
        return cache[cache_key]

    def _resolve_trend(self, market, instrument):
        return self._ppi.trend(instrument.key, instrument.ppi_type, instrument.settlement)

    def _resolve_quote(self, market, instrument):
        native = market.native_currency
        price, source, failures = self._first_available(native, instrument)
        if price is None:
            return Quote.unavailable(" | ".join(failures) or None)
        return Quote.from_native(price, native, source, self._fx)

    def _first_available(self, native, instrument):
        """(price, source, reasons_of_the_sources_that_failed)."""
        failures = []
        live, error = self._ppi.price(instrument.key, instrument.ppi_type, instrument.settlement)
        if live is not None:
            return live, PPI_SOURCE, failures
        _record(failures, "PPI", error)

        if native == USD:
            yahoo, error = self._yahoo.price(instrument.key)
            if yahoo is not None:
                return yahoo, YAHOO_SOURCE, failures
            _record(failures, "Yahoo", error)

        if instrument.manual_price is not None:
            return float(instrument.manual_price), MANUAL_SOURCE, failures
        return None, None, failures


def _record(failures, source, error):
    if error:
        failures.append(f"{source}: {error}")
