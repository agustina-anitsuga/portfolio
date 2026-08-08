# -*- coding: utf-8 -*-
import pytest

from doubles import FakePpi, FakeYahoo, make_position, write_workbook
from portfolio.market import Market
from portfolio.marketdata.price_resolver import PriceResolver
from portfolio.portfolio.position import Position
from portfolio.portfolio.report_builder import ReportBuilder
from portfolio.workbook.portfolio_workbook import PortfolioWorkbook


def builder(workbook_path, fx, ppi=None, yahoo=None):
    workbook = PortfolioWorkbook(workbook_path)
    prices = PriceResolver(ppi or FakePpi(), yahoo or FakeYahoo(), fx)
    return ReportBuilder(workbook, prices), workbook


def empty_positions():
    return {key: {} for key in Market.keys()}


def test_builds_one_report_per_market(workbook_path, fx):
    reports, _ = builder(workbook_path, fx)
    assert list(reports.build(empty_positions())) == Market.keys()


def test_positions_become_holdings(workbook_path, fx):
    reports, _ = builder(workbook_path, fx, ppi=FakePpi(prices={"AAA": (5.0, None)}))
    positions = empty_positions()
    positions["usd"] = {"AAA": make_position(units=10.0, cost_ars=1000.0, cost_usd=10.0)}
    rows = reports.build(positions)["usd"].rows
    assert [row["key"] for row in rows] == ["AAA"]
    assert rows[0]["price_usd"] == 5.0


def test_closed_positions_with_no_sales_are_dropped(workbook_path, fx):
    """Nothing held and nothing sold means there is nothing to report."""
    reports, _ = builder(workbook_path, fx)
    positions = empty_positions()
    positions["usd"] = {"AAA": Position()}
    assert reports.build(positions)["usd"].rows == []


def test_a_fully_sold_position_is_still_reported(workbook_path, fx):
    reports, _ = builder(workbook_path, fx)
    position = Position()
    position.buy(5, {"ars": 500.0, "usd": 5.0}, "2025", in_scope=True)
    position.sell(5, {"ars": 900.0, "usd": 9.0}, in_scope=True)
    positions = empty_positions()
    positions["usd"] = {"AAA": position}
    rows = reports.build(positions)["usd"].rows
    assert rows[0]["units_sold"] == 5
    assert rows[0]["realized_abs_ars"] == pytest.approx(400.0)


def test_the_instrument_metadata_comes_from_the_spreadsheet(workbook_path, fx):
    reports, _ = builder(workbook_path, fx)
    positions = empty_positions()
    positions["usd"] = {"AAA": make_position()}
    row = reports.build(positions)["usd"].rows[0]
    assert row["name"] == "Alpha Corp"
    assert row["sector"] == "Technology"


def test_a_ticker_missing_from_the_instruments_sheet_still_reports(workbook_path, fx):
    reports, _ = builder(workbook_path, fx)
    positions = empty_positions()
    positions["usd"] = {"ZZZ": make_position()}
    row = reports.build(positions)["usd"].rows[0]
    assert row["key"] == "ZZZ"
    assert row["name"] == "ZZZ"


def test_prices_are_requested_once_per_ticker_across_years(tmp_path, fx):
    """Building the per-year reports must not cost extra market calls."""
    path = write_workbook(tmp_path / "p.xlsx",
                          instruments=[("AAA", "Alpha", "ACCIONES-USA", "A-48HS", 1,
                                        "Tech", "USD", None, "Stock")])
    ppi = FakePpi(prices={"AAA": (5.0, None)})
    reports, _ = builder(path, fx, ppi=ppi)
    positions = empty_positions()
    positions["usd"] = {"AAA": make_position()}
    reports.build(positions)
    reports.build(positions)
    assert len(ppi.price_calls) == 1
    assert len(ppi.trend_calls) == 1
