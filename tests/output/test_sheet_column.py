# -*- coding: utf-8 -*-
import pytest

from portfolio.output.sheet_column import MONEY_FORMAT, PERCENT_FORMAT, SheetColumn


def test_a_percent_column_is_recognised_by_its_format():
    assert SheetColumn("pl_pct_ars", "P&L %", 12, PERCENT_FORMAT).is_percent is True
    assert SheetColumn("invested_ars", "Invertido", 12, MONEY_FORMAT).is_percent is False
    assert SheetColumn("key", "Ticker", 10).is_percent is False


def test_percentages_are_handed_to_excel_as_a_fraction():
    """Excel multiplies by 100 when it applies the 0.00% format."""
    column = SheetColumn("pl_pct_ars", "P&L %", 12, PERCENT_FORMAT)
    assert column.cell_value({"pl_pct_ars": 15.5}) == pytest.approx(0.155)


def test_other_values_go_through_untouched():
    column = SheetColumn("invested_ars", "Invertido", 12, MONEY_FORMAT)
    assert column.cell_value({"invested_ars": 1234.5}) == 1234.5


def test_a_missing_percentage_stays_empty_instead_of_becoming_zero():
    column = SheetColumn("pl_pct_ars", "P&L %", 12, PERCENT_FORMAT)
    assert column.cell_value({"pl_pct_ars": None}) is None


def test_a_key_absent_from_the_row_leaves_the_cell_empty():
    assert SheetColumn("value_ars", "Valor", 12, MONEY_FORMAT).cell_value({}) is None
