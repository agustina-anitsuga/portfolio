# -*- coding: utf-8 -*-
import openpyxl
import pytest

from portfolio.workbook.instrument_sheet import InstrumentSheet


def sheet_with(rows, name="instrumentos"):
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    sheet = workbook.create_sheet(name)
    sheet.append(["Key", "Nombre", "Tipo PPI", "Settlement PPI", "Ratio",
                  "Sector", "Moneda", "Precio Manual", "Tipo"])
    for row in rows:
        sheet.append(list(row))
    return workbook


def test_indexes_the_instruments_by_ticker():
    workbook = sheet_with([("AAA", "Alpha"), ("BBB", "Beta")])
    instruments = InstrumentSheet(workbook).read()
    assert sorted(instruments) == ["AAA", "BBB"]
    assert instruments["BBB"].name == "Beta"


def test_the_header_row_is_never_read_as_data():
    assert "Key" not in InstrumentSheet(sheet_with([])).read()


def test_rows_without_a_ticker_are_skipped():
    """Blank separator rows are common in hand-kept spreadsheets."""
    workbook = sheet_with([("AAA", "Alpha"), (None, "huerfano"), ("", "vacio")])
    assert list(InstrumentSheet(workbook).read()) == ["AAA"]


def test_a_missing_sheet_yields_no_instruments_instead_of_failing():
    workbook = sheet_with([], name="otra-hoja")
    assert InstrumentSheet(workbook).read() == {}


def test_the_last_row_wins_when_a_ticker_is_duplicated():
    workbook = sheet_with([("AAA", "Primero"), ("AAA", "Segundo")])
    assert InstrumentSheet(workbook).read()["AAA"].name == "Segundo"


@pytest.mark.parametrize("row, expected_ratio", [
    (("AAA", "Alpha", "CEDEARS", "A-48HS", 20), 20),
    (("AAA", "Alpha"), ""),
])
def test_optional_columns_may_be_absent(row, expected_ratio):
    assert InstrumentSheet(sheet_with([row])).read()["AAA"].ratio == expected_ratio
