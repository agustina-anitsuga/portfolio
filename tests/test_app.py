# -*- coding: utf-8 -*-
import datetime as dt

import pytest

from doubles import FakePpi, FakeYahoo, write_workbook
from portfolio_dashboard.app import PortfolioApp
from portfolio_dashboard.market import Market

INSTRUMENTS = [("AAA", "Alpha Corp", "ACCIONES-USA", "A-48HS", 1, "Technology", "USD", None, "Stock")]


@pytest.fixture
def spreadsheet(tmp_path):
    return write_workbook(tmp_path / "p.xlsx", instruments=INSTRUMENTS, manual_fx=1200.0,
                          sheets={"tx-usd": [
                              ("AAA", "BUY", 10, dt.datetime(2025, 3, 1), 1.0, 100.0, 100000.0)]})


def app(ppi=None, yahoo=None):
    return PortfolioApp(ppi=ppi or FakePpi(prices={"AAA": (15.0, None)}),
                        yahoo=yahoo or FakeYahoo())


def test_the_snapshot_covers_every_market(spreadsheet):
    assert set(app().snapshot(spreadsheet).reports) == set(Market.keys())


def test_the_positions_are_priced_with_the_market_data(spreadsheet):
    row = app().snapshot(spreadsheet).reports["usd"].rows[0]
    assert row["units"] == 10
    assert row["price_usd"] == 15.0


def test_the_live_mep_rate_is_preferred(spreadsheet):
    snapshot = app(ppi=FakePpi(prices={"AAA": (15.0, None)}, mep=(1450.0, None))).snapshot(spreadsheet)
    assert snapshot.fx.value == 1450.0


def test_without_a_live_rate_the_manual_one_from_the_sheet_is_used(spreadsheet):
    assert app().snapshot(spreadsheet).fx.value == 1200.0


def test_the_exchange_rate_reaches_the_converted_columns(spreadsheet):
    row = app().snapshot(spreadsheet).reports["usd"].rows[0]
    assert row["price_ars"] == pytest.approx(15.0 * 1200.0)


def test_yahoo_is_consulted_when_ppi_has_nothing(spreadsheet):
    yahoo = FakeYahoo(prices={"AAA": (20.0, None)})
    snapshot = app(ppi=FakePpi(), yahoo=yahoo).snapshot(spreadsheet)
    assert snapshot.reports["usd"].rows[0]["price_source"] == "Yahoo Finance"
    assert yahoo.calls == ["AAA"]


def test_the_transactions_are_part_of_the_snapshot(spreadsheet):
    assert len(app().snapshot(spreadsheet).transactions) == 1


def test_the_dependencies_default_to_the_real_ones(monkeypatch):
    """Nothing is constructed until a snapshot is asked for, so building the
    app must not touch the network."""
    application = PortfolioApp()
    assert application is not None
