# -*- coding: utf-8 -*-
"""Prices on a past date, for the year-end valuation."""

from ..market import ARS, USD

CEDEARS = "cedears"


class HistoricalPrices:
    """Same source order as PriceResolver (PPI first, Yahoo for USD
    instruments), but for a given day. Anything it cannot get is None: the
    caller leaves that figure empty instead of inventing it.

    The exchange rate of a past day is the implicit MEP (AL30 / AL30D) of
    that day, the same pair the live rate uses.
    """

    def __init__(self, ppi_market_data, yahoo_market_data):
        self._ppi = ppi_market_data
        self._yahoo = yahoo_market_data
        self._cache = {}

    def close(self, market, instrument, date):
        """Price in the market's NATIVE currency, or None."""
        return self._cached(("close", market.key, instrument.key, date),
                            lambda: self._resolve_close(market, instrument, date))

    def mep(self, date):
        """ARS per USD on that day, or None."""
        return self._cached(("mep", date), lambda: self._resolve_mep(date))

    def convert(self, amount, native, target, date):
        """`amount` in the native currency expressed in `target`, or None."""
        if amount is None:
            return None
        if native == target:
            return amount
        rate = self.mep(date)
        if not rate:
            return None
        return amount * rate if target == ARS else amount / rate

    def _cached(self, key, resolve):
        if key not in self._cache:
            self._cache[key] = resolve()
        return self._cache[key]

    def _resolve_close(self, market, instrument, date):
        if market.key == CEDEARS:
            price = self._cedear_from_underlying(market, instrument, date)
            if price is not None:
                return price
        price, _ = self._ppi.close_on(instrument.key, instrument.ppi_type, instrument.settlement, date)
        if price is None and market.native_currency == USD:
            price, _ = self._yahoo.close_on(instrument.key, date)
        return price

    def _cedear_from_underlying(self, market, instrument, date):
        """ARS price of one Cedear, from the close of the underlying stock and
        the ratio of the instruments sheet.

        PPI's history of a Cedear is adjusted when its ratio changes, while the
        units in the spreadsheet are counted with the ratio they were bought
        under -- valuing those units with the adjusted price inflates (or
        deflates) the result by the ratio change. The underlying and the ratio
        of the sheet do not have that problem.
        """
        ratio = _positive(instrument.ratio)
        rate = self.mep(date)
        if not ratio or not rate:
            return None
        underlying, _ = self._yahoo.close_on(instrument.key, date)
        return underlying / ratio * rate if underlying else None

    def _resolve_mep(self, date):
        ars, _ = self._ppi.close_on("AL30", "BONOS", "INMEDIATA", date)
        usd, _ = self._ppi.close_on("AL30D", "BONOS", "INMEDIATA", date)
        return ars / usd if (ars and usd) else None


def _positive(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None
