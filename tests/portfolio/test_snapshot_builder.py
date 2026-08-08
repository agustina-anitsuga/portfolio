# -*- coding: utf-8 -*-
import datetime as dt

import pytest

from doubles import FakePpi, FakeYahoo, write_workbook
from portfolio_dashboard.market import Market
from portfolio_dashboard.marketdata.price_resolver import PriceResolver
from portfolio_dashboard.portfolio.snapshot_builder import SnapshotBuilder
from portfolio_dashboard.workbook.portfolio_workbook import PortfolioWorkbook

INSTRUMENTS = [("AAA", "Alpha Corp", "ACCIONES-USA", "A-48HS", 1, "Technology", "USD", None, "Stock")]


def build(path, fx, ppi=None):
    workbook = PortfolioWorkbook(path)
    prices = PriceResolver(ppi or FakePpi(prices={"AAA": (5.0, None)}), FakeYahoo(), fx)
    return SnapshotBuilder(workbook, prices, fx).build()


@pytest.fixture
def two_years(tmp_path):
    return write_workbook(tmp_path / "p.xlsx", instruments=INSTRUMENTS, sheets={"tx-usd": [
        ("AAA", "BUY", 10, dt.datetime(2025, 3, 1), 1.0, 10.0, 10000.0),
        ("AAA", "BUY", 20, dt.datetime(2026, 3, 1), 2.0, 40.0, 40000.0),
        ("AAA", "SELL", 5, dt.datetime(2026, 6, 1), 3.0, 15.0, 15000.0),
    ]})


def test_the_snapshot_has_a_report_for_every_market(two_years, fx):
    assert set(build(two_years, fx).reports) == set(Market.keys())


def test_the_full_report_covers_the_whole_history(two_years, fx):
    row = build(two_years, fx).reports["usd"].rows[0]
    assert row["units"] == 25          # 10 + 20 - 5
    assert row["units_sold"] == 5


def test_there_is_one_report_set_per_year_with_purchases(two_years, fx):
    assert build(two_years, fx).years == ["2026", "2025"]


def test_each_year_reports_only_its_own_trades(two_years, fx):
    snapshot = build(two_years, fx)
    assert snapshot.reports_by_year["2025"]["usd"].rows[0]["units"] == 10
    assert snapshot.reports_by_year["2026"]["usd"].rows[0]["units"] == 15   # 20 bought - 5 sold


def test_the_yearly_slices_add_up_to_the_full_portfolio(two_years, fx):
    snapshot = build(two_years, fx)
    per_year = sum(snapshot.reports_by_year[year]["usd"].rows[0]["invested_usd"]
                   for year in snapshot.years)
    assert per_year == pytest.approx(snapshot.reports["usd"].rows[0]["invested_usd"])


def test_a_year_without_purchases_is_not_offered(tmp_path, fx):
    path = write_workbook(tmp_path / "p.xlsx", instruments=INSTRUMENTS, sheets={"tx-usd": [
        ("AAA", "BUY", 10, dt.datetime(2025, 3, 1), 1.0, 10.0, 10000.0),
        ("AAA", "SELL", 5, dt.datetime(2026, 6, 1), 3.0, 15.0, 15000.0),
    ]})
    assert build(path, fx).years == ["2025"]


def test_the_transactions_are_included(two_years, fx):
    assert len(build(two_years, fx).transactions) == 3


def test_the_exchange_rate_is_carried_along(two_years, fx):
    assert build(two_years, fx).fx is fx


def test_an_empty_spreadsheet_produces_an_empty_snapshot(tmp_path, fx):
    path = write_workbook(tmp_path / "p.xlsx")
    snapshot = build(path, fx)
    assert snapshot.position_count == 0
    assert snapshot.years == []
    assert snapshot.transactions == []


def test_the_market_is_only_asked_once_per_ticker(two_years, fx):
    """Two yearly slices plus the full report reuse the same quote."""
    ppi = FakePpi(prices={"AAA": (5.0, None)})
    build(two_years, fx, ppi=ppi)
    assert len(ppi.price_calls) == 1
