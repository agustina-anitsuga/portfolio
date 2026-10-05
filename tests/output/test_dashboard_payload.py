# -*- coding: utf-8 -*-
import datetime as dt

from doubles import CEDEARS_MARKET, USD_MARKET, make_holding, make_instrument, make_quote
from portfolio.market import Market
from portfolio.marketdata.fx_rate import FxRate
from portfolio.output.dashboard_payload import DashboardPayload
from portfolio.portfolio.market_report import MarketReport
from portfolio.portfolio.snapshot import PortfolioSnapshot

NOW = dt.datetime(2026, 8, 8, 14, 30)


def report(market=USD_MARKET, *holdings):
    return MarketReport(market, list(holdings))


def snapshot(**kwargs):
    reports = {key: report(Market.get(key)) for key in Market.keys()}
    reports["usd"] = report(USD_MARKET, make_holding(instrument=make_instrument("AAA")))
    defaults = dict(reports=reports, fx=FxRate(1450.0, "PPI"), transactions=[],
                    watchlist=[], reports_by_year={})
    defaults.update(kwargs)
    return PortfolioSnapshot(**defaults)


def payload(**kwargs):
    return DashboardPayload(snapshot(**kwargs), now=NOW).as_dict()


def test_the_payload_has_the_sections_the_page_reads():
    assert set(payload()) == {"markets", "general", "transactions", "watchlist", "annual", "years",
                              "fx_rate", "fx_source", "generated_at"}


def test_every_market_is_present_even_when_empty():
    assert set(payload()["markets"]) == set(Market.keys())


def test_a_market_carries_its_label_rows_and_kpis():
    market = payload()["markets"]["usd"]
    assert market["label"] == "US Stocks"
    assert [row["key"] for row in market["rows"]] == ["AAA"]
    assert set(market["kpis"]) == {"ars", "usd", "unpriced"}


def test_the_yearly_sets_are_embedded_per_market():
    by_year = {"2025": {key: report(Market.get(key)) for key in Market.keys()}}
    by_year["2025"]["usd"] = report(USD_MARKET, make_holding(instrument=make_instrument("BBB")))
    market = payload(reports_by_year=by_year)["markets"]["usd"]
    assert [row["key"] for row in market["rows_by_year"]["2025"]] == ["BBB"]
    assert set(market["kpis_by_year"]["2025"]) == {"ars", "usd", "unpriced"}


def test_the_years_are_listed_newest_first():
    by_year = {year: {key: report(Market.get(key)) for key in Market.keys()}
               for year in ("2024", "2026", "2025")}
    assert payload(reports_by_year=by_year)["years"] == ["2026", "2025", "2024"]


def test_general_gathers_the_rows_of_every_market():
    reports = {key: report(Market.get(key)) for key in Market.keys()}
    reports["usd"] = report(USD_MARKET, make_holding(instrument=make_instrument("AAA")))
    reports["cedears"] = report(CEDEARS_MARKET,
                                make_holding(market=CEDEARS_MARKET,
                                             instrument=make_instrument("BBB")))
    keys = {row["key"] for row in payload(reports=reports)["general"]}
    assert keys == {"AAA", "BBB"}


def test_general_is_sorted_by_result_with_the_best_first():
    winner = make_holding(instrument=make_instrument("WIN"),
                          quote=make_quote(price_ars=9000.0, price_usd=9.0))
    loser = make_holding(instrument=make_instrument("LOSS"),
                         quote=make_quote(price_ars=10.0, price_usd=0.01))
    reports = {key: report(Market.get(key)) for key in Market.keys()}
    reports["usd"] = report(USD_MARKET, loser, winner)
    assert [row["key"] for row in payload(reports=reports)["general"]] == ["WIN", "LOSS"]


def test_the_exchange_rate_and_its_origin_travel_along():
    result = payload()
    assert result["fx_rate"] == 1450.0
    assert result["fx_source"] == "PPI"


def test_a_missing_exchange_rate_is_reported_as_nothing():
    result = payload(fx=FxRate.unavailable("mercado cerrado"))
    assert result["fx_rate"] is None
    assert result["fx_source"] == "mercado cerrado"


def test_the_watchlist_is_passed_through():
    assert payload(watchlist=[{"ticker": "AAPL"}])["watchlist"] == [{"ticker": "AAPL"}]


def test_the_transactions_are_passed_through():
    assert payload(transactions=[{"ticker": "AAA"}])["transactions"] == [{"ticker": "AAA"}]


def test_the_generation_time_is_stamped():
    assert payload()["generated_at"] == "2026-08-08 14:30"
