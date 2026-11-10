# -*- coding: utf-8 -*-
import datetime as dt
from contextlib import contextmanager

import openpyxl
import pytest

from doubles import USD_MARKET, make_holding, make_instrument
from portfolio.cli import DashboardCli, main
from portfolio.market import Market
from portfolio.marketdata.fx_rate import FxRate
from portfolio.portfolio.market_report import MarketReport
from portfolio.portfolio.snapshot import PortfolioSnapshot
from portfolio.settings import Settings


class FakeApp:
    """Stands in for PortfolioApp: no spreadsheet and no market involved."""

    def __init__(self, settings=None):
        self.asked_for = []
        self.watchlist_requested = []
        self.annual_requested = []

    def snapshot(self, xlsx_path, with_watchlist=True, with_annual=True):
        self.asked_for.append(xlsx_path)
        self.watchlist_requested.append(with_watchlist)
        self.annual_requested.append(with_annual)
        reports = {key: MarketReport(Market.get(key), []) for key in Market.keys()}
        reports["usd"] = MarketReport(USD_MARKET, [make_holding(instrument=make_instrument("AAA"))])
        return PortfolioSnapshot(reports=reports, fx=FxRate(1450.0, "PPI"))


@pytest.fixture
def cli():
    app = FakeApp()
    return DashboardCli(app=app), app


def test_the_html_is_written_where_asked(tmp_path, cli, capsys):
    dashboard, _ = cli
    out = tmp_path / "dashboard.html"
    dashboard.run(["portfolio.xlsx", "--out-html", str(out)])
    assert out.exists()
    assert "const DATA" in out.read_text(encoding="utf-8")


def test_the_spreadsheet_argument_reaches_the_app(tmp_path, cli, capsys):
    dashboard, app = cli
    dashboard.run(["mi-planilla.xlsx", "--out-html", str(tmp_path / "d.html")])
    assert app.asked_for == ["mi-planilla.xlsx"]


def test_the_excel_is_optional(tmp_path, cli, capsys):
    dashboard, _ = cli
    dashboard.run(["portfolio.xlsx", "--out-html", str(tmp_path / "d.html")])
    assert list(tmp_path.glob("*.xlsx")) == []


def test_the_excel_is_written_when_requested(tmp_path, cli, capsys):
    dashboard, _ = cli
    out = tmp_path / "out.xlsx"
    dashboard.run(["portfolio.xlsx", "--out-html", str(tmp_path / "d.html"), "--out-xlsx", str(out)])
    assert "dashboard-general" in openpyxl.load_workbook(out).sheetnames


def test_the_summary_lists_only_the_files_actually_generated(tmp_path, cli, capsys):
    dashboard, _ = cli
    dashboard.run(["portfolio.xlsx", "--out-html", str(tmp_path / "d.html")])
    output = capsys.readouterr().out
    assert output.count("Listo:") == 1
    assert "1 posiciones procesadas" in output


def test_the_watchlist_is_computed_by_default(tmp_path, cli, capsys):
    dashboard, app = cli
    dashboard.run(["portfolio.xlsx", "--out-html", str(tmp_path / "d.html")])
    assert app.watchlist_requested == [True]


def test_no_watchlist_skips_it(tmp_path, cli, capsys):
    """It is the slowest part of a run and says nothing about the portfolio."""
    dashboard, app = cli
    dashboard.run(["portfolio.xlsx", "--out-html", str(tmp_path / "d.html"), "--no-watchlist"])
    assert app.watchlist_requested == [False]


def test_the_annual_tab_is_computed_by_default(tmp_path, cli, capsys):
    dashboard, app = cli
    dashboard.run(["portfolio.xlsx", "--out-html", str(tmp_path / "d.html")])
    assert app.annual_requested == [True]


def test_no_annual_skips_it(tmp_path, cli, capsys):
    dashboard, app = cli
    dashboard.run(["portfolio.xlsx", "--out-html", str(tmp_path / "d.html"), "--no-annual"])
    assert app.annual_requested == [False]


def test_a_successful_run_returns_zero(tmp_path, cli, capsys):
    dashboard, _ = cli
    assert dashboard.run(["portfolio.xlsx", "--out-html", str(tmp_path / "d.html")]) == 0


def test_the_html_output_has_a_default_name(tmp_path, monkeypatch, cli, capsys):
    dashboard, _ = cli
    monkeypatch.chdir(tmp_path)
    dashboard.run(["portfolio.xlsx"])
    assert (tmp_path / "Portfolio Dashboard.html").exists()


class FakeSheet:
    """Stands in for GoogleSheet: hands out a fixed path, no network."""

    def __init__(self):
        self.modified_time = dt.datetime(2026, 11, 10, 14, 32)
        self.downloads = 0

    @contextmanager
    def downloaded(self):
        self.downloads += 1
        yield "/tmp/drive-export.xlsx"


def test_without_a_path_the_spreadsheet_comes_from_drive(tmp_path, capsys):
    app, sheet = FakeApp(), FakeSheet()
    DashboardCli(app=app, settings=Settings(), sheet=sheet).run(
        ["--out-html", str(tmp_path / "d.html")])
    assert sheet.downloads == 1
    assert app.asked_for == ["/tmp/drive-export.xlsx"]
    assert "editada el 10/11/2026 14:32" in capsys.readouterr().out


def test_a_local_path_never_touches_drive(tmp_path, capsys):
    app, sheet = FakeApp(), FakeSheet()
    DashboardCli(app=app, settings=Settings(), sheet=sheet).run(
        ["portfolio.xlsx", "--out-html", str(tmp_path / "d.html")])
    assert sheet.downloads == 0
    assert "Google Drive" not in capsys.readouterr().out


def test_drive_without_configuration_fails_with_a_clear_message(tmp_path, capsys):
    out = tmp_path / "d.html"
    code = DashboardCli(app=FakeApp(), settings=Settings()).run(["--out-html", str(out)])
    assert code == 1
    assert "PORTFOLIO_SHEET_ID" in capsys.readouterr().err
    assert not out.exists()


def test_main_builds_the_real_app_by_default(tmp_path, monkeypatch, capsys):
    """Only the wiring is checked here; the app itself is tested separately."""
    import portfolio.cli as module
    monkeypatch.setattr(module, "PortfolioApp", FakeApp)
    assert main(["portfolio.xlsx", "--out-html", str(tmp_path / "d.html")]) == 0
