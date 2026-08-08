# -*- coding: utf-8 -*-
import pytest

from doubles import make_holding, make_position, make_quote
from portfolio_dashboard.market import ARS
from portfolio_dashboard.marketdata.quote import Quote
from portfolio_dashboard.portfolio.kpis import Kpis


def holding(cost_ars=1000.0, price_ars=200.0, units=10.0):
    return make_holding(position=make_position(units=units, cost_ars=cost_ars, cost_usd=10.0),
                        quote=make_quote(price_ars=price_ars, price_usd=2.0))


def test_totals_add_up_across_the_holdings():
    kpis = Kpis.from_holdings([holding(cost_ars=1000.0), holding(cost_ars=500.0)], ARS)
    assert kpis.invested == pytest.approx(1500.0)
    assert kpis.value == pytest.approx(4000.0)


def test_unrealized_pl_is_derived_from_the_totals():
    kpis = Kpis.from_holdings([holding(cost_ars=1000.0, price_ars=150.0)], ARS)
    assert kpis.pl_abs == pytest.approx(500.0)
    assert kpis.pl_pct == pytest.approx(50.0)


def test_an_empty_tab_reports_nothing_rather_than_zero():
    """Zero would read as "you invested nothing"; None reads as "no data"."""
    kpis = Kpis.from_holdings([], ARS)
    assert kpis.invested is None
    assert kpis.value is None
    assert kpis.pl_abs is None
    assert kpis.pl_pct is None


def test_unpriced_holdings_leave_the_value_undefined():
    kpis = Kpis.from_holdings([make_holding(quote=Quote.unavailable("sin datos"))], ARS)
    assert kpis.invested is not None
    assert kpis.value is None
    assert kpis.pl_abs is None


def test_priced_holdings_still_total_up_when_a_neighbour_has_no_price():
    holdings = [holding(cost_ars=1000.0), make_holding(quote=Quote.unavailable("sin datos"))]
    kpis = Kpis.from_holdings(holdings, ARS)
    assert kpis.value == pytest.approx(2000.0)


def test_a_zero_invested_total_leaves_the_percentage_undefined():
    kpis = Kpis.from_holdings([holding(cost_ars=0.0)], ARS)
    assert kpis.pl_pct is None


def test_realized_results_are_totalled_too():
    from portfolio_dashboard.portfolio.position import Position
    position = Position()
    position.buy(10, {ARS: 1000.0, "usd": 10.0}, "2025", in_scope=True)
    position.sell(5, {ARS: 800.0, "usd": 8.0}, in_scope=True)
    kpis = Kpis.from_holdings([make_holding(position=position)], ARS)
    assert kpis.realized == pytest.approx(300.0)


def test_as_dict_exposes_the_five_pills():
    assert set(Kpis.from_holdings([], ARS).as_dict()) == {
        "invested", "value", "pl_abs", "pl_pct", "realized"}
