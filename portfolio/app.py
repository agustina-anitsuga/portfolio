# -*- coding: utf-8 -*-
"""Wiring of the pieces: spreadsheet + market -> computed portfolio."""

from .marketdata.bond_calculator import BondCalculator
from .marketdata.historical_prices import HistoricalPrices
from .marketdata.fx_rate_provider import FxRateProvider
from .marketdata.ppi_market_data import PpiMarketData
from .marketdata.ppi_session import PpiSession
from .marketdata.price_resolver import PriceResolver
from .marketdata.yahoo_market_data import YahooMarketData
from .portfolio.snapshot_builder import SnapshotBuilder
from .watchlist.watchlist_builder import WatchlistBuilder
from .settings import Settings
from .workbook.portfolio_workbook import PortfolioWorkbook


class PortfolioApp:
    """The single place where dependencies are assembled, so every other class
    receives what it needs and stays easy to test on its own."""

    def __init__(self, settings=None, ppi=None, yahoo=None, bonds=None, watchlist=None):
        settings = settings or Settings.from_env()
        session = PpiSession(settings)
        self._ppi = ppi or PpiMarketData(session)
        self._yahoo = yahoo or YahooMarketData()
        self._bonds = bonds if bonds is not None else BondCalculator(session)
        self._watchlist = watchlist if watchlist is not None else WatchlistBuilder()

    def snapshot(self, xlsx_path, with_watchlist=True, with_annual=True):
        """`with_watchlist=False` skips the watchlist entirely: it is the
        slowest part of a run (two Yahoo calls per watched instrument) and it
        has nothing to do with the portfolio itself. `with_annual=False` skips
        the year-end prices (one history request per instrument and year), so
        the annual tab stays empty."""
        workbook = PortfolioWorkbook(xlsx_path)
        fx = FxRateProvider(self._ppi).resolve(workbook.manual_fx)
        prices = PriceResolver(self._ppi, self._yahoo, fx, self._bonds)
        watchlist = self._watchlist if with_watchlist else None
        history = HistoricalPrices(self._ppi, self._yahoo) if with_annual else None
        return SnapshotBuilder(workbook, prices, fx, watchlist, history).build()
