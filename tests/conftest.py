# -*- coding: utf-8 -*-
"""Fixtures built on top of the doubles in doubles.py."""

import datetime as dt

import pytest

from doubles import FakePpi, FakeYahoo, make_holding, write_workbook
from portfolio_dashboard.marketdata.fx_rate import FxRate
from portfolio_dashboard.settings import Settings


@pytest.fixture
def fake_ppi():
    return FakePpi()


@pytest.fixture
def fake_yahoo():
    return FakeYahoo()


@pytest.fixture
def fx():
    """1 USD = 1000 ARS -- round numbers keep the assertions readable."""
    return FxRate(1000.0, "test")


@pytest.fixture
def no_fx():
    return FxRate.unavailable("sin cotizacion")


@pytest.fixture
def settings():
    """No pausing and a single attempt, so tests never sleep."""
    return Settings(public_key="pub", private_key="priv", pause=0, retries=1, backoff=0)


@pytest.fixture
def holding():
    return make_holding()


@pytest.fixture
def workbook_path(tmp_path):
    """A minimal but complete spreadsheet: one USD position with a sale."""
    return write_workbook(
        tmp_path / "portfolio.xlsx",
        instruments=[("AAA", "Alpha Corp", "ACCIONES-USA", "A-48HS", 1,
                      "Technology", "USD", None, "Stock")],
        manual_fx=1000.0,
        sheets={"tx-usd": [
            ("AAA", "BUY", 10, dt.datetime(2025, 3, 15), 10.0, 100.0, 100000.0),
            ("AAA", "SELL", 4, dt.datetime(2026, 4, 20), 15.0, 60.0, 60000.0),
        ]},
    )
