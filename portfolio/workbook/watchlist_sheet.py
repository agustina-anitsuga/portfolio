# -*- coding: utf-8 -*-
"""Hoja "watchlist"."""

SHEET = "watchlist"


class WatchlistSheet:
    """Los tickers que se siguen sin tenerlos en cartera.

    Solo se lee la primera columna; el resto queda libre para tus notas. La
    hoja es opcional: sin ella simplemente no hay watchlist.
    """

    def __init__(self, workbook):
        self._workbook = workbook

    def tickers(self):
        if SHEET not in self._workbook.sheetnames:
            return []
        rows = self._workbook[SHEET].iter_rows(min_row=2, values_only=True)
        seen = []
        for row in rows:
            ticker = str(row[0]).strip() if row and row[0] else None
            if ticker and ticker not in seen:
                seen.append(ticker)
        return seen
