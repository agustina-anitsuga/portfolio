# -*- coding: utf-8 -*-
import datetime as dt

import pytest

from doubles import FakePpi, FakeYahoo, write_workbook
from portfolio.marketdata.historical_prices import HistoricalPrices
from portfolio.marketdata.price_resolver import PriceResolver
from portfolio.portfolio.annual_summary import AnnualSummary
from portfolio.workbook.portfolio_workbook import PortfolioWorkbook

INSTRUMENTS = [("AAA", "Alpha Corp", "ACCIONES-USA", "A-48HS", 1, "Technology", "USD", None, "Stock")]
TODAY = dt.date(2026, 8, 1)


def rows(path, fx, yahoo_closes, ppi_closes=None):
    ppi = FakePpi(prices={"AAA": (5.0, None)}, closes=ppi_closes or {})
    yahoo = FakeYahoo(closes=yahoo_closes)
    prices = PriceResolver(ppi, yahoo, fx)
    summary = AnnualSummary(PortfolioWorkbook(path), prices, fx, HistoricalPrices(ppi, yahoo), today=TODAY)
    return {r["year"]: r for r in summary.rows()}


@pytest.fixture
def two_years(tmp_path):
    return write_workbook(tmp_path / "p.xlsx", instruments=INSTRUMENTS, sheets={"tx-usd": [
        ("AAA", "BUY", 10, dt.datetime(2025, 3, 1), 1.0, 10.0, 10000.0),
        ("AAA", "BUY", 20, dt.datetime(2026, 3, 1), 2.0, 40.0, 40000.0),
        ("AAA", "SELL", 5, dt.datetime(2026, 6, 1), 3.0, 15.0, 15000.0),
    ]})


MEP_2025 = {("AL30", 2025): (1100.0, None), ("AL30D", 2025): (1.0, None)}
CLOSE_2025 = {("AAA", 2025): (1.5, None)}
AVG_COST_2026 = 50 / 30          # (10 + 40) / 30 units


def test_there_is_one_row_per_calendar_year_most_recent_first(two_years, fx):
    assert list(rows(two_years, fx, {})) == ["2026", "2025"]


def test_years_without_trades_are_still_shown_up_to_today(tmp_path, fx):
    path = write_workbook(tmp_path / "p.xlsx", instruments=INSTRUMENTS, sheets={"tx-usd": [
        ("AAA", "BUY", 10, dt.datetime(2024, 3, 1), 1.0, 10.0, 10000.0)]})
    assert list(rows(path, fx, {})) == ["2026", "2025", "2024"]


def test_contribution_is_what_was_bought_and_sold_that_year(two_years, fx):
    year = rows(two_years, fx, {})["2026"]
    assert year["bought_usd"] == 40.0
    assert year["sold_usd"] == 15.0
    assert year["net_contribution_usd"] == 25.0


def test_realized_is_the_sales_of_that_year_against_the_real_average_cost(two_years, fx):
    year = rows(two_years, fx, {})["2026"]
    assert year["realized_usd"] == pytest.approx(15.0 - 5 * AVG_COST_2026)
    assert rows(two_years, fx, {})["2025"]["realized_usd"] == 0.0


def test_unrealized_of_a_past_year_is_the_one_at_its_close(two_years, fx):
    year = rows(two_years, fx, CLOSE_2025)["2025"]
    assert year["invested_usd"] == pytest.approx(10.0)
    assert year["close_value_usd"] == pytest.approx(15.0)
    assert year["unrealized_usd"] == pytest.approx(5.0)


def test_the_current_year_is_valued_at_todays_price_with_everything_held(two_years, fx):
    year = rows(two_years, fx, CLOSE_2025)["2026"]
    assert year["invested_usd"] == pytest.approx(25 * AVG_COST_2026)
    assert year["close_value_usd"] == pytest.approx(25 * 5.0)
    assert year["unrealized_usd"] == pytest.approx(25 * 5.0 - 25 * AVG_COST_2026)


def test_the_base_of_a_year_is_the_value_at_the_close_of_the_previous_one(two_years, fx):
    years = rows(two_years, fx, CLOSE_2025)
    assert years["2025"]["base_value_usd"] == 0.0
    assert years["2026"]["base_value_usd"] == pytest.approx(years["2025"]["close_value_usd"])


def test_the_result_of_the_year_is_unrealized_change_plus_realized(two_years, fx):
    years = rows(two_years, fx, CLOSE_2025)
    y25, y26 = years["2025"], years["2026"]
    assert y25["result_usd"] == pytest.approx(5.0)
    assert y26["result_usd"] == pytest.approx(
        y26["unrealized_usd"] - y25["unrealized_usd"] + y26["realized_usd"])
    assert y26["result_pct_usd"] == pytest.approx(y26["result_usd"] / (15.0 + 40.0) * 100)


def test_the_other_currency_uses_the_exchange_rate_of_that_day(two_years, fx):
    year = rows(two_years, fx, CLOSE_2025, MEP_2025)["2025"]
    assert year["close_value_ars"] == pytest.approx(1.5 * 1100 * 10)


def test_a_year_without_historical_price_is_left_empty_and_flagged(two_years, fx):
    years = rows(two_years, fx, {})
    assert years["2025"]["close_value_usd"] is None
    assert years["2025"]["unrealized_usd"] is None
    assert years["2025"]["close_missing"] == 1
    assert years["2026"]["base_value_usd"] is None
    assert years["2026"]["result_usd"] is None


def test_each_year_carries_its_instruments_and_they_add_up_to_the_year(two_years, fx):
    year = rows(two_years, fx, CLOSE_2025)["2025"]
    (detail,) = year["detail"]
    assert detail["key"] == "AAA" and detail["market"] == "usd"
    assert detail["units"] == 10
    assert detail["close_price_usd"] == pytest.approx(1.5)
    assert detail["close_value_usd"] == pytest.approx(year["close_value_usd"])
    assert detail["bought_usd"] == pytest.approx(year["bought_usd"])
