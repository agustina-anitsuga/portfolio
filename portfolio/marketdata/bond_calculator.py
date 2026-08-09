# -*- coding: utf-8 -*-
"""PPI's bond calculator (1.0/MarketData/Bonds/Estimate)."""

import datetime as dt

from .bond_analytics import BondAnalytics

try:
    from ppi_client.models.estimate_bonds import EstimateBonds
    HAVE_PPI = True
except ImportError:
    HAVE_PPI = False

# PPI quotes bonds per 100 of nominal value, and the calculator expects that
# same quoted price -- not the per-unit one the rest of the dashboard uses.
QUOTE_NOMINAL = 100.0
QUANTITY_TYPE = "PAPELES"


class BondCalculator:
    """Yield, coupon, maturity and duration for one bond.

    Best-effort like every other market call: any failure just means the bond
    columns stay empty, never an error reaching the user.
    """

    def __init__(self, session):
        self._session = session

    def analytics(self, ticker, unit_price, units, fx):
        """`unit_price` is the per-unit price in the bond's quoting currency."""
        if not HAVE_PPI or not self._session.available:
            return BondAnalytics.empty()
        if not unit_price or not units or not fx:
            # without an exchange rate the yield would be computed against
            # cash flows in another currency, which is worse than no yield.
            return BondAnalytics.empty()
        value, _ = self._session.call(lambda: self._estimate(ticker, unit_price, units, fx))
        return value or BondAnalytics.empty()

    def _estimate(self, ticker, unit_price, units, fx):
        data = self._session.client.marketdata.estimate_bonds(
            self._request(ticker, unit_price, units, fx))
        if not isinstance(data, dict):
            return None, f"la calculadora devolvio {type(data).__name__} en vez de un dict"
        if not data.get("tir") and not data.get("expirationDate"):
            return None, "la calculadora respondio sin datos del bono"
        return BondAnalytics.from_response(data), None

    @staticmethod
    def _request(ticker, unit_price, units, fx):
        return EstimateBonds(
            ticker=ticker,
            date=dt.datetime.now().strftime("%Y-%m-%d"),
            quantityType=QUANTITY_TYPE,
            quantity=units,
            price=unit_price * QUOTE_NOMINAL,
            amountOfMoney=None,
            exchangeRate=fx.value,
            equityRate=None,
            exchangeRateAmortization=fx.value,
            rateAdjustmentAmortization=None,
        )
