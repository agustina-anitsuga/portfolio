# -*- coding: utf-8 -*-
"""Builds the whole portfolio out of the spreadsheet and the market."""

from .position_tracker import PositionTracker
from .report_builder import ReportBuilder
from .snapshot import PortfolioSnapshot
from .transaction_ledger import TransactionLedger


class SnapshotBuilder:
    """Computes the entire portfolio: the full one and one version per year
    with purchases.

    The per-year scope does not hide rows, it recomputes: when 2025 is picked,
    the units, average cost, invested amount and P&L of each position come only
    from what was traded in 2025.
    """

    def __init__(self, workbook, prices, fx):
        self._workbook = workbook
        self._prices = prices
        self._fx = fx
        self._reports = ReportBuilder(workbook, prices)

    def build(self):
        positions = self._positions()
        reports = self._reports.build(positions)
        return PortfolioSnapshot(
            reports=reports,
            reports_by_year={y: self._reports.build(self._positions(y)) for y in self._buy_years(positions)},
            fx=self._fx,
            transactions=TransactionLedger(self._workbook.all_transactions(), reports).rows(),
        )

    def _positions(self, year=None):
        return PositionTracker(self._fx, year).track_all(self._workbook)

    @staticmethod
    def _buy_years(positions):
        """Years that actually had purchases, from the most recent to the
        oldest -- these are the options of the year filter."""
        years = {year for by_ticker in positions.values()
                 for position in by_ticker.values() for year in position.buy_years}
        return sorted(years, reverse=True)
