# -*- coding: utf-8 -*-
import pytest

from portfolio.market import ARS, USD
from portfolio.marketdata.fx_rate import FxRate
from portfolio.marketdata.quote import UNAVAILABLE, Quote

FX = FxRate(1000.0, "test")


def test_a_usd_native_price_is_exact_and_the_ars_one_is_derived():
    quote = Quote.from_native(2.5, USD, "PPI (en vivo)", FX)
    assert quote.price_usd == 2.5
    assert quote.price_ars == 2500.0


def test_an_ars_native_price_is_exact_and_the_usd_one_is_derived():
    quote = Quote.from_native(2500.0, ARS, "PPI (en vivo)", FX)
    assert quote.price_ars == 2500.0
    assert quote.price_usd == pytest.approx(2.5)


def test_without_an_exchange_rate_only_the_native_price_survives():
    quote = Quote.from_native(2.5, USD, "manual", FxRate.unavailable("sin cotizacion"))
    assert quote.price_usd == 2.5
    assert quote.price_ars is None


def test_a_missing_price_stays_missing_in_both_currencies():
    quote = Quote.from_native(None, USD, "manual", FX)
    assert (quote.price_ars, quote.price_usd) == (None, None)


def test_the_source_is_carried_through():
    assert Quote.from_native(1.0, USD, "Yahoo Finance", FX).source == "Yahoo Finance"


def test_an_unavailable_quote_records_why():
    quote = Quote.unavailable("PPI: sin datos | Yahoo: sin datos")
    assert (quote.price_ars, quote.price_usd) == (None, None)
    assert quote.source == UNAVAILABLE
    assert "Yahoo" in quote.debug_note


def test_a_resolved_quote_carries_no_debug_note():
    assert Quote.from_native(1.0, USD, "manual", FX).debug_note is None


@pytest.mark.parametrize("currency, expected", [(ARS, 2500.0), (USD, 2.5)])
def test_price_reads_the_requested_currency(currency, expected):
    assert Quote.from_native(2.5, USD, "PPI (en vivo)", FX).price(currency) == expected
