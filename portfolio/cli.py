# -*- coding: utf-8 -*-
"""Command line interface."""

import argparse

from .app import PortfolioApp
from .console_summary import ConsoleSummary
from .output.excel_report import ExcelReport
from .output.html_dashboard import HtmlDashboard


class DashboardCli:
    """python3 generate_dashboard.py portfolio.xlsx --out-html portfolio.html"""

    def __init__(self, app=None):
        self._app = app or PortfolioApp()

    def run(self, argv=None):
        args = self._parse_args(argv)
        snapshot = self._app.snapshot(args.xlsx_path, with_watchlist=not args.no_watchlist,
                                   with_annual=not args.no_annual)

        HtmlDashboard(snapshot).write(args.out_html)
        generated = [args.out_html]
        if args.out_xlsx:
            ExcelReport(snapshot).save(args.out_xlsx)
            generated.append(args.out_xlsx)

        ConsoleSummary(snapshot).print_report(generated)
        return 0

    @staticmethod
    def _parse_args(argv):
        parser = argparse.ArgumentParser()
        parser.add_argument("xlsx_path", help="portfolio.xlsx")
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
