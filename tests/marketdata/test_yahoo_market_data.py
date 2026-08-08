# -*- coding: utf-8 -*-
import pytest

from portfolio_dashboard.marketdata import yahoo_market_data as module
from portfolio_dashboard.marketdata.yahoo_market_data import NOT_INSTALLED, YahooMarketData


class FakeHistory:
    def __init__(self, closes):
        self._closes = closes
        self.empty = not closes

    def __getitem__(self, column):
        return self

    def dropna(self):
        return self

    def __len__(self):
        return len(self._closes)

    @property
    def iloc(self):
        return self._closes


class FakeTicker:
    def __init__(self, fast_info=None, info=None, history=None, raises=()):
        self._fast_info = fast_info if fast_info is not None else {}
        self._info = info if info is not None else {}
        self._history = history
        self._raises = raises

    @property
    def fast_info(self):
        if "fast_info" in self._raises:
            raise RuntimeError("fast_info roto")
        return self._fast_info

    @property
    def info(self):
        if "info" in self._raises:
            raise RuntimeError("info roto")
        return self._info

    def history(self, period):
        if "history" in self._raises:
            raise RuntimeError("history roto")
        return FakeHistory(self._history or [])


@pytest.fixture
def yahoo(monkeypatch):
    monkeypatch.setattr(module, "HAVE_YFINANCE", True)

    def install(ticker):
        monkeypatch.setattr(module, "yf", type("yf", (), {"Ticker": staticmethod(lambda t: ticker)}),
                            raising=False)
        return YahooMarketData()
    return install


def test_price_comes_from_fast_info_when_available(yahoo):
    assert yahoo(FakeTicker(fast_info={"last_price": 42.5})).price("AAA") == (42.5, None)


def test_alternative_fast_info_keys_are_tried(yahoo):
    assert yahoo(FakeTicker(fast_info={"regularMarketPrice": 7.0})).price("AAA") == (7.0, None)


def test_falls_back_to_info_when_fast_info_has_nothing(yahoo):
    ticker = FakeTicker(fast_info={}, info={"previousClose": 12.0})
    assert yahoo(ticker).price("AAA") == (12.0, None)


def test_falls_back_to_the_history_when_info_has_nothing(yahoo):
    ticker = FakeTicker(fast_info={}, info={}, history=[10.0, 11.0, 13.5])
    assert yahoo(ticker).price("AAA") == (13.5, None)


def test_a_broken_probe_does_not_stop_the_next_one(yahoo):
    ticker = FakeTicker(info={"currentPrice": 5.0}, raises=("fast_info",))
    assert yahoo(ticker).price("AAA") == (5.0, None)


def test_when_every_probe_fails_the_reason_names_the_ticker(yahoo):
    price, reason = yahoo(FakeTicker()).price("ZZZ")
    assert price is None
    assert "ZZZ" in reason


def test_the_last_error_is_included_in_the_reason(yahoo):
    ticker = FakeTicker(raises=("fast_info", "info", "history"))
    price, reason = yahoo(ticker).price("ZZZ")
    assert price is None
    assert "history roto" in reason


def test_without_yfinance_it_says_so_instead_of_crashing(monkeypatch):
    monkeypatch.setattr(module, "HAVE_YFINANCE", False)
    assert YahooMarketData().price("AAA") == (None, NOT_INSTALLED)


def test_a_zero_price_is_not_accepted(yahoo):
    """A zero would silently value the whole position at nothing."""
    ticker = FakeTicker(fast_info={"last_price": 0}, info={"regularMarketPrice": 3.0})
    assert yahoo(ticker).price("AAA") == (3.0, None)
