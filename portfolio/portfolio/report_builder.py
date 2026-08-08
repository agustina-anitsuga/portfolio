# -*- coding: utf-8 -*-
"""From positions to reports, resolving the price of each instrument."""

from ..market import Market
from .holding import Holding
from .market_report import MarketReport


class ReportBuilder:
    """One MarketReport per market. Prices are requested only once by the
    PriceResolver, which caches them: building the reports of each year does
    not cost a single extra request to PPI/Yahoo."""

    def __init__(self, workbook, prices):
        self._workbook = workbook
        self._prices = prices

    def build(self, positions_by_market):
        return {market.key: self._report(market, positions_by_market[market.key])
                for market in Market.all()}

    def _report(self, market, positions):
        holdings = [self._holding(market, ticker, position)
                    for ticker, position in positions.items() if not position.is_empty]
        return MarketReport(market, holdings)

    def _holding(self, market, ticker, position):
        instrument = self._workbook.instrument(ticker)
        return Holding(
            market, instrument, position,
            quote=self._prices.quote(market, instrument),
            trend=self._prices.trend(market, instrument),
        )
