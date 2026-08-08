# -*- coding: utf-8 -*-
import pytest

from doubles import (CEDEARS_MARKET, USD_MARKET, make_holding, make_instrument,
                     make_position, make_quote)
from portfolio_dashboard.market import ARS, USD
from portfolio_dashboard.marketdata.quote import Quote
from portfolio_dashboard.marketdata.trend import Trend
from portfolio_dashboard.portfolio.position import Position


def test_metrics_are_computed_for_both_currencies():
    holding = make_holding(position=make_position(units=10.0, cost_ars=1000.0, cost_usd=10.0),
                           quote=make_quote(price_ars=200.0, price_usd=2.0))
    assert holding.metrics[ARS].value == pytest.approx(2000.0)
    assert holding.metrics[USD].value == pytest.approx(20.0)


def test_value_reads_the_requested_currency():
    holding = make_holding(quote=make_quote(price_ars=200.0, price_usd=2.0))
    assert holding.value(ARS) == pytest.approx(2000.0)
    assert holding.value(USD) == pytest.approx(20.0)


def test_a_holding_without_a_price_in_either_currency_is_unpriced():
    assert make_holding(quote=Quote.unavailable("sin datos")).unpriced is True


def test_a_holding_priced_in_only_one_currency_is_not_unpriced():
    """It happens when there is no exchange rate: the native price still counts."""
    holding = make_holding(quote=make_quote(price_ars=None, price_usd=2.0))
    assert holding.unpriced is False


def test_negative_units_are_reported_as_zero():
    position = Position()
    position.sell(5, {ARS: 500.0, USD: 5.0}, in_scope=True)
    assert make_holding(position=position).units == 0.0


def test_the_row_carries_the_instrument_metadata():
    instrument = make_instrument("BBB", name="Beta SA", sector="Energy", instrument_type="ETF",
                                 ratio=20)
    row = make_holding(instrument=instrument).as_dict()
    assert row["key"] == "BBB"
    assert row["name"] == "Beta SA"
    assert row["sector"] == "Energy"
    assert row["instrument_type"] == "ETF"
    assert row["ratio"] == 20


def test_a_missing_sector_or_type_shows_a_dash():
    row = make_holding(instrument=make_instrument(sector="", instrument_type="")).as_dict()
    assert row["sector"] == "-"
    assert row["instrument_type"] == "-"


def test_the_row_carries_the_market_and_its_native_currency():
    row = make_holding(market=CEDEARS_MARKET).as_dict()
    assert row["market"] == "cedears"
    assert row["native_currency"] == ARS


def test_the_row_carries_the_price_source_and_the_trend():
    holding = make_holding(quote=make_quote(source="Yahoo Finance"),
                           trend=Trend(12.5, [1.0, 1.125]))
    row = holding.as_dict()
    assert row["price_source"] == "Yahoo Finance"
    assert row["trend_30d"] == pytest.approx(12.5)
    assert row["trend_series"] == [1.0, 1.125]


def test_the_row_reports_when_amounts_were_approximated():
    position = make_position()
    position.approximated = True
    assert make_holding(position=position).as_dict()["fx_approx"] is True


def test_the_row_reports_an_oversold_position():
    position = make_position()
    position.oversold = True
    assert make_holding(position=position).as_dict()["oversold"] is True


def test_the_debug_note_travels_only_when_there_is_no_price():
    priced = make_holding().as_dict()
    unpriced = make_holding(quote=Quote.unavailable("PPI: cerrado")).as_dict()
    assert priced["price_debug_note"] is None
    assert unpriced["price_debug_note"] == "PPI: cerrado"


def test_the_portfolio_share_starts_empty_and_can_be_set():
    holding = make_holding()
    assert holding.as_dict()["pct_portfolio_ars"] is None
    holding.set_portfolio_share(ARS, 25.0)
    assert holding.as_dict()["pct_portfolio_ars"] == 25.0


def test_the_row_has_the_metrics_of_both_currencies_side_by_side():
    row = make_holding(market=USD_MARKET).as_dict()
    for field in ("avg_cost", "price", "invested", "value", "pl_abs", "pl_pct",
                  "cost_of_sales", "income_from_sales", "realized_abs", "realized_pct"):
        assert f"{field}_ars" in row
        assert f"{field}_usd" in row
