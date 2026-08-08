# -*- coding: utf-8 -*-
import datetime as dt

import pytest

from doubles import CEDEARS_MARKET, USD_MARKET, make_transaction
from portfolio.market import ARS, USD
from portfolio.portfolio.position_tracker import PositionTracker


def track(transactions, fx, scope_year=None):
    return PositionTracker(fx, scope_year).track(transactions)


def test_groups_the_trades_by_ticker(fx):
    positions = track([
        make_transaction(ticker="AAA", units=10),
        make_transaction(ticker="BBB", units=5),
        make_transaction(ticker="AAA", units=2),
    ], fx)
    assert sorted(positions) == ["AAA", "BBB"]
    assert positions["AAA"].units == 12


def test_a_buy_and_a_sell_are_applied_in_order(fx):
    positions = track([
        make_transaction(op="BUY", units=10, amount_ars=1000.0, amount_usd=10.0),
        make_transaction(op="SELL", units=4, amount_ars=800.0, amount_usd=8.0),
    ], fx)
    position = positions["AAA"]
    assert position.units == 6
    assert position.units_sold == 4


def test_rows_without_an_operation_are_ignored(fx):
    assert track([make_transaction(op=None)], fx) == {}


def test_rows_without_units_are_ignored(fx):
    assert track([make_transaction(units=None)], fx) == {}


def test_an_unknown_operation_creates_the_position_but_moves_nothing(fx):
    positions = track([make_transaction(op="DIVIDEND")], fx)
    assert positions["AAA"].units == 0.0


def test_a_recorded_amount_in_both_currencies_is_used_as_is(fx):
    """No approximation: those are the real historical numbers."""
    positions = track([make_transaction(amount_ars=17000.0, amount_usd=10.0)], fx)
    position = positions["AAA"]
    assert position.cost_basis[ARS] == 17000.0
    assert position.cost_basis[USD] == 10.0
    assert position.dual_real is True


def test_a_missing_other_currency_is_approximated_at_todays_rate(fx):
    positions = track([make_transaction(market=USD_MARKET, amount_usd=10.0, amount_ars=None)], fx)
    position = positions["AAA"]
    assert position.cost_basis[ARS] == 10000.0   # 10 USD x 1000
    assert position.dual_real is False


def test_the_approximation_runs_the_other_way_for_ars_native_markets(fx):
    positions = track([make_transaction(market=CEDEARS_MARKET, amount_ars=5000.0,
                                        amount_usd=None)], fx)
    position = positions["AAA"]
    assert position.cost_basis[USD] == pytest.approx(5.0)
    assert position.dual_real is False


def test_without_an_exchange_rate_the_other_currency_is_zero_and_flagged(no_fx):
    positions = track([make_transaction(amount_usd=10.0, amount_ars=None)], no_fx)
    position = positions["AAA"]
    assert position.cost_basis[ARS] == 0.0
    assert position.dual_real is False


def test_one_approximated_trade_flags_the_whole_position(fx):
    positions = track([
        make_transaction(amount_ars=17000.0, amount_usd=10.0),
        make_transaction(amount_ars=None, amount_usd=10.0),
    ], fx)
    assert positions["AAA"].dual_real is False


def test_a_missing_native_amount_counts_as_zero(fx):
    positions = track([make_transaction(amount_usd=None, amount_ars=None)], fx)
    assert positions["AAA"].cost_basis[USD] == 0.0


def test_scoping_to_a_year_reports_only_that_years_trades(fx):
    transactions = [
        make_transaction(units=10, date=dt.datetime(2025, 5, 1), amount_ars=1000.0, amount_usd=10.0),
        make_transaction(units=20, date=dt.datetime(2026, 5, 1), amount_ars=4000.0, amount_usd=40.0),
    ]
    scoped = track(transactions, fx, scope_year="2025")["AAA"]
    assert scoped.units == 10
    assert scoped.cost_basis[ARS] == 1000.0


def test_a_scoped_sale_still_carries_the_real_cost_of_older_units(fx):
    """Buy in 2025, sell in 2026: the 2026 slice must value that sale with the
    2025 cost, not with zero."""
    transactions = [
        make_transaction(op="BUY", units=10, date=dt.datetime(2025, 5, 1),
                         amount_ars=1000.0, amount_usd=10.0),
        make_transaction(op="SELL", units=4, date=dt.datetime(2026, 5, 1),
                         amount_ars=800.0, amount_usd=8.0),
    ]
    scoped = track(transactions, fx, scope_year="2026")["AAA"]
    assert scoped.cost_of_sales[ARS] == pytest.approx(400.0)
    assert scoped.income_from_sales[ARS] == 800.0


def test_the_yearly_slices_add_up_to_the_full_portfolio(fx):
    transactions = [
        make_transaction(op="BUY", units=10, date=dt.datetime(2025, 5, 1),
                         amount_ars=1000.0, amount_usd=10.0),
        make_transaction(op="BUY", units=10, date=dt.datetime(2026, 5, 1),
                         amount_ars=3000.0, amount_usd=30.0),
        make_transaction(op="SELL", units=5, date=dt.datetime(2026, 6, 1),
                         amount_ars=1500.0, amount_usd=15.0),
    ]
    full = track(transactions, fx)["AAA"]
    per_year = [track(transactions, fx, scope_year=y)["AAA"] for y in ("2025", "2026")]
    assert sum(p.units for p in per_year) == pytest.approx(full.units)
    assert sum(p.cost_basis[ARS] for p in per_year) == pytest.approx(full.cost_basis[ARS])
    assert sum(p.units_sold for p in per_year) == pytest.approx(full.units_sold)


def test_purchase_years_are_recorded_even_outside_the_scope(fx):
    """They feed the year filter, which must list every year with purchases."""
    transactions = [
        make_transaction(date=dt.datetime(2025, 5, 1)),
        make_transaction(date=dt.datetime(2026, 5, 1)),
    ]
    assert track(transactions, fx, scope_year="2026")["AAA"].buy_years == ["2025", "2026"]


def test_track_all_covers_every_market(fx, workbook_path):
    from portfolio.market import Market
    from portfolio.workbook.portfolio_workbook import PortfolioWorkbook
    positions = PositionTracker(fx).track_all(PortfolioWorkbook(workbook_path))
    assert set(positions) == set(Market.keys())
    assert positions["usd"]["AAA"].units == 6
