# -*- coding: utf-8 -*-
"""Where the exchange rate of the day comes from."""

from .fx_rate import FxRate

LIVE_SOURCE = "PPI (MEP AL30/AL30D, en vivo)"
MANUAL_SOURCE = "manual (hoja config)"


class FxRateProvider:
    """PPI's live MEP dollar first; if it is not available, the manual value
    from the "config" sheet."""

    def __init__(self, ppi_market_data):
        self._ppi = ppi_market_data

    def resolve(self, manual_fx):
        live, reason = self._ppi.mep_rate()
        if live:
            return FxRate(live, LIVE_SOURCE)
        if manual_fx:
            return FxRate(float(manual_fx), MANUAL_SOURCE)
        return FxRate.unavailable(reason)
