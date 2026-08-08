# -*- coding: utf-8 -*-
import datetime as dt

import openpyxl

from doubles import USD_MARKET
from portfolio_dashboard.workbook.transaction_sheet import TransactionSheet


def workbook_with(rows, sheet_name="tx-usd"):
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    sheet = workbook.create_sheet(sheet_name)
    sheet.append(["Key", "Op", "Units", "Date", "Share Price", "Total USD", "Total ARS"])
    for row in rows:
        sheet.append(list(row))
    return workbook


def test_reads_the_rows_in_spreadsheet_order():
    workbook = workbook_with([
        ("BBB", "BUY", 1, dt.datetime(2026, 1, 1), 1.0, 1.0, 1000.0),
        ("AAA", "BUY", 2, dt.datetime(2025, 1, 1), 1.0, 2.0, 2000.0),
    ])
    assert [tx.ticker for tx in TransactionSheet(workbook, USD_MARKET).rows()] == ["BBB", "AAA"]


def test_chronological_puts_the_oldest_trade_first():
    """Average cost depends on the order: a sale processed before the purchases
    that supply it would be assigned a cost that does not exist yet."""
    workbook = workbook_with([
        ("AAA", "SELL", 1, "30/09/2026", 1.0, 1.0, 1000.0),
        ("AAA", "BUY", 2, "15/03/2025", 1.0, 2.0, 2000.0),
        ("AAA", "BUY", 2, dt.datetime(2025, 12, 1), 1.0, 2.0, 2000.0),
    ])
    dates = [tx.iso_date for tx in TransactionSheet(workbook, USD_MARKET).chronological()]
    assert dates == ["2025-03-15", "2025-12-01", "2026-09-30"]


def test_mixed_date_formats_still_sort_correctly():
    workbook = workbook_with([
        ("AAA", "BUY", 1, "2026-01-05", 1.0, 1.0, 1.0),
        ("AAA", "BUY", 1, "31/12/2025", 1.0, 1.0, 1.0),
    ])
    dates = [tx.iso_date for tx in TransactionSheet(workbook, USD_MARKET).chronological()]
    assert dates == ["2025-12-31", "2026-01-05"]


def test_rows_with_an_unreadable_date_go_last_keeping_their_order():
    workbook = workbook_with([
        ("AAA", "BUY", 1, None, 1.0, 1.0, 1.0),
        ("BBB", "BUY", 1, dt.datetime(2025, 1, 1), 1.0, 1.0, 1.0),
        ("CCC", "BUY", 1, None, 1.0, 1.0, 1.0),
    ])
    assert [tx.ticker for tx in TransactionSheet(workbook, USD_MARKET).chronological()] == \
        ["BBB", "AAA", "CCC"]


def test_rows_without_a_ticker_are_skipped():
    workbook = workbook_with([("AAA", "BUY", 1, None, 1.0, 1.0, 1.0), (None, "BUY", 1)])
    assert len(TransactionSheet(workbook, USD_MARKET).rows()) == 1


def test_a_missing_sheet_simply_has_no_trades():
    """A spreadsheet without RSU or bonds is perfectly valid."""
    workbook = workbook_with([], sheet_name="otra-hoja")
    assert TransactionSheet(workbook, USD_MARKET).rows() == []
    assert TransactionSheet(workbook, USD_MARKET).chronological() == []
