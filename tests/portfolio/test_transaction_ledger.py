# -*- coding: utf-8 -*-
import datetime as dt

import pytest

from doubles import USD_MARKET, make_holding, make_instrument, make_quote, make_transaction
from portfolio.market import Market
from portfolio.portfolio.market_report import MarketReport
from portfolio.portfolio.transaction_ledger import TransactionLedger


def reports_with(key="AAA", price_ars=2000.0, price_usd=2.0, source="PPI (en vivo)"):
    holding = make_holding(instrument=make_instrument(key),
                           quote=make_quote(price_ars=price_ars, price_usd=price_usd,
                                            source=source))
    reports = {market_key: MarketReport(Market.get(market_key), []) for market_key in Market.keys()}
    reports["usd"] = MarketReport(USD_MARKET, [holding])
    return reports


def test_one_row_per_trade():
    ledger = TransactionLedger([make_transaction(), make_transaction(op="SELL")], reports_with())
    assert len(ledger.rows()) == 2


def test_rows_without_an_operation_are_left_out():
    ledger = TransactionLedger([make_transaction(op=None)], reports_with())
    assert ledger.rows() == []


def test_todays_quote_is_attached_to_each_trade():
    ledger = TransactionLedger([make_transaction(ticker="AAA")], reports_with(price_usd=3.0))
    row = ledger.rows()[0]
    assert row["current_price_usd"] == 3.0
    assert row["current_price_source"] == "PPI (en vivo)"


def test_a_ticker_with_no_report_shows_as_unpriced():
    ledger = TransactionLedger([make_transaction(ticker="ZZZ")], reports_with("AAA"))
    row = ledger.rows()[0]
    assert row["current_price_usd"] is None
    assert row["current_price_source"] == "no disponible"


def test_a_purchase_compares_its_price_against_todays_quote():
    transaction = make_transaction(op="BUY", units=10, amount_usd=10.0, amount_ars=10000.0)
    row = TransactionLedger([transaction], reports_with(price_usd=2.0, price_ars=2000.0)).rows()[0]
    assert row["price_usd"] == 1.0
    assert row["pl_pct_usd"] == pytest.approx(100.0)
    assert row["pl_pct_ars"] == pytest.approx(100.0)


def test_a_sale_has_no_pl():
    """The position is already closed: comparing the sale price against today's
    quote would be a what-if of having held, not a result."""
    transaction = make_transaction(op="SELL", units=10, amount_usd=10.0, amount_ars=10000.0)
    row = TransactionLedger([transaction], reports_with()).rows()[0]
    assert row["pl_pct_usd"] is None
    assert row["pl_pct_ars"] is None


def test_a_purchase_without_a_recorded_price_has_no_pl():
    transaction = make_transaction(amount_usd=None, amount_ars=None)
    row = TransactionLedger([transaction], reports_with()).rows()[0]
    assert row["pl_pct_usd"] is None


def test_a_purchase_of_an_unpriced_ticker_has_no_pl():
    row = TransactionLedger([make_transaction(ticker="ZZZ")], reports_with("AAA")).rows()[0]
    assert row["pl_pct_usd"] is None


def test_rows_come_back_newest_first():
    transactions = [
        make_transaction(date=dt.datetime(2025, 1, 1)),
        make_transaction(date=dt.datetime(2026, 5, 1)),
        make_transaction(date=dt.datetime(2025, 8, 1)),
    ]
    dates = [row["date"] for row in TransactionLedger(transactions, reports_with()).rows()]
    assert dates == ["2026-05-01", "2025-08-01", "2025-01-01"]


def test_trades_of_the_same_day_are_ordered_by_ticker():
    transactions = [
        make_transaction(ticker="AAA", date=dt.datetime(2025, 1, 1)),
        make_transaction(ticker="ZZZ", date=dt.datetime(2025, 1, 1)),
    ]
    tickers = [row["ticker"] for row in TransactionLedger(transactions, reports_with()).rows()]
    assert tickers == ["ZZZ", "AAA"]


def test_a_trade_without_a_date_does_not_break_the_ordering():
    transactions = [make_transaction(date=None), make_transaction(date=dt.datetime(2025, 1, 1))]
    rows = TransactionLedger(transactions, reports_with()).rows()
    assert rows[-1]["date"] == ""
