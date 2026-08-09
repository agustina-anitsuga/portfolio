# -*- coding: utf-8 -*-
import openpyxl
import pytest

from doubles import USD_MARKET, make_holding, make_instrument
from portfolio.cli import DashboardCli, main
from portfolio.market import Market
from portfolio.marketdata.fx_rate import FxRate
from portfolio.portfolio.market_report import MarketReport
from portfolio.portfolio.snapshot import PortfolioSnapshot


class FakeApp:
    """Stands in for PortfolioApp: no spreadsheet and no market involved."""

    def __init__(self):
        self.asked_for = []
        self.watchlist_requested = []

    def snapshot(self, xlsx_path, with_watchlist=True):
        self.asked_for.append(xlsx_path)
        self.watchlist_requested.append(with_watchlist)
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


def test_a_successful_run_returns_zero(tmp_path, cli, capsys):
    dashboard, _ = cli
    assert dashboard.run(["portfolio.xlsx", "--out-html", str(tmp_path / "d.html")]) == 0


def test_the_html_output_has_a_default_name(tmp_path, monkeypatch, cli, capsys):
    dashboard, _ = cli
    monkeypatch.chdir(tmp_path)
    dashboard.run(["portfolio.xlsx"])
    assert (tmp_path / "Portfolio Dashboard.html").exists()


def test_the_spreadsheet_path_is_required(cli):
    dashboard, _ = cli
    with pytest.raises(SystemExit):
        dashboard.run([])


def test_main_builds_the_real_app_by_default(tmp_path, monkeypatch, capsys):
    """Only the wiring is checked here; the app itself is tested separately."""
    import portfolio.cli as module
    monkeypatch.setattr(module, "PortfolioApp", FakeApp)
    assert main(["portfolio.xlsx", "--out-html", str(tmp_path / "d.html")]) == 0
