# -*- coding: utf-8 -*-
import datetime as dt

import pytest

from doubles import FakePpi, FakeYahoo, write_workbook
from portfolio.marketdata.historical_prices import HistoricalPrices
from portfolio.marketdata.price_resolver import PriceResolver
from portfolio.portfolio.annual_summary import AnnualSummary
from portfolio.portfolio.snapshot_builder import SnapshotBuilder
from portfolio.workbook.portfolio_workbook import PortfolioWorkbook

INSTRUMENTS = [("AAA", "Alpha Corp", "ACCIONES-USA", "A-48HS", 1, "Technology", "USD", None, "Stock")]
TODAY = dt.date(2026, 8, 1)


def rows(path, fx, yahoo_closes, ppi_closes=None):
    ppi = FakePpi(prices={"AAA": (5.0, None)}, closes=ppi_closes or {})
    yahoo = FakeYahoo(closes=yahoo_closes)
    prices = PriceResolver(ppi, yahoo, fx)
    snapshot = SnapshotBuilder(PortfolioWorkbook(path), prices, fx).build()
    return {r["year"]: r for r in
            AnnualSummary(snapshot.reports_by_year, HistoricalPrices(ppi, yahoo), today=TODAY).rows()}


@pytest.fixture
def two_years(tmp_path):
    return write_workbook(tmp_path / "p.xlsx", instruments=INSTRUMENTS, sheets={"tx-usd": [
        ("AAA", "BUY", 10, dt.datetime(2025, 3, 1), 1.0, 10.0, 10000.0),
        ("AAA", "BUY", 20, dt.datetime(2026, 3, 1), 2.0, 40.0, 40000.0),
        ("AAA", "SELL", 5, dt.datetime(2026, 6, 1), 3.0, 15.0, 15000.0),
    ]})


MEP_2025 = {("AL30", 2025): (1100.0, None), ("AL30D", 2025): (1.0, None)}


def test_there_is_one_row_per_year_most_recent_first(two_years, fx):
    assert list(rows(two_years, fx, {})) == ["2026", "2025"]


def test_invested_is_shown_gross_and_net_of_the_sales_of_that_year(two_years, fx):
    year = rows(two_years, fx, {})["2026"]
    assert year["invested_gross_usd"] == 40.0
    assert year["invested_net_usd"] == pytest.approx(40.0 - 5 * 50 / 30)   # 5 sold at the real avg cost: (10+40)/30 units


def test_a_past_year_is_valued_at_its_closing_price(two_years, fx):
    year = rows(two_years, fx, {("AAA", 2025): (1.5, None)})["2025"]
    assert year["close_value_usd"] == pytest.approx(15.0)
    assert year["year_pct_usd"] == pytest.approx(50.0)


def test_the_other_currency_uses_the_exchange_rate_of_that_day(two_years, fx):
    year = rows(two_years, fx, {("AAA", 2025): (1.5, None)}, MEP_2025)["2025"]
    assert year["close_value_ars"] == pytest.approx(1.5 * 1100 * 10)


def test_without_the_exchange_rate_of_that_day_the_other_currency_is_empty(two_years, fx):
    year = rows(two_years, fx, {("AAA", 2025): (1.5, None)})["2025"]
    assert year["close_value_ars"] is None
    assert year["year_pct_ars"] is None


def test_a_year_without_historical_price_is_left_empty_and_flagged(two_years, fx):
    year = rows(two_years, fx, {})["2025"]
    assert year["close_value_usd"] is None
    assert year["close_missing"] == 1


def test_the_gain_to_date_values_the_position_at_todays_price(two_years, fx):
    year = rows(two_years, fx, {})["2025"]
    assert year["gain_usd"] == pytest.approx(10 * 5.0 - 10.0)
    assert year["gain_pct_usd"] == pytest.approx(400.0)


def test_the_current_year_closes_at_todays_value(two_years, fx):
    year = rows(two_years, fx, {})["2026"]
    assert year["close_value_usd"] == pytest.approx(15 * 5.0)


def test_each_year_carries_its_instruments_and_they_add_up_to_the_year(two_years, fx):
    year = rows(two_years, fx, {("AAA", 2025): (1.5, None)})["2025"]
    (detail,) = year["detail"]
    assert detail["key"] == "AAA" and detail["market"] == "usd"
    assert detail["units_bought"] == 10
    assert detail["close_price_usd"] == pytest.approx(1.5)
    assert detail["close_value_usd"] == pytest.approx(year["close_value_usd"])
    assert detail["invested_gross_usd"] == pytest.approx(year["invested_gross_usd"])
