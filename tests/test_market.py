# -*- coding: utf-8 -*-
import pytest

from portfolio.market import ARS, CURRENCIES, USD, Market, other_currency


def test_other_currency_flips_between_the_two():
    assert other_currency(ARS) == USD
    assert other_currency(USD) == ARS


def test_currencies_holds_both():
    assert CURRENCIES == (ARS, USD)


def test_markets_are_listed_in_dashboard_order():
    assert Market.keys() == ["usd", "cedears", "merval", "rsu", "bonds"]


def test_each_market_knows_its_sheet_and_native_currency():
    assert Market.get("cedears").sheet == "tx-cedears"
    assert Market.get("cedears").native_currency == ARS
    assert Market.get("rsu").native_currency == USD


def test_other_currency_of_a_market_is_the_one_that_may_be_missing():
    assert Market.get("usd").other_currency == ARS
    assert Market.get("merval").other_currency == USD


@pytest.mark.parametrize("key, ars_column, usd_column", [
    ("usd", 6, 5),
    ("cedears", 4, 6),
    ("merval", 5, 6),
    ("rsu", 6, 5),
    ("bonds", 5, 6),
])
def test_amount_columns_match_each_sheet_layout(key, ars_column, usd_column):
    """These indexes are the contract with the spreadsheet: getting one wrong
    reads the neighbouring column and silently reports the wrong money."""
    market = Market.get(key)
    assert market.amount_column(ARS) == ars_column
    assert market.amount_column(USD) == usd_column


def test_labels_maps_every_key():
    assert Market.labels()["merval"] == "Acciones Merval"
    assert set(Market.labels()) == set(Market.keys())


def test_unknown_market_raises():
    with pytest.raises(KeyError):
        Market.get("cripto")
