# -*- coding: utf-8 -*-
import openpyxl

from portfolio.workbook.contribution_sheet import ContributionSheet

ALLOCATION = [("SCHD", 35, "CCL"), ("SPY", 40, "ARS"), ("SGOV", 15, "CCL"), ("XLU", 10, "ARS")]


def sheet_with(rows, name="aporte"):
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    sheet = workbook.create_sheet(name)
    for row in rows:
        sheet.append(list(row))
    return workbook


def full_sheet(allocation=ALLOCATION, monthly=4000000):
    return sheet_with([("A", "B", "C"), ("Monto mensual ARS", monthly), ("Ticker", "%", "Moneda"), *allocation])


def test_reads_the_monthly_amount_and_the_allocation():
    plan = ContributionSheet(full_sheet()).plan()
    assert plan["monthly_ars"] == 4000000
    assert [(r["ticker"], r["pct"], r["currency"]) for r in plan["rows"]] == [
        ("SCHD", 35, "CCL"), ("SPY", 40, "ARS"), ("SGOV", 15, "CCL"), ("XLU", 10, "ARS")]


def test_headers_and_notes_are_ignored():
    plan = ContributionSheet(sheet_with([("Monto mensual", 100), ("Ticker", "%", "Moneda"), ("nota suelta",),
                                         ("SPY", 100, "ARS")])).plan()
    assert [r["ticker"] for r in plan["rows"]] == ["SPY"]


def test_the_currency_is_case_insensitive():
    plan = ContributionSheet(full_sheet([("SCHD", 100, " ccl ")])).plan()
    assert plan["rows"][0]["currency"] == "CCL"


def test_percent_formatted_cells_are_read_as_percentages():
    plan = ContributionSheet(full_sheet([("SCHD", 0.6, "CCL"), ("SPY", 0.4, "ARS")])).plan()
    assert [r["pct"] for r in plan["rows"]] == [60, 40]


def test_a_row_with_an_unknown_currency_is_skipped():
    plan = ContributionSheet(full_sheet([("SCHD", 50, "EUR"), ("SPY", 50, "ARS")])).plan()
    assert [r["ticker"] for r in plan["rows"]] == ["SPY"]


def test_without_the_amount_there_is_no_plan():
    assert ContributionSheet(sheet_with([("SPY", 100, "ARS")])).plan() is None


def test_a_missing_sheet_is_not_an_error():
    assert ContributionSheet(sheet_with([], name="otra")).plan() is None
