# -*- coding: utf-8 -*-
import datetime as dt

import pytest

from doubles import FakeSession
from portfolio.marketdata.ppi_market_data import (MISSING_INSTRUMENT_META, TREND_DAYS,
                                                  PpiMarketData)
from portfolio.marketdata.ppi_session import NO_CLIENT


class FakeMarketData:
    def __init__(self, current=None, history=None):
        self._current = current if current is not None else {}
        self._history = history or []
        self.current_calls = []
        self.search_calls = []

    def current(self, ticker, ppi_type, settlement):
        self.current_calls.append((ticker, ppi_type, settlement))
        answer = self._current
        return answer(ticker) if callable(answer) else answer

    def search(self, ticker, ppi_type, settlement, date_from, date_to):
        self.search_calls.append((ticker, date_from, date_to))
        return self._history


class FakeClient:
    def __init__(self, marketdata):
        self.marketdata = marketdata


def market_data(current=None, history=None, available=True):
    feed = FakeMarketData(current, history)
    return PpiMarketData(FakeSession(FakeClient(feed), available=available)), feed


def test_price_returns_the_quoted_value():
    ppi, _ = market_data(current={"price": 123.5})
    assert ppi.price("AAA", "ACCIONES-USA", "A-48HS") == (123.5, None)


def test_bonds_are_converted_from_per_100_nominal_to_per_unit():
    """PPI quotes bonds per 100 of nominal value; without this the position is
    worth ~100x what it should."""
    ppi, _ = market_data(current={"price": 1400.0})
    assert ppi.price("AO28", "BONOS", "INMEDIATA") == (14.0, None)


def test_no_client_wins_over_missing_metadata():
    """Both are true at once when there are no credentials; the missing client
    is the actionable one, so it is the reason reported."""
    ppi, feed = market_data(available=False)
    assert ppi.price("AAA", "", "") == (None, NO_CLIENT)
    assert feed.current_calls == []


def test_missing_ppi_type_or_settlement_is_reported_without_calling_ppi():
    ppi, feed = market_data(current={"price": 1.0})
    assert ppi.price("AAA", "", "A-48HS") == (None, MISSING_INSTRUMENT_META)
    assert ppi.price("AAA", "ACCIONES-USA", None) == (None, MISSING_INSTRUMENT_META)
    assert feed.current_calls == []


def test_a_response_without_a_price_explains_which_fields_came_back():
    ppi, _ = market_data(current={"ticker": "AAA", "volume": 10})
    price, reason = ppi.price("AAA", "ACCIONES-USA", "A-48HS")
    assert price is None
    assert "sin precio" in reason and "ticker" in reason


def test_a_response_that_is_not_a_dict_is_reported_with_its_type():
    ppi, _ = market_data(current="<html>error</html>")
    price, reason = ppi.price("AAA", "ACCIONES-USA", "A-48HS")
    assert price is None
    assert "str en vez de un dict" in reason


def test_a_zero_price_counts_as_no_price():
    ppi, _ = market_data(current={"price": 0})
    assert ppi.price("AAA", "ACCIONES-USA", "A-48HS")[0] is None


def test_trend_builds_the_series_from_the_history():
    ppi, _ = market_data(history=[{"price": 100.0}, {"price": 110.0}, {"price": 120.0}])
    trend = ppi.trend("AAA", "ACCIONES-USA", "A-48HS")
    assert trend.series == [100.0, 110.0, 120.0]
    assert trend.pct == pytest.approx(20.0)


def test_trend_asks_for_thirty_days_back():
    ppi, feed = market_data(history=[{"price": 1.0}, {"price": 2.0}])
    ppi.trend("AAA", "ACCIONES-USA", "A-48HS")
    _, date_from, date_to = feed.search_calls[0]
    assert (date_to - date_from) == dt.timedelta(days=TREND_DAYS)


def test_trend_is_empty_when_the_history_is_too_short():
    ppi, _ = market_data(history=[{"price": 100.0}])
    trend = ppi.trend("AAA", "ACCIONES-USA", "A-48HS")
    assert (trend.pct, trend.series) == (None, [])


def test_trend_is_empty_without_instrument_metadata():
    ppi, feed = market_data(history=[{"price": 1.0}, {"price": 2.0}])
    trend = ppi.trend("AAA", "", "")
    assert (trend.pct, trend.series) == (None, [])
    assert feed.search_calls == []


def test_trend_is_empty_when_the_series_starts_at_zero():
    ppi, _ = market_data(history=[{"price": 0}, {"price": 10.0}])
    trend = ppi.trend("AAA", "ACCIONES-USA", "A-48HS")
    assert (trend.pct, trend.series) == (None, [])


def test_mep_rate_divides_the_two_al30_prices():
    ppi, _ = market_data(current=lambda ticker: {"price": 145000.0 if ticker == "AL30" else 100.0})
    rate, reason = ppi.mep_rate()
    assert rate == pytest.approx(1450.0)
    assert reason is None


def test_mep_rate_is_not_affected_by_the_bond_per_100_rule():
    """Both legs are BONOS, so the factor cancels out in the ratio."""
    ppi, _ = market_data(current=lambda ticker: {"price": 145000.0 if ticker == "AL30" else 100.0})
    assert ppi.mep_rate()[0] == pytest.approx(1450.0)


def test_mep_rate_names_the_leg_that_did_not_quote():
    ppi, _ = market_data(current=lambda ticker: {"price": 1.0} if ticker == "AL30" else {})
    rate, reason = ppi.mep_rate()
    assert rate is None
    assert "AL30D" in reason and "horario de mercado" in reason


def test_mep_rate_names_both_legs_when_neither_quotes():
    ppi, _ = market_data(current={})
    _, reason = ppi.mep_rate()
    assert "AL30 y AL30D" in reason
