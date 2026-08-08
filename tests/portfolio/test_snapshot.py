# -*- coding: utf-8 -*-
from doubles import USD_MARKET, make_holding, make_instrument, make_quote
from portfolio_dashboard.marketdata.fx_rate import FxRate
from portfolio_dashboard.marketdata.quote import Quote
from portfolio_dashboard.portfolio.market_report import MarketReport
from portfolio_dashboard.portfolio.snapshot import PortfolioSnapshot


def report(*holdings):
    return MarketReport(USD_MARKET, list(holdings))


def snapshot(**kwargs):
    defaults = dict(reports={"usd": report(make_holding())}, fx=FxRate(1000.0, "test"))
    defaults.update(kwargs)
    return PortfolioSnapshot(**defaults)


def test_years_come_back_newest_first():
    snap = snapshot(reports_by_year={"2025": {}, "2026": {}, "2024": {}})
    assert snap.years == ["2026", "2025", "2024"]


def test_without_yearly_reports_there_are_no_years():
    assert snapshot().years == []


def test_report_looks_up_a_market_by_key():
    snap = snapshot()
    assert snap.report("usd") is snap.reports["usd"]


def test_all_rows_flattens_every_market():
    snap = snapshot(reports={
        "usd": report(make_holding(instrument=make_instrument("AAA"))),
        "cedears": report(make_holding(instrument=make_instrument("BBB"))),
    })
    assert sorted(row["key"] for row in snap.all_rows()) == ["AAA", "BBB"]


def test_unpriced_rows_are_the_ones_without_a_value_in_either_currency():
    priced = make_holding(instrument=make_instrument("AAA"))
    unpriced = make_holding(instrument=make_instrument("ZZZ"), quote=Quote.unavailable("sin datos"))
    snap = snapshot(reports={"usd": report(priced, unpriced)})
    assert [row["key"] for row in snap.unpriced_rows()] == ["ZZZ"]


def test_a_row_priced_in_only_one_currency_is_not_unpriced():
    holding = make_holding(quote=make_quote(price_ars=None, price_usd=2.0))
    assert snapshot(reports={"usd": report(holding)}).unpriced_rows() == []


def test_position_count_adds_up_every_market():
    snap = snapshot(reports={
        "usd": report(make_holding(instrument=make_instrument("AAA")),
                      make_holding(instrument=make_instrument("BBB"))),
        "cedears": report(make_holding(instrument=make_instrument("CCC"))),
    })
    assert snap.position_count == 3


def test_transactions_default_to_an_empty_list():
    assert snapshot().transactions == []
