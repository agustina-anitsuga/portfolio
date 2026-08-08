# -*- coding: utf-8 -*-
"""Wiring of the pieces: spreadsheet + market -> computed portfolio."""

from .marketdata.fx_rate_provider import FxRateProvider
from .marketdata.ppi_market_data import PpiMarketData
from .marketdata.ppi_session import PpiSession
from .marketdata.price_resolver import PriceResolver
from .marketdata.yahoo_market_data import YahooMarketData
from .portfolio.snapshot_builder import SnapshotBuilder
from .settings import Settings
from .workbook.portfolio_workbook import PortfolioWorkbook


class PortfolioApp:
    """The single place where dependencies are assembled, so every other class
    receives what it needs and stays easy to test on its own."""

    def __init__(self, settings=None, ppi=None, yahoo=None):
        settings = settings or Settings.from_env()
        self._ppi = ppi or PpiMarketData(PpiSession(settings))
        self._yahoo = yahoo or YahooMarketData()

    def snapshot(self, xlsx_path):
        workbook = PortfolioWorkbook(xlsx_path)
        fx = FxRateProvider(self._ppi).resolve(workbook.manual_fx)
        prices = PriceResolver(self._ppi, self._yahoo, fx)
        return SnapshotBuilder(workbook, prices, fx).build()
