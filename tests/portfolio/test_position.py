# -*- coding: utf-8 -*-
import pytest

from portfolio_dashboard.market import ARS, USD
from portfolio_dashboard.portfolio.position import Position

ONE_UNIT = {ARS: 1000.0, USD: 1.0}


def amounts(ars, usd):
    return {ARS: ars, USD: usd}


def test_a_fresh_position_is_empty():
    position = Position()
    assert position.is_empty
    assert position.units == 0.0
    assert position.cost_basis[ARS] == 0.0


def test_buying_accumulates_units_and_cost_in_both_currencies():
    position = Position()
    position.buy(10, amounts(10000.0, 10.0), "2025", in_scope=True)
    position.buy(5, amounts(6000.0, 5.0), "2025", in_scope=True)
    assert position.units == 15
    assert position.cost_basis[ARS] == 16000.0
    assert position.cost_basis[USD] == 15.0


def test_selling_uses_the_average_cost_not_the_sale_price():
    position = Position()
    position.buy(10, amounts(1000.0, 10.0), "2025", in_scope=True)   # 100 ARS / unit
    position.sell(4, amounts(800.0, 8.0), in_scope=True)
    assert position.units == 6
    assert position.units_sold == 4
    assert position.cost_of_sales[ARS] == pytest.approx(400.0)       # 4 x 100
    assert position.income_from_sales[ARS] == 800.0
    assert position.cost_basis[ARS] == pytest.approx(600.0)


def test_the_average_cost_blends_purchases_at_different_prices():
    position = Position()
    position.buy(10, amounts(1000.0, 10.0), "2025", in_scope=True)   # 100 / unit
    position.buy(10, amounts(3000.0, 30.0), "2025", in_scope=True)   # 300 / unit
    position.sell(5, amounts(1500.0, 15.0), in_scope=True)
    assert position.cost_of_sales[ARS] == pytest.approx(1000.0)      # 5 x 200


def test_selling_everything_leaves_no_units_and_no_cost():
    position = Position()
    position.buy(10, amounts(1000.0, 10.0), "2025", in_scope=True)
    position.sell(10, amounts(1500.0, 15.0), in_scope=True)
    assert position.units == pytest.approx(0.0)
    assert position.cost_basis[ARS] == pytest.approx(0.0)
    assert position.is_empty is False   # it still has sales to report


def test_selling_more_than_was_bought_is_flagged():
    """Part of that sale has no purchase cost, so its realized P&L is inflated
    and the dashboard has to warn about it."""
    position = Position()
    position.buy(5, amounts(500.0, 5.0), "2025", in_scope=True)
    position.sell(8, amounts(1600.0, 16.0), in_scope=True)
    assert position.oversold is True


def test_a_normal_sale_is_not_flagged():
    position = Position()
    position.buy(5, amounts(500.0, 5.0), "2025", in_scope=True)
    position.sell(5, amounts(1000.0, 10.0), in_scope=True)
    assert position.oversold is False


def test_selling_from_an_empty_position_costs_nothing():
    position = Position()
    position.sell(3, amounts(300.0, 3.0), in_scope=True)
    assert position.cost_of_sales[ARS] == 0.0
    assert position.oversold is True


def test_out_of_scope_trades_still_move_the_real_average_cost():
    """This is what makes a 2026 sale of units bought in 2025 carry the real
    cost of those units instead of zero."""
    position = Position()
    position.buy(10, amounts(1000.0, 10.0), "2025", in_scope=False)
    position.sell(4, amounts(800.0, 8.0), in_scope=True)
    assert position.cost_of_sales[ARS] == pytest.approx(400.0)
    assert position.cost_basis[ARS] == pytest.approx(-400.0)  # only the sale is reported


def test_out_of_scope_trades_are_not_reported():
    position = Position()
    position.buy(10, amounts(1000.0, 10.0), "2025", in_scope=False)
    assert position.units == 0.0
    assert position.cost_basis[ARS] == 0.0


def test_purchase_years_are_collected_sorted_and_deduplicated():
    position = Position()
    position.buy(1, ONE_UNIT, "2026", in_scope=True)
    position.buy(1, ONE_UNIT, "2025", in_scope=True)
    position.buy(1, ONE_UNIT, "2025", in_scope=True)
    assert position.buy_years == ["2025", "2026"]


def test_a_purchase_without_a_readable_date_adds_no_year():
    position = Position()
    position.buy(1, ONE_UNIT, None, in_scope=True)
    assert position.buy_years == []


def test_sales_do_not_add_purchase_years():
    position = Position()
    position.buy(1, ONE_UNIT, "2025", in_scope=True)
    position.sell(1, ONE_UNIT, in_scope=True)
    assert position.buy_years == ["2025"]


def test_a_position_is_real_until_something_is_approximated():
    position = Position()
    assert position.dual_real is True
    position.approximated = True
    assert position.dual_real is False


def test_reported_units_never_go_negative():
    """A spreadsheet inconsistency must not show a negative holding."""
    position = Position()
    position.sell(5, amounts(500.0, 5.0), in_scope=True)
    assert position.units < 0
    assert position.reported_units == 0.0


def test_a_position_with_only_sales_is_not_empty():
    position = Position()
    position.buy(5, amounts(500.0, 5.0), "2025", in_scope=False)
    position.sell(5, amounts(700.0, 7.0), in_scope=True)
    assert position.is_empty is False


def test_currencies_are_tracked_independently():
    position = Position()
    position.buy(10, amounts(1000.0, 20.0), "2025", in_scope=True)
    position.sell(5, amounts(800.0, 4.0), in_scope=True)
    assert position.cost_of_sales[ARS] == pytest.approx(500.0)
    assert position.cost_of_sales[USD] == pytest.approx(10.0)
    assert position.income_from_sales[USD] == 4.0
