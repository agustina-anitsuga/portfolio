# -*- coding: utf-8 -*-
import openpyxl

from portfolio_dashboard.output.excel_style import ExcelStyle


def a_sheet():
    workbook = openpyxl.Workbook()
    return workbook.active


def test_header_paints_the_cell_dark_with_white_bold_text():
    cell = a_sheet()["A1"]
    ExcelStyle.header(cell)
    assert cell.fill.fgColor.rgb == "001F2937"
    assert cell.font.bold is True
    assert cell.font.color.rgb == "00FFFFFF"


def test_header_can_wrap_and_centre_long_titles():
    cell = a_sheet()["A1"]
    ExcelStyle.header(cell, wrap=True)
    assert cell.alignment.wrap_text is True
    assert cell.alignment.horizontal == "center"


def test_header_does_not_wrap_by_default():
    cell = a_sheet()["A1"]
    ExcelStyle.header(cell)
    assert not cell.alignment.wrap_text


def test_the_semaphore_adds_a_green_and_a_red_rule():
    sheet = a_sheet()
    ExcelStyle.pl_semaphore(sheet, "E2:E10")
    rules = sheet.conditional_formatting["E2:E10"]
    assert len(rules) == 2
    assert {rule.operator for rule in rules} == {"greaterThanOrEqual", "lessThan"}


def test_the_semaphore_splits_at_zero():
    sheet = a_sheet()
    ExcelStyle.pl_semaphore(sheet, "E2:E10")
    assert all(rule.formula == ["0"] for rule in sheet.conditional_formatting["E2:E10"])
