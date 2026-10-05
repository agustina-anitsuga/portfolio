# -*- coding: utf-8 -*-
import datetime as dt

import pytest

from doubles import CEDEARS_MARKET, USD_MARKET, FakePpi, FakeYahoo, make_instrument
from portfolio.market import ARS, USD
from portfolio.marketdata.historical_prices import HistoricalPrices

DAY = dt.date(2025, 12, 31)
MEP = {("AL30", 2025): (1500.0, None), ("AL30D", 2025): (1.0, None)}


def history(ppi_closes=None, yahoo_closes=None):
    return HistoricalPrices(FakePpi(closes={**MEP, **(ppi_closes or {})}),
                            FakeYahoo(closes=yahoo_closes or {}))


def test_a_cedear_is_priced_from_the_underlying_and_the_ratio_of_the_sheet():
    # PPI's own history says 52250: adjusted for a ratio change, so it must be ignored
    h = history({("SPY", 2025): (52250.0, None)}, {("SPY", 2025): (600.0, None)})
    spy = make_instrument("SPY", ratio=60)
    price = h.close(CEDEARS_MARKET, spy, DAY)
    assert price == pytest.approx(600.0 / 60 * 1500.0)
    assert h.convert(price, ARS, USD, DAY) == pytest.approx(10.0)


def test_a_cedear_falls_back_to_ppi_when_the_underlying_is_not_available():
    h = history({("SPY", 2025): (17000.0, None)})
    assert h.close(CEDEARS_MARKET, make_instrument("SPY", ratio=60), DAY) == 17000.0


def test_a_cedear_without_ratio_falls_back_to_ppi():
    h = history({("SPY", 2025): (17000.0, None)}, {("SPY", 2025): (600.0, None)})
    assert h.close(CEDEARS_MARKET, make_instrument("SPY", ratio=None), DAY) == 17000.0


def test_a_us_stock_keeps_using_ppi_then_yahoo():
    h = history(yahoo_closes={("AAA", 2025): (12.0, None)})
    assert h.close(USD_MARKET, make_instrument("AAA"), DAY) == 12.0
