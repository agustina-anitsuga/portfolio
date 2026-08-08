# -*- coding: utf-8 -*-
import pytest

from doubles import make_position
from portfolio.market import ARS, USD
from portfolio.portfolio.currency_metrics import CurrencyMetrics
from portfolio.portfolio.position import Position


def metrics(position=None, currency=ARS, units=10.0, price=200.0):
    position = position or make_position(units=10.0, cost_ars=1000.0, cost_usd=10.0)
    return CurrencyMetrics.compute(position, currency, units, price)


def test_average_cost_is_the_invested_amount_over_the_units():
    assert metrics().avg_cost == pytest.approx(100.0)


def test_value_is_the_current_price_times_the_units():
    assert metrics(price=250.0).value == pytest.approx(2500.0)


def test_unrealized_pl_compares_value_against_what_was_invested():
    result = metrics(price=250.0)
    assert result.pl_abs == pytest.approx(1500.0)
    assert result.pl_pct == pytest.approx(150.0)


def test_a_loss_comes_out_negative():
    result = metrics(price=50.0)
    assert result.pl_abs == pytest.approx(-500.0)
    assert result.pl_pct == pytest.approx(-50.0)


def test_without_a_price_there_is_no_value_and_no_pl():
    result = metrics(price=None)
    assert result.value is None
    assert result.pl_abs is None
    assert result.pl_pct is None


def test_the_invested_amount_survives_even_without_a_price():
    """Losing the quote must not hide what was actually spent."""
    assert metrics(price=None).invested == 1000.0


def test_realized_pl_is_income_minus_the_cost_of_what_was_sold():
    position = Position()
    position.buy(10, {ARS: 1000.0, USD: 10.0}, "2025", in_scope=True)
    position.sell(5, {ARS: 800.0, USD: 8.0}, in_scope=True)
    result = CurrencyMetrics.compute(position, ARS, 5.0, 200.0)
    assert result.cost_of_sales == pytest.approx(500.0)
    assert result.income_from_sales == 800.0
    assert result.realized_abs == pytest.approx(300.0)
    assert result.realized_pct == pytest.approx(60.0)


def test_without_sales_the_realized_percentage_is_undefined_not_zero():
    result = metrics()
    assert result.realized_abs == 0.0
    assert result.realized_pct is None


def test_a_position_with_no_units_left_has_no_average_cost():
    position = Position()
    position.buy(5, {ARS: 500.0, USD: 5.0}, "2025", in_scope=True)
    position.sell(5, {ARS: 900.0, USD: 9.0}, in_scope=True)
    assert CurrencyMetrics.compute(position, ARS, 0.0, 200.0).avg_cost is None


def test_a_zero_invested_amount_leaves_the_percentage_undefined():
    """Dividing by it would raise; the dashboard shows a dash instead."""
    position = Position()
    position.buy(10, {ARS: 0.0, USD: 0.0}, "2025", in_scope=True)
    assert CurrencyMetrics.compute(position, ARS, 10.0, 5.0).pl_pct is None


def test_each_currency_is_computed_from_its_own_numbers():
    position = make_position(units=10.0, cost_ars=20000.0, cost_usd=20.0)
    assert CurrencyMetrics.compute(position, ARS, 10.0, 3000.0).pl_abs == pytest.approx(10000.0)
    assert CurrencyMetrics.compute(position, USD, 10.0, 3.0).pl_abs == pytest.approx(10.0)


def test_as_dict_suffixes_every_field_with_the_currency():
    fields = metrics().as_dict(ARS)
    assert fields["avg_cost_ars"] == pytest.approx(100.0)
    assert set(fields) == {
        "avg_cost_ars", "price_ars", "invested_ars", "value_ars", "pl_abs_ars", "pl_pct_ars",
        "cost_of_sales_ars", "income_from_sales_ars", "realized_abs_ars", "realized_pct_ars",
    }
