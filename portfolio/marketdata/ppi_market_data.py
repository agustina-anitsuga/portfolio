# -*- coding: utf-8 -*-
"""Prices, history and the MEP exchange rate from the PPI API."""

import datetime as dt

from .ppi_session import NO_CLIENT
from .trend import Trend

MISSING_INSTRUMENT_META = "falta Tipo PPI o Settlement PPI en la hoja instrumentos"
TREND_DAYS = 30


class PpiMarketData:
    """Everything asked of PPI, already normalized.

    The methods return (value, reason_if_it_failed): the reason matters,
    because when PPI does not quote something you need to tell "the market is
    closed" apart from "the ticker is misspelled" or "I am being rate-limited".
    """

    def __init__(self, session):
        self._session = session

    def price(self, ticker, ppi_type, settlement):
        if not self._session.available:
            return None, NO_CLIENT
        if not ppi_type or not settlement:
            return None, MISSING_INSTRUMENT_META
        return self._session.call(lambda: self._read_price(ticker, ppi_type, settlement))

    def trend(self, ticker, ppi_type, settlement):
        """Best-effort variation and price series over the last 30 days.

        The series is what draws the trend line in the dashboard; the
        percentage is computed from that same series and kept because it is
        what sorts the column and what goes into the Excel file.
        """
        if not ppi_type or not settlement:
            return Trend.empty()
        value, _ = self._session.call(lambda: self._read_trend(ticker, ppi_type, settlement))
        return value or Trend.empty()

    def mep_rate(self):
        """Implicit MEP dollar: price in ARS of AL30 / price in USD of AL30D
        (same bond, two different settlement currencies). It is the same pair
        PPI uses as the example for its real-time feed.

        AL30/AL30D trade on BYMA, so outside Argentine market hours (roughly 11
        to 17hs on business days) it is normal for them not to return a price
        -- that is not a problem with this script.
        """
        return self._session.call(self._read_mep_rate)

    def _read_price(self, ticker, ppi_type, settlement):
        data = self._session.client.marketdata.current(ticker, ppi_type, settlement)
        if not isinstance(data, dict):
            return None, f"PPI devolvio {type(data).__name__} en vez de un dict: {str(data)[:120]}"
        price = data.get("price")
        if not price:
            return None, f"PPI respondio sin precio (campos: {sorted(data)[:8]})"
        return self._per_unit(float(price), ppi_type), None

    @staticmethod
    def _per_unit(price, ppi_type):
        """Bonds are quoted by PPI "per 100 of nominal value" (the standard
        market convention), not per unit -- without this adjustment the value
        of the position ends up ~100x inflated. Note this does NOT affect the
        MEP rate, because that is a ratio between two BONOS prices and the
        factor of 100 cancels out on its own."""
        return price / 100.0 if ppi_type == "BONOS" else price

    def _read_trend(self, ticker, ppi_type, settlement):
        date_to = dt.datetime.now()
        date_from = date_to - dt.timedelta(days=TREND_DAYS)
        history = self._session.client.marketdata.search(ticker, ppi_type, settlement, date_from, date_to)
        prices = [float(h["price"]) for h in (history or []) if h.get("price")]
        if len(prices) < 2:
            return None, "historico vacio o con menos de 2 puntos"
        trend = Trend.from_series(prices)
        if trend is None:
            return None, "el primer precio del historico es cero"
        return trend, None

    def _read_mep_rate(self):
        current = self._session.client.marketdata.current
        prices = {t: self._quoted_price(current(t, "BONOS", "INMEDIATA")) for t in ("AL30", "AL30D")}
        if prices["AL30"] and prices["AL30D"]:
            return prices["AL30"] / prices["AL30D"], None
        missing = [t for t, p in prices.items() if not p]
        return None, (f"PPI no devolvio precio para {' y '.join(missing)} "
                      f"(probablemente fuera del horario de mercado)")

    @staticmethod
    def _quoted_price(data):
        price = data.get("price") if isinstance(data, dict) else None
        return float(price) if price else None
