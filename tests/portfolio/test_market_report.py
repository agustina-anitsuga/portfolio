# -*- coding: utf-8 -*-
import pytest

from doubles import USD_MARKET, make_holding, make_instrument, make_position, make_quote
from portfolio_dashboard.market import ARS, USD
from portfolio_dashboard.marketdata.quote import Quote
from portfolio_dashboard.portfolio.market_report import MarketReport


def holding(key="AAA", value_ars=1000.0, cost_ars=500.0):
    """A holding of exactly one unit, so price == value."""
    return make_holding(instrument=make_instrument(key),
                        position=make_position(units=1.0, cost_ars=cost_ars, cost_usd=1.0),
                        quote=make_quote(price_ars=value_ars, price_usd=value_ars / 1000.0))


def test_holdings_are_sorted_from_the_largest_position_down():
    report = MarketReport(USD_MARKET, [holding("AAA", 100.0), holding("BBB", 900.0),
                                       holding("CCC", 500.0)])
    assert [row["key"] for row in report.rows] == ["BBB", "CCC", "AAA"]


def test_unpriced_holdings_sink_to_the_bottom():
    unpriced = make_holding(instrument=make_instrument("ZZZ"), quote=Quote.unavailable("sin datos"))
    report = MarketReport(USD_MARKET, [unpriced, holding("AAA", 100.0)])
    assert [row["key"] for row in report.rows] == ["AAA", "ZZZ"]


def test_each_holding_gets_its_share_of_the_tab_total():
    report = MarketReport(USD_MARKET, [holding("AAA", 750.0), holding("BBB", 250.0)])
    shares = {row["key"]: row["pct_portfolio_ars"] for row in report.rows}
    assert shares["AAA"] == pytest.approx(75.0)
    assert shares["BBB"] == pytest.approx(25.0)
    assert sum(shares.values()) == pytest.approx(100.0)


def test_the_share_is_computed_per_currency():
    report = MarketReport(USD_MARKET, [holding("AAA", 750.0), holding("BBB", 250.0)])
    row = report.rows[0]
    assert row["pct_portfolio_usd"] == pytest.approx(75.0)


def test_an_unpriced_holding_has_no_share():
    unpriced = make_holding(instrument=make_instrument("ZZZ"), quote=Quote.unavailable("sin datos"))
    report = MarketReport(USD_MARKET, [holding("AAA", 100.0), unpriced])
    assert report.rows[-1]["pct_portfolio_ars"] is None


def test_with_nothing_priced_no_share_can_be_computed():
    unpriced = make_holding(quote=Quote.unavailable("sin datos"))
    report = MarketReport(USD_MARKET, [unpriced])
    assert report.rows[0]["pct_portfolio_ars"] is None


def test_kpis_are_computed_from_the_holdings():
    report = MarketReport(USD_MARKET, [holding("AAA", 1000.0, cost_ars=400.0)])
    assert report.kpis(ARS).invested == pytest.approx(400.0)
    assert report.kpis(ARS).value == pytest.approx(1000.0)
    assert report.kpis(USD).invested == pytest.approx(1.0)


def test_unpriced_holdings_are_counted():
    unpriced = make_holding(quote=Quote.unavailable("sin datos"))
    report = MarketReport(USD_MARKET, [holding(), unpriced, unpriced])
    assert report.unpriced_count == 2


def test_the_kpis_payload_carries_both_currencies_and_the_unpriced_count():
    report = MarketReport(USD_MARKET, [holding()])
    payload = report.kpis_payload()
    assert set(payload) == {"ars", "usd", "unpriced"}
    assert payload["unpriced"] == 0
    assert set(payload["ars"]) == {"invested", "value", "pl_abs", "pl_pct", "realized"}


def test_rows_are_built_once_and_reused():
    """They are handed straight to the JSON payload and the Excel writers."""
    report = MarketReport(USD_MARKET, [holding()])
    assert report.rows is report.rows


def test_an_empty_report_is_harmless():
    report = MarketReport(USD_MARKET, [])
    assert report.rows == []
    assert report.unpriced_count == 0
    assert report.kpis(ARS).invested is None
