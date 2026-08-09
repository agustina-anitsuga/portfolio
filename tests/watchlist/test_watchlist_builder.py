# -*- coding: utf-8 -*-
from portfolio.watchlist.fundamentals import Fundamentals
from portfolio.watchlist.watchlist_builder import WatchlistBuilder


class FakeSource:
    def __init__(self, known=None):
        self.known = known or {}
        self.calls = []

    def of(self, ticker):
        self.calls.append(ticker)
        return self.known.get(ticker, Fundamentals.empty())


def test_one_row_per_ticker_in_the_order_of_the_sheet():
    source = FakeSource()
    rows = WatchlistBuilder(source).rows(["AAPL", "GOOGL", "SPY"])
    assert [row["ticker"] for row in rows] == ["AAPL", "GOOGL", "SPY"]


def test_each_instrument_is_asked_once():
    source = FakeSource()
    WatchlistBuilder(source).rows(["AAPL", "GOOGL"])
    assert source.calls == ["AAPL", "GOOGL"]


def test_the_figures_reach_the_row():
    source = FakeSource({"AAPL": Fundamentals(price=313.33, low52=219.25, high52=344.57)})
    row = WatchlistBuilder(source).rows(["AAPL"])[0]
    assert row["price"] == 313.33
    assert row["signal_price"] == "Hold"


def test_an_empty_watchlist_produces_no_rows():
    assert WatchlistBuilder(FakeSource()).rows([]) == []
