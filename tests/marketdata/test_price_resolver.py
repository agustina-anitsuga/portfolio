# -*- coding: utf-8 -*-
import pytest

from doubles import (CEDEARS_MARKET, RSU_MARKET, USD_MARKET, FakePpi, FakeYahoo,
                     make_instrument)
from portfolio_dashboard.marketdata.price_resolver import (MANUAL_SOURCE, PPI_SOURCE,
                                                           YAHOO_SOURCE, PriceResolver)
from portfolio_dashboard.marketdata.trend import Trend


def resolver(ppi=None, yahoo=None, fx=None):
    from portfolio_dashboard.marketdata.fx_rate import FxRate
    return PriceResolver(ppi or FakePpi(), yahoo or FakeYahoo(), fx or FxRate(1000.0, "test"))


def test_ppi_is_the_first_choice():
    prices = resolver(ppi=FakePpi(prices={"AAA": (3.0, None)}),
                      yahoo=FakeYahoo(prices={"AAA": (9.0, None)}))
    quote = prices.quote(USD_MARKET, make_instrument("AAA"))
    assert (quote.price_usd, quote.source) == (3.0, PPI_SOURCE)


def test_yahoo_covers_usd_instruments_that_ppi_does_not_quote():
    prices = resolver(yahoo=FakeYahoo(prices={"AAA": (9.0, None)}))
    quote = prices.quote(USD_MARKET, make_instrument("AAA"))
    assert (quote.price_usd, quote.source) == (9.0, YAHOO_SOURCE)


def test_yahoo_also_covers_rsu():
    prices = resolver(yahoo=FakeYahoo(prices={"JPM": (300.0, None)}))
    assert prices.quote(RSU_MARKET, make_instrument("JPM")).source == YAHOO_SOURCE


def test_yahoo_is_never_used_for_cedears():
    """The Cedear price on BYMA is not the price of the underlying stock in
    USD, so asking Yahoo there would return a wrong number."""
    yahoo = FakeYahoo(prices={"AAA": (9.0, None)})
    prices = resolver(yahoo=yahoo)
    quote = prices.quote(CEDEARS_MARKET, make_instrument("AAA"))
    assert quote.source != YAHOO_SOURCE
    assert yahoo.calls == []


def test_the_manual_price_is_the_last_resort():
    prices = resolver()
    quote = prices.quote(CEDEARS_MARKET, make_instrument("AAA", manual_price=1500.0))
    assert (quote.price_ars, quote.source) == (1500.0, MANUAL_SOURCE)


def test_the_manual_price_is_coerced_to_a_number():
    quote = resolver().quote(CEDEARS_MARKET, make_instrument("AAA", manual_price="1500"))
    assert quote.price_ars == 1500.0


def test_a_manual_price_of_zero_is_still_used():
    """Unlike a missing value, an explicit 0 is a decision by the user."""
    quote = resolver().quote(CEDEARS_MARKET, make_instrument("AAA", manual_price=0))
    assert quote.source == MANUAL_SOURCE


def test_when_everything_fails_the_reasons_are_collected():
    prices = resolver(ppi=FakePpi(prices={"AAA": (None, "PPI cerrado")}),
                      yahoo=FakeYahoo(prices={"AAA": (None, "Yahoo sin datos")}))
    quote = prices.quote(USD_MARKET, make_instrument("AAA", manual_price=None))
    assert quote.price_usd is None
    assert quote.debug_note == "PPI: PPI cerrado | Yahoo: Yahoo sin datos"


def test_for_cedears_the_note_only_mentions_ppi():
    prices = resolver(ppi=FakePpi(prices={"AAA": (None, "PPI cerrado")}))
    quote = prices.quote(CEDEARS_MARKET, make_instrument("AAA"))
    assert quote.debug_note == "PPI: PPI cerrado"


def test_the_derived_currency_uses_the_exchange_rate():
    prices = resolver(ppi=FakePpi(prices={"AAA": (3.0, None)}))
    quote = prices.quote(USD_MARKET, make_instrument("AAA"))
    assert quote.price_ars == 3000.0


def test_ppi_is_asked_with_the_instrument_metadata():
    ppi = FakePpi(prices={"AAA": (3.0, None)})
    resolver(ppi=ppi).quote(USD_MARKET, make_instrument("AAA", ppi_type="CEDEARS", settlement="A-24HS"))
    assert ppi.price_calls == [("AAA", "CEDEARS", "A-24HS")]


def test_quotes_are_cached_per_market_and_ticker():
    """The dashboard builds one report per year on top of the full one, and
    today's price is the same in all of them."""
    ppi = FakePpi(prices={"AAA": (3.0, None)})
    prices = resolver(ppi=ppi)
    instrument = make_instrument("AAA")
    first = prices.quote(USD_MARKET, instrument)
    second = prices.quote(USD_MARKET, instrument)
    assert first is second
    assert len(ppi.price_calls) == 1


def test_the_same_ticker_in_two_markets_is_quoted_separately():
    """A ticker held both as a Cedear and as a US stock has two prices."""
    ppi = FakePpi(prices={"AAA": (3.0, None)})
    prices = resolver(ppi=ppi)
    prices.quote(USD_MARKET, make_instrument("AAA"))
    prices.quote(CEDEARS_MARKET, make_instrument("AAA"))
    assert len(ppi.price_calls) == 2


def test_trends_are_cached_too():
    ppi = FakePpi(trends={"AAA": Trend(5.0, [1.0, 1.05])})
    prices = resolver(ppi=ppi)
    instrument = make_instrument("AAA")
    assert prices.trend(USD_MARKET, instrument).pct == pytest.approx(5.0)
    prices.trend(USD_MARKET, instrument)
    assert len(ppi.trend_calls) == 1
