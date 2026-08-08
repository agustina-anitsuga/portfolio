# -*- coding: utf-8 -*-
import openpyxl

from portfolio.workbook.config_sheet import ConfigSheet


def config_with(rows, name="config"):
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    sheet = workbook.create_sheet(name)
    sheet.append(["Parametro", "Valor", "Notas"])
    for row in rows:
        sheet.append(list(row))
    return workbook


def test_reads_the_manual_exchange_rate():
    assert ConfigSheet(config_with([("USD/ARS Manual (respaldo)", 1450.0)])).manual_fx() == 1450.0


def test_the_label_is_matched_regardless_of_case_and_wording():
    assert ConfigSheet(config_with([("Dolar usd/ars de respaldo", 1200.0)])).manual_fx() == 1200.0


def test_other_parameters_are_ignored():
    workbook = config_with([("Otro parametro", 5), ("USD/ARS Manual", 1300.0), ("Mas", 7)])
    assert ConfigSheet(workbook).manual_fx() == 1300.0


def test_an_empty_value_reads_as_nothing():
    assert ConfigSheet(config_with([("USD/ARS Manual", None)])).manual_fx() is None


def test_without_the_row_there_is_no_manual_rate():
    assert ConfigSheet(config_with([("Otro", 1)])).manual_fx() is None


def test_a_missing_config_sheet_is_not_an_error():
    """The sheet is optional: PPI is the primary source anyway."""
    assert ConfigSheet(config_with([], name="otra")).manual_fx() is None


def test_the_last_matching_row_wins():
    workbook = config_with([("USD/ARS viejo", 1000.0), ("USD/ARS Manual", 1450.0)])
    assert ConfigSheet(workbook).manual_fx() == 1450.0
