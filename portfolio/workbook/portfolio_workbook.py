# -*- coding: utf-8 -*-
"""The whole spreadsheet."""

import openpyxl

from ..market import Market
from .config_sheet import ConfigSheet
from .contribution_sheet import ContributionSheet
from .instrument import Instrument
from .instrument_sheet import InstrumentSheet
from .transaction_sheet import TransactionSheet
from .watchlist_sheet import WatchlistSheet


class PortfolioWorkbook:
    """Entry point to the spreadsheet: instruments, config and the trades of
    each market. It is read once and kept in memory, so the per-year recalc
    never touches the disk again."""

    def __init__(self, path):
        workbook = openpyxl.load_workbook(path, data_only=True)
        self.instruments = InstrumentSheet(workbook).read()
        config = ConfigSheet(workbook)
        self.manual_fx = config.manual_fx()
        self.manual_ccl = config.manual_ccl()
        self.contribution = ContributionSheet(workbook).plan()
        self.watchlist = WatchlistSheet(workbook).tickers()
        self._sheets = {m.key: TransactionSheet(workbook, m) for m in Market.all()}
        self._chronological = {k: s.chronological() for k, s in self._sheets.items()}

    def instrument(self, key):
        return self.instruments.get(key) or Instrument.unknown(key)

    def transactions(self, market):
        """Trades of one market, in chronological order."""
        return self._chronological[market.key]

    def all_transactions(self):
        """Every trade, in the entry order of each sheet -- this is what feeds
        the "Transacciones" tab."""
        return [tx for market in Market.all() for tx in self._sheets[market.key].rows()]
