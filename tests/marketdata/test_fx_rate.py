# -*- coding: utf-8 -*-
import pytest

from portfolio_dashboard.market import ARS, USD
from portfolio_dashboard.marketdata.fx_rate import FxRate


def test_a_rate_with_a_value_is_truthy():
    assert bool(FxRate(1450.0, "PPI")) is True


def test_an_unavailable_rate_is_falsy():
    """Callers guard on `if fx:` before converting anything."""
    assert bool(FxRate.unavailable("mercado cerrado")) is False
    assert bool(FxRate()) is False


def test_a_zero_rate_is_falsy_too():
    """Dividing by it would raise, so it must not pass the guard."""
    assert bool(FxRate(0.0, "roto")) is False


def test_unavailable_keeps_the_reason_as_the_source():
    assert FxRate.unavailable("mercado cerrado").source == "mercado cerrado"


def test_unavailable_without_a_reason_still_reads_sensibly():
    assert FxRate.unavailable(None).source == "no disponible"


def test_converts_usd_into_ars_by_multiplying():
    assert FxRate(1000.0, "test").to_ars(2.5) == 2500.0


def test_converts_ars_into_usd_by_dividing():
    assert FxRate(1000.0, "test").to_usd(2500.0) == 2.5


@pytest.mark.parametrize("currency, expected", [(ARS, 2500.0), (USD, 0.0025)])
def test_convert_picks_the_direction_from_the_target_currency(currency, expected):
    assert FxRate(1000.0, "test").convert(2.5, currency) == pytest.approx(expected)
