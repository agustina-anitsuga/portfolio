# -*- coding: utf-8 -*-
from doubles import FakePpi
from portfolio.marketdata.fx_rate_provider import CCL_LIVE_SOURCE, LIVE_SOURCE, MANUAL_SOURCE, FxRateProvider


def test_prefers_the_live_mep_rate():
    fx = FxRateProvider(FakePpi(mep=(1450.0, None))).resolve(manual_fx=999.0)
    assert fx.value == 1450.0
    assert fx.source == LIVE_SOURCE


def test_falls_back_to_the_manual_rate_from_the_config_sheet():
    fx = FxRateProvider(FakePpi(mep=(None, "fuera de horario"))).resolve(manual_fx=1200.0)
    assert fx.value == 1200.0
    assert fx.source == MANUAL_SOURCE


def test_the_manual_rate_is_coerced_to_a_number():
    """Excel hands back whatever the cell holds, sometimes as text."""
    assert FxRateProvider(FakePpi()).resolve(manual_fx="1200.5").value == 1200.5


def test_without_any_source_it_keeps_ppis_reason():
    fx = FxRateProvider(FakePpi(mep=(None, "fuera de horario"))).resolve(manual_fx=None)
    assert fx.value is None
    assert fx.source == "fuera de horario"
    assert not fx


def test_a_zero_manual_rate_is_not_used():
    fx = FxRateProvider(FakePpi(mep=(None, "sin datos"))).resolve(manual_fx=0)
    assert fx.value is None


def test_ccl_prefers_the_live_rate():
    fx = FxRateProvider(FakePpi(ccl=(1500.0, None))).resolve_ccl(manual_ccl=999.0)
    assert fx.value == 1500.0
    assert fx.source == CCL_LIVE_SOURCE


def test_ccl_falls_back_to_the_manual_value():
    fx = FxRateProvider(FakePpi(ccl=(None, "fuera de horario"))).resolve_ccl(manual_ccl="1300")
    assert (fx.value, fx.source) == (1300.0, MANUAL_SOURCE)


def test_ccl_without_any_source_keeps_ppis_reason():
    fx = FxRateProvider(FakePpi(ccl=(None, "fuera de horario"))).resolve_ccl(manual_ccl=None)
    assert not fx and fx.source == "fuera de horario"
