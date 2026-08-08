# -*- coding: utf-8 -*-
import datetime as dt

from doubles import USD_MARKET, write_workbook
from portfolio_dashboard.market import Market
from portfolio_dashboard.workbook.portfolio_workbook import PortfolioWorkbook


def test_exposes_instruments_and_the_manual_rate(workbook_path):
    workbook = PortfolioWorkbook(workbook_path)
    assert workbook.instruments["AAA"].name == "Alpha Corp"
    assert workbook.manual_fx == 1000.0


def test_transactions_of_a_market_come_back_chronological(workbook_path):
    dates = [tx.iso_date for tx in PortfolioWorkbook(workbook_path).transactions(USD_MARKET)]
    assert dates == sorted(dates)


def test_all_transactions_covers_every_market(tmp_path):
    path = write_workbook(
        tmp_path / "p.xlsx",
        sheets={
            "tx-usd": [("AAA", "BUY", 1, dt.datetime(2025, 1, 1), 1.0, 10.0, 10000.0)],
            "tx-merval": [("YPFD", "BUY", 1, dt.datetime(2025, 1, 2), 1.0, 20000.0, 20.0)],
            "tx-bonds": [("AO28", "BUY", 1, dt.datetime(2025, 1, 3), 1.0, 30000.0, 30.0)],
        },
    )
    tickers = [tx.ticker for tx in PortfolioWorkbook(path).all_transactions()]
    assert tickers == ["AAA", "YPFD", "AO28"]


def test_an_unknown_ticker_still_gets_an_instrument(workbook_path):
    """Otherwise a trade of a ticker missing from the sheet would crash."""
    instrument = PortfolioWorkbook(workbook_path).instrument("ZZZ")
    assert instrument.key == "ZZZ"
    assert instrument.name == "ZZZ"


def test_missing_transaction_sheets_are_treated_as_empty(tmp_path):
    path = write_workbook(tmp_path / "p.xlsx", skip=("tx-rsu", "tx-bonds"))
    workbook = PortfolioWorkbook(path)
    assert workbook.transactions(Market.get("rsu")) == []
    assert workbook.transactions(Market.get("bonds")) == []


def test_every_market_has_an_entry_even_when_the_sheet_is_absent(tmp_path):
    path = write_workbook(tmp_path / "p.xlsx", skip=("tx-rsu",))
    workbook = PortfolioWorkbook(path)
    for market in Market.all():
        assert isinstance(workbook.transactions(market), list)


def test_the_file_is_read_once_and_kept_in_memory(workbook_path):
    """The per-year recalculation reuses this, so it must not hit the disk."""
    workbook = PortfolioWorkbook(workbook_path)
    first = workbook.transactions(USD_MARKET)
    assert workbook.transactions(USD_MARKET) is first
