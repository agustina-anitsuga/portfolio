# -*- coding: utf-8 -*-
import pytest

from portfolio.watchlist import yahoo_fundamentals as module
from portfolio.watchlist.yahoo_fundamentals import YahooFundamentals

INFO = {
    "longName": "Apple Inc", "currentPrice": 313.33, "regularMarketChangePercent": 0.294479,
    "marketCap": 4572794322944, "trailingEps": 8.71,
    "fiftyTwoWeekLow": 223.78, "fiftyTwoWeekHigh": 344.57,
    "trailingPE": 35.97359, "currentRatio": 1.003, "debtToEquity": 78.445,
    "priceToBook": 42.57201,
}


class FakeHistory:
    def __init__(self, closes):
        self._closes = closes
        self.empty = not closes

    def __getitem__(self, column):
        return self

    def dropna(self):
        return self

    def tolist(self):
        return self._closes


class FakeTicker:
    def __init__(self, info=INFO, closes=None, calendar=None, raises=()):
        self._info, self._closes = info, closes or []
        self._calendar = calendar
        self._raises = raises

    @property
    def info(self):
        if "info" in self._raises:
            raise RuntimeError("info roto")
        return self._info

    @property
    def calendar(self):
        if "calendar" in self._raises:
            raise RuntimeError("calendar roto")
        return self._calendar

    def history(self, period):
        if "history" in self._raises:
            raise RuntimeError("history roto")
        return FakeHistory(self._closes)


@pytest.fixture
def yahoo(monkeypatch):
    monkeypatch.setattr(module, "HAVE_YFINANCE", True)

    def install(ticker):
        monkeypatch.setattr(module, "yf",
                            type("yf", (), {"Ticker": staticmethod(lambda t: ticker)}),
                            raising=False)
        return YahooFundamentals()
    return install


def test_reads_the_quote_and_the_name(yahoo):
    data = yahoo(FakeTicker()).of("AAPL")
    assert data.name == "Apple Inc"
    assert data.price == 313.33
    assert data.change_pct == pytest.approx(0.294479)


def test_the_market_cap_is_expressed_in_billions(yahoo):
    """The column of the original spreadsheet is "Market Cap (B)"."""
    assert yahoo(FakeTicker()).of("AAPL").market_cap == pytest.approx(4572.794322944)


def test_debt_to_equity_is_turned_into_a_ratio(yahoo):
    """Yahoo answers a percentage (78.4) where Finviz answers 0.78, and the
    scoring rule ("less than 1") is written for the ratio."""
    assert yahoo(FakeTicker()).of("AAPL").debt_to_equity == pytest.approx(0.78445)


def test_the_rsi_is_computed_from_the_history(yahoo):
    data = yahoo(FakeTicker(closes=[100 + i for i in range(30)])).of("AAPL")
    assert data.rsi == 100.0


def test_without_enough_history_there_is_no_rsi(yahoo):
    assert yahoo(FakeTicker(closes=[100.0, 101.0])).of("AAPL").rsi is None


def test_the_next_earnings_date_is_kept_as_iso(yahoo):
    import datetime as dt
    ticker = FakeTicker(calendar={"Earnings Date": [dt.date(2026, 10, 29)]})
    assert yahoo(ticker).of("AAPL").earnings == "2026-10-29"


def test_an_etf_without_fundamentals_keeps_what_it_has(yahoo):
    """SPY has a price and a 52-week range but no EPS and no debt."""
    ticker = FakeTicker(info={"currentPrice": 773.26, "fiftyTwoWeekLow": 629.28,
                              "fiftyTwoWeekHigh": 776.85})
    data = yahoo(ticker).of("SPY")
    assert data.price == 773.26
    assert data.eps is None
    assert data.debt_to_equity is None


def test_a_broken_lookup_yields_an_empty_row(yahoo):
    assert yahoo(FakeTicker(raises=("info",))).of("ZZZZ").price is None


def test_a_broken_history_does_not_lose_the_rest(yahoo):
    data = yahoo(FakeTicker(raises=("history", "calendar"))).of("AAPL")
    assert data.price == 313.33
    assert data.rsi is None
    assert data.earnings is None


def test_without_yfinance_every_row_is_empty(monkeypatch):
    monkeypatch.setattr(module, "HAVE_YFINANCE", False)
    assert YahooFundamentals().of("AAPL").price is None
