# -*- coding: utf-8 -*-
import openpyxl

from portfolio.workbook.watchlist_sheet import WatchlistSheet


def sheet_with(rows, name="watchlist"):
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    sheet = workbook.create_sheet(name)
    sheet.append(["Ticker", "Notas"])
    for row in rows:
        sheet.append(list(row))
    return workbook


def test_reads_the_tickers_in_the_order_of_the_sheet():
    workbook = sheet_with([("AAPL",), ("GOOGL",), ("SPY",)])
    assert WatchlistSheet(workbook).tickers() == ["AAPL", "GOOGL", "SPY"]


def test_the_header_is_not_a_ticker():
    assert "Ticker" not in WatchlistSheet(sheet_with([])).tickers()


def test_empty_rows_are_skipped():
    workbook = sheet_with([("AAPL",), (None,), ("",), ("  ",), ("GOOGL",)])
    assert WatchlistSheet(workbook).tickers() == ["AAPL", "GOOGL"]


def test_surrounding_spaces_are_trimmed():
    assert WatchlistSheet(sheet_with([("  AAPL  ",)])).tickers() == ["AAPL"]


def test_a_repeated_ticker_is_listed_once():
    """Otherwise it would be quoted twice and shown twice."""
    workbook = sheet_with([("AAPL",), ("GOOGL",), ("AAPL",)])
    assert WatchlistSheet(workbook).tickers() == ["AAPL", "GOOGL"]


def test_the_other_columns_are_free_for_your_notes():
    workbook = sheet_with([("AAPL", "mirar despues del balance")])
    assert WatchlistSheet(workbook).tickers() == ["AAPL"]


def test_a_spreadsheet_without_the_sheet_simply_has_no_watchlist():
    assert WatchlistSheet(sheet_with([], name="otra")).tickers() == []
