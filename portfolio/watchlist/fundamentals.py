# -*- coding: utf-8 -*-
"""The figures behind a watchlist row."""

from dataclasses import dataclass

BILLION = 1_000_000_000.0


@dataclass(frozen=True)
class Fundamentals:
    """Everything a watched instrument is judged by.

    Any field can be missing: ETFs have no EPS, no current ratio and no debt,
    and a brand new listing has no 52-week range. Missing stays None instead of
    zero, because a zero would sail through comparisons like "debt < 1" and
    hand out a good score for absent data.
    """

    name: str = None
    price: float = None
    change_pct: float = None
    market_cap: float = None      # in billions, like the original spreadsheet
    eps: float = None
    low52: float = None
    high52: float = None
    earnings: str = None
    pe: float = None
    current_ratio: float = None
    rsi: float = None
    debt_to_equity: float = None
    price_to_book: float = None

    @classmethod
    def empty(cls):
        return cls()

    def as_dict(self):
        return {
            "name": self.name, "price": self.price, "change_pct": self.change_pct,
            "market_cap": self.market_cap, "eps": self.eps,
            "low52": self.low52, "high52": self.high52, "earnings": self.earnings,
            "pe": self.pe, "current_ratio": self.current_ratio, "rsi": self.rsi,
            "debt_to_equity": self.debt_to_equity, "price_to_book": self.price_to_book,
        }
