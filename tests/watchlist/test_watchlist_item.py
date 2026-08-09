# -*- coding: utf-8 -*-
import pytest

from portfolio.watchlist.fundamentals import Fundamentals
from portfolio.watchlist.watchlist_item import WatchlistItem

AAPL = Fundamentals(name="Apple Inc", price=313.33, change_pct=0.29, market_cap=4572.79,
                    eps=8.72, low52=219.25, high52=344.57, earnings="2026-10-29",
                    pe=36.32, current_ratio=1.07, rsi=47.6, debt_to_equity=0.78,
                    price_to_book=42.57)


def test_the_row_carries_the_ticker_and_the_figures():
    row = WatchlistItem("AAPL", AAPL).as_dict()
    assert row["ticker"] == "AAPL"
    assert row["name"] == "Apple Inc"
    assert row["price"] == 313.33
    assert row["market_cap"] == pytest.approx(4572.79)


def test_the_row_carries_the_targets_and_both_signals():
    row = WatchlistItem("AAPL", AAPL).as_dict()
    assert row["target_buy"] == pytest.approx(281.91)
    assert row["target_sell"] == pytest.approx(325.772)
    assert row["signal_price"] == "Hold"
    assert row["score"] == 3   # solo current ratio, RSI y deuda pasan
    assert row["signal_score"] == "Hold"


def test_an_instrument_without_data_still_produces_a_row():
    """A ticker Yahoo does not know must not break the whole tab."""
    row = WatchlistItem("ZZZZ", Fundamentals.empty()).as_dict()
    assert row["ticker"] == "ZZZZ"
    assert row["price"] is None
    assert row["signal_price"] is None
    assert row["score"] is None


def test_priced_tells_whether_the_quote_arrived():
    assert WatchlistItem("AAPL", AAPL).priced is True
    assert WatchlistItem("ZZZZ", Fundamentals.empty()).priced is False


def test_the_row_has_one_key_per_column_of_the_tab():
    assert set(WatchlistItem("AAPL", AAPL).as_dict()) == {
        "ticker", "name", "price", "change_pct", "market_cap", "eps", "low52", "high52",
        "earnings", "pe", "current_ratio", "rsi", "debt_to_equity", "price_to_book",
        "target_buy", "target_sell", "signal_price", "score", "signal_score"}
