# -*- coding: utf-8 -*-
from portfolio_dashboard.workbook.row import cell, number


def test_cell_reads_the_requested_position():
    assert cell(("a", "b", "c"), 1) == "b"


def test_cell_returns_none_past_the_end_of_the_row():
    """Optional trailing columns simply are not there in shorter rows."""
    assert cell(("a",), 5) is None


def test_number_coerces_whatever_excel_handed_back():
    assert number((10, "20", 30.5), 1) == 20.0
    assert isinstance(number((10,), 0), float)


def test_number_keeps_none_as_none():
    """None means "not recorded", which is different from zero: it is what
    triggers the exchange rate approximation."""
    assert number((None,), 0) is None
    assert number((), 3) is None


def test_number_keeps_zero_as_zero():
    assert number((0,), 0) == 0.0
