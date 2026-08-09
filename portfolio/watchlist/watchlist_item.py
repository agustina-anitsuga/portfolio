# -*- coding: utf-8 -*-
"""Una fila de la watchlist."""

from .parameter_score import ParameterScore
from .target_price_signal import TargetPriceSignal


class WatchlistItem:
    """Un instrumento vigilado, con sus datos y las dos señales calculadas."""

    def __init__(self, ticker, fundamentals):
        self.ticker = ticker
        self.fundamentals = fundamentals
        self.target = TargetPriceSignal(fundamentals.price, fundamentals.low52, fundamentals.high52)
        self.parameters = ParameterScore(fundamentals)

    @property
    def priced(self):
        return self.fundamentals.price is not None

    def as_dict(self):
        row = {"ticker": self.ticker}
        row.update(self.fundamentals.as_dict())
        row.update({
            "target_buy": self.target.target_buy,
            "target_sell": self.target.target_sell,
            "signal_price": self.target.signal,
            "score": self.parameters.score,
            "signal_score": self.parameters.signal,
        })
        return row
