# -*- coding: utf-8 -*-
import pytest

from portfolio.marketdata.fx_rate import FxRate
from portfolio.portfolio.contribution_plan import ContributionPlan

CONTRIBUTION = {"monthly_ars": 4000000.0, "rows": [
    {"ticker": "SCHD", "pct": 35.0, "currency": "CCL"},
    {"ticker": "SPY", "pct": 40.0, "currency": "ARS"},
    {"ticker": "SGOV", "pct": 15.0, "currency": "CCL"},
    {"ticker": "XLU", "pct": 10.0, "currency": "ARS"},
]}


def plan(ccl=FxRate(1000.0, "PPI"), contribution=CONTRIBUTION):
    return ContributionPlan(contribution, ccl).as_dict()


def test_each_ticker_gets_its_share_of_the_month():
    amounts = {r["ticker"]: r["ars"] for r in plan()["rows"]}
    assert amounts == {"SCHD": 1400000, "SPY": 1600000, "SGOV": 600000, "XLU": 400000}


def test_only_the_ccl_tickers_need_pesos_converted_first():
    result = plan()
    assert result["ars_to_ccl"] == 2000000
    assert result["usd_from_ccl"] == pytest.approx(2000.0)
    assert result["ars_direct"] == 2000000


def test_dollar_amounts_use_the_ccl_rate():
    rows = {r["ticker"]: r["usd"] for r in plan(FxRate(1250.0, "PPI"))["rows"]}
    assert rows["SCHD"] == pytest.approx(1120.0)
    assert plan(FxRate(1250.0, "PPI"))["monthly_usd"] == pytest.approx(3200.0)


def test_without_a_ccl_rate_the_dollar_amounts_are_empty():
    result = plan(FxRate.unavailable("fuera de horario"))
    assert result["usd_from_ccl"] is None
    assert result["ccl_rate"] is None
    assert result["ccl_source"] == "fuera de horario"
    assert result["ars_to_ccl"] == 2000000      # the peso amounts do not depend on it


def test_the_percentages_total_is_reported_to_catch_typos():
    bad = {"monthly_ars": 100.0, "rows": [{"ticker": "SPY", "pct": 90.0, "currency": "ARS"}]}
    assert plan(contribution=bad)["pct_total"] == 90.0


def test_no_contribution_sheet_means_no_plan():
    assert plan(contribution=None) is None
