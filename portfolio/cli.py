# -*- coding: utf-8 -*-
"""Command line interface."""

import argparse
import sys
from contextlib import nullcontext

from .app import PortfolioApp
from .console_summary import ConsoleSummary
from .output.excel_report import ExcelReport
from .output.html_dashboard import HtmlDashboard
from .settings import Settings
from .sources.google_sheet import GoogleSheet, SheetSourceError


class DashboardCli:
    """python3 generate_dashboard.py                 -> planilla de Google Drive
    python3 generate_dashboard.py portfolio.xlsx  -> archivo local"""

    def __init__(self, app=None, settings=None, sheet=None):
        self._settings = settings or Settings.from_env()
        self._app = app or PortfolioApp(self._settings)
        self._sheet = sheet  # built on demand: a local run needs no Google credentials

    def run(self, argv=None):
        args = self._parse_args(argv)
        try:
            with self._spreadsheet(args) as xlsx_path:
                snapshot = self._app.snapshot(xlsx_path, with_watchlist=not args.no_watchlist,
                                              with_annual=not args.no_annual)
        except SheetSourceError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1

        HtmlDashboard(snapshot).write(args.out_html)
        generated = [args.out_html]
        if args.out_xlsx:
            ExcelReport(snapshot).save(args.out_xlsx)
            generated.append(args.out_xlsx)

        ConsoleSummary(snapshot).print_report(generated)
        if not args.xlsx_path:
            print(f"  Planilla de Google Drive editada el "
                  f"{self._sheet.modified_time:%d/%m/%Y %H:%M}.")
        return 0

    def _spreadsheet(self, args):
        """A local path is used as is; without one the spreadsheet is exported
        from Google Drive to a temporary file."""
        if args.xlsx_path:
            return nullcontext(args.xlsx_path)
        if self._sheet is None:
            self._sheet = GoogleSheet.from_settings(self._settings, sheet_id=args.sheet_id)
        return self._sheet.downloaded()

    @staticmethod
    def _parse_args(argv):
        parser = argparse.ArgumentParser()
        parser.add_argument("xlsx_path", nargs="?", default=None,
                            help="portfolio.xlsx local. Si se omite, se lee la planilla de "
                                 "Google Drive (PORTFOLIO_SHEET_ID).")
        parser.add_argument("--sheet-id", default=None,
                            help="ID de la planilla de Google Drive; pisa PORTFOLIO_SHEET_ID.")
        parser.add_argument("--out-html", default="Portfolio Dashboard.html")
        parser.add_argument("--out-xlsx", default=None,
                            help="Si se pasa, ademas genera un xlsx con la misma info (opcional).")
        parser.add_argument("--no-watchlist", action="store_true",
                            help="No calcula la watchlist. Es la parte mas lenta de la corrida "
                                 "(dos consultas por instrumento vigilado) y no afecta al "
                                 "portfolio: la solapa queda vacia.")
        parser.add_argument("--no-annual", action="store_true",
                            help="No calcula la solapa Anual. Pide el precio de cierre de cada "
                                 "anio de cada instrumento (muchas consultas a PPI/Yahoo) y no "
                                 "afecta al resto del portfolio: la solapa queda vacia.")
        return parser.parse_args(argv)


def main(argv=None):
    return DashboardCli().run(argv)
