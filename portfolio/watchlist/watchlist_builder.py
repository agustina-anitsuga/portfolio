# -*- coding: utf-8 -*-
"""Arma la watchlist completa."""

from .watchlist_item import WatchlistItem
from .yahoo_fundamentals import YahooFundamentals


class WatchlistBuilder:
    """Una fila por ticker de la hoja "watchlist", en el orden en que estan
    cargados. Cada instrumento se consulta una sola vez."""

    def __init__(self, source=None):
        self._source = source or YahooFundamentals()

    def build(self, tickers):
        return [WatchlistItem(ticker, self._source.of(ticker)) for ticker in tickers]

    def rows(self, tickers):
        return [item.as_dict() for item in self.build(tickers)]
