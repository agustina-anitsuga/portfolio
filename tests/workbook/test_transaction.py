# -*- coding: utf-8 -*-
import datetime as dt

import pytest

from doubles import CEDEARS_MARKET, MERVAL_MARKET, USD_MARKET, make_transaction
from portfolio_dashboard.market import ARS, USD
from portfolio_dashboard.workbook.transaction import Transaction


def test_reads_a_usd_row_taking_each_amount_from_its_column():
    row = ("AAA", "BUY", 10, dt.datetime(2025, 3, 15), 10.0, 100.0, 150000.0)
    tx = Transaction.from_row(USD_MARKET, row)
    assert (tx.ticker, tx.op, tx.units) == ("AAA", "BUY", 10.0)
    assert tx.amount_usd == 100.0     # column 5
    assert tx.amount_ars == 150000.0  # column 6


def test_reads_a_cedears_row_with_its_own_column_order():
    row = ("SPY", "BUY", 45, "30/09/2025", 770322.25, 666.18, 499.63, 60)
    tx = Transaction.from_row(CEDEARS_MARKET, row)
    assert tx.amount_ars == 770322.25  # column 4, @Local
    assert tx.amount_usd == 499.63     # column 6, @Origin


def test_reads_a_merval_row():
    row = ("YPFD", "BUY", 20, dt.datetime(2026, 6, 26), 70400, 140800.0, 95.25)
    tx = Transaction.from_row(MERVAL_MARKET, row)
    assert tx.amount_ars == 140800.0
    assert tx.amount_usd == 95.25


def test_an_optional_amount_that_was_never_recorded_stays_none():
    """That None is what later triggers the approximation at today's rate."""
    tx = Transaction.from_row(USD_MARKET, ("AAA", "BUY", 10, "2025-03-15", 10.0, 100.0))
    assert tx.amount_usd == 100.0
    assert tx.amount_ars is None


def test_amount_reads_the_requested_currency():
    tx = make_transaction(amount_ars=10000.0, amount_usd=10.0)
    assert tx.amount(ARS) == 10000.0
    assert tx.amount(USD) == 10.0


def test_price_is_the_amount_spread_over_the_units():
    tx = make_transaction(units=4.0, amount_ars=2000.0, amount_usd=2.0)
    assert tx.price(ARS) == 500.0
    assert tx.price(USD) == 0.5


def test_price_is_unknown_when_the_amount_was_not_recorded():
    assert make_transaction(amount_ars=None).price(ARS) is None


def test_price_of_a_zero_unit_row_does_not_divide_by_zero():
    assert make_transaction(units=0).price(USD) is None


def test_a_buy_is_recognised_by_its_operation():
    assert make_transaction(op="BUY").is_buy is True
    assert make_transaction(op="SELL").is_buy is False


def test_the_date_is_exposed_normalised_and_as_a_year():
    tx = make_transaction(date="30/09/2025")
    assert tx.iso_date == "2025-09-30"
    assert tx.year == "2025"


def test_as_dict_carries_what_the_transactions_tab_shows():
    tx = make_transaction(units=4.0, amount_ars=2000.0, amount_usd=2.0,
                          date=dt.datetime(2025, 9, 30))
    assert tx.as_dict() == {
        "ticker": "AAA", "market": "usd", "op": "BUY", "date": "2025-09-30",
        "year": "2025", "units": 4.0, "amount_ars": 2000.0, "amount_usd": 2.0,
        "price_ars": 500.0, "price_usd": 0.5,
    }


@pytest.mark.parametrize("units", [None, 0])
def test_rows_without_usable_units_still_produce_a_dict(units):
    """The Transacciones tab lists them; only the maths skips them."""
    assert make_transaction(units=units).as_dict()["units"] == units
