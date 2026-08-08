# -*- coding: utf-8 -*-
import io

from doubles import CEDEARS_MARKET, USD_MARKET, make_holding, make_instrument, make_quote
from portfolio.market import Market
from portfolio.marketdata.fx_rate import FxRate
from portfolio.marketdata.quote import Quote
from portfolio.portfolio.market_report import MarketReport
from portfolio.portfolio.snapshot import PortfolioSnapshot
from portfolio.console_summary import ConsoleSummary


def snapshot(holdings=None, fx=None, market=USD_MARKET):
    reports = {key: MarketReport(Market.get(key), []) for key in Market.keys()}
    reports[market.key] = MarketReport(market, list(holdings or [make_holding()]))
    # `fx or ...` would discard an unavailable rate, which is deliberately falsy
    return PortfolioSnapshot(reports=reports,
                             fx=FxRate(1450.0, "PPI (MEP)") if fx is None else fx)


def summary_of(snap, paths=("portfolio.html",)):
    out = io.StringIO()
    ConsoleSummary(snap, out=out).print_report(list(paths))
    return out.getvalue()


def test_every_generated_file_is_listed():
    text = summary_of(snapshot(), paths=("portfolio.html", "portfolio.xlsx"))
    assert "Listo: portfolio.html" in text
    assert "Listo: portfolio.xlsx" in text


def test_the_number_of_positions_is_reported():
    text = summary_of(snapshot([make_holding(instrument=make_instrument("AAA")),
                                make_holding(instrument=make_instrument("BBB"))]))
    assert "2 posiciones procesadas" in text


def test_with_everything_priced_nothing_more_is_said():
    text = summary_of(snapshot())
    assert "0 sin precio disponible" in text
    assert "Sin precio:" not in text


def test_unpriced_positions_are_named_with_their_portfolio():
    unpriced = make_holding(market=CEDEARS_MARKET, instrument=make_instrument("ZZZ"),
                            quote=Quote.unavailable("PPI: cerrado"))
    text = summary_of(snapshot([unpriced], market=CEDEARS_MARKET))
    assert "Sin precio: ZZZ (Cedears)" in text


def test_the_reason_each_source_failed_is_printed():
    """Otherwise a missing price looks the same as a typo in the ticker."""
    unpriced = make_holding(instrument=make_instrument("ZZZ"),
                            quote=Quote.unavailable("PPI: cerrado | Yahoo: sin datos"))
    text = summary_of(snapshot([unpriced]))
    assert "- ZZZ: PPI: cerrado | Yahoo: sin datos" in text


def test_the_hint_about_the_manual_price_is_shown_when_something_is_missing():
    unpriced = make_holding(quote=Quote.unavailable("sin datos"))
    assert "Precio Manual" in summary_of(snapshot([unpriced]))


def test_a_position_priced_in_one_currency_is_not_reported_as_missing():
    holding = make_holding(quote=make_quote(price_ars=None, price_usd=2.0))
    assert "0 sin precio" in summary_of(snapshot([holding]))


def test_the_exchange_rate_and_its_origin_are_reported():
    assert "Tipo de cambio: 1450.0 (PPI (MEP))" in summary_of(snapshot())


def test_a_missing_exchange_rate_is_flagged_with_advice():
    text = summary_of(snapshot(fx=FxRate.unavailable("mercado cerrado")))
    assert "Tipo de cambio: N/D (mercado cerrado)" in text
    assert "PPI_PUBLIC_KEY" in text


def test_with_a_rate_available_no_advice_is_printed():
    assert "PPI_PUBLIC_KEY" not in summary_of(snapshot())
