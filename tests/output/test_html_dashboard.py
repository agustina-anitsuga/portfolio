# -*- coding: utf-8 -*-
import datetime as dt
import json
import re

import pytest

from doubles import USD_MARKET, make_holding, make_instrument
from portfolio.market import Market
from portfolio.marketdata.fx_rate import FxRate
from portfolio.output.html_dashboard import ASSETS, HtmlDashboard
from portfolio.portfolio.market_report import MarketReport
from portfolio.portfolio.snapshot import PortfolioSnapshot


def snapshot():
    reports = {key: MarketReport(Market.get(key), []) for key in Market.keys()}
    reports["usd"] = MarketReport(USD_MARKET, [make_holding(instrument=make_instrument("AAA"))])
    return PortfolioSnapshot(reports=reports, fx=FxRate(1450.0, "PPI"),
                             transactions=[{"ticker": "AAA", "op": "BUY"}])


@pytest.fixture
def page():
    return HtmlDashboard(snapshot(), now=dt.datetime(2026, 8, 8, 14, 30)).render()


def embedded_data(html):
    return json.loads(re.search(r"^const DATA = (.*);$", html, re.M).group(1))


def test_no_placeholder_survives_the_render(page):
    for placeholder in ("__STYLES__", "__SCRIPT__", "__DATA_JSON__"):
        assert placeholder not in page


def test_the_page_is_self_contained(page):
    assert page.lstrip().startswith("<!DOCTYPE html>")
    assert "<style>" in page and "<script>" in page


def test_the_styles_are_inlined(page):
    assert ASSETS.joinpath("dashboard.css").read_text(encoding="utf-8").strip() in page


def a_verbatim_line(module):
    """The longest line of the module that the render does not substitute."""
    lines = ASSETS.joinpath("js", module).read_text(encoding="utf-8").splitlines()
    return max((line for line in lines if "__DATA_JSON__" not in line), key=len)


def test_every_script_module_is_inlined_in_order(page):
    """They are concatenated into a single <script>, and the tail of app.js
    only runs correctly once everything it calls has been defined."""
    positions = [page.index(a_verbatim_line(module)) for module in HtmlDashboard.JS_MODULES]
    assert positions == sorted(positions)


def test_the_data_is_embedded_as_json(page):
    data = embedded_data(page)
    assert data["fx_rate"] == 1450.0
    assert [row["key"] for row in data["markets"]["usd"]["rows"]] == ["AAA"]
    assert data["transactions"] == [{"ticker": "AAA", "op": "BUY"}]


def test_the_generation_time_is_embedded(page):
    assert embedded_data(page)["generated_at"] == "2026-08-08 14:30"


def test_accents_are_kept_readable_instead_of_escaped(page):
    assert "\\u00e1" not in page


def test_write_saves_the_rendered_page(tmp_path):
    path = tmp_path / "dashboard.html"
    HtmlDashboard(snapshot()).write(path)
    assert embedded_data(path.read_text(encoding="utf-8"))["fx_rate"] == 1450.0


def test_the_data_line_is_the_only_thing_that_changes_between_runs(tmp_path):
    """Everything else comes from the assets, so a diff of two dashboards shows
    only the data."""
    first = HtmlDashboard(snapshot(), now=dt.datetime(2026, 1, 1)).render()
    second = HtmlDashboard(snapshot(), now=dt.datetime(2026, 1, 1)).render()
    assert first == second
