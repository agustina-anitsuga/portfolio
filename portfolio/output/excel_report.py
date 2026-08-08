# -*- coding: utf-8 -*-
"""Optional secondary output: the same information in an .xlsx file."""

import openpyxl

from ..market import Market
from .general_dashboard_writer import GeneralDashboardWriter
from .market_dashboard_writer import MarketDashboardWriter
from .portfolio_sheet_writer import PortfolioSheetWriter


class ExcelReport:
    """A dashboard and a detail sheet per market, plus a general sheet up front."""

    def __init__(self, snapshot):
        self._snapshot = snapshot

    def save(self, path):
        workbook = openpyxl.Workbook()
        workbook.remove(workbook.active)
        self._write_markets(workbook)
        GeneralDashboardWriter(workbook).write(self._snapshot.reports)
        workbook.move_sheet("dashboard-general", offset=-(len(workbook.sheetnames) - 1))
        workbook.save(path)

    def _write_markets(self, workbook):
        dashboards = MarketDashboardWriter(workbook)
        portfolios = PortfolioSheetWriter(workbook)
        for market in Market.all():
            report = self._snapshot.report(market.key)
            dashboards.write(f"dashboard-{market.key}", report)
            portfolios.write(f"portfolio-{market.key}", report.rows)
