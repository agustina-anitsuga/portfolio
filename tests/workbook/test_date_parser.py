# -*- coding: utf-8 -*-
import datetime as dt

import pytest

from portfolio_dashboard.workbook.date_parser import DateParser


@pytest.mark.parametrize("value, expected", [
    (dt.datetime(2025, 3, 15), (2025, 3, 15)),
    (dt.date(2025, 3, 15), (2025, 3, 15)),
    ("2026-11-06", (2026, 11, 6)),          # ISO
    ("30/09/2025", (2025, 9, 30)),          # local, day first
    ("30-09-2025", (2025, 9, 30)),
    ("30.09.2025", (2025, 9, 30)),
    ("2025-01-15 00:00:00", (2025, 1, 15)),  # time attached
    ("  2025-01-15  ", (2025, 1, 15)),
])
def test_parses_every_format_the_sheets_mix(value, expected):
    assert DateParser.parse(value) == expected


def test_a_text_date_starting_with_the_year_is_read_as_iso():
    """01/02 is ambiguous, the position of the 4-digit year resolves it."""
    assert DateParser.parse("2025-01-02") == (2025, 1, 2)
    assert DateParser.parse("01/02/2025") == (2025, 2, 1)


@pytest.mark.parametrize("value", [
    None, "", "   ", "sin fecha", "15/03", "31/13/2025", "32/01/2025", "15/03/99",
])
def test_unreadable_values_yield_nothing(value):
    assert DateParser.parse(value) is None


def test_a_two_digit_year_is_rejected_as_ambiguous():
    assert DateParser.parse("15/03/25") is None


def test_year_comes_back_as_text_to_match_the_html_select():
    assert DateParser.year("30/09/2025") == "2025"
    assert isinstance(DateParser.year(dt.datetime(2025, 1, 1)), str)


def test_year_of_an_unreadable_date_is_nothing():
    assert DateParser.year("sin fecha") is None


def test_iso_normalises_every_format_so_the_column_sorts_chronologically():
    assert DateParser.iso("30/09/2025") == "2025-09-30"
    assert DateParser.iso(dt.datetime(2025, 3, 5)) == "2025-03-05"


def test_iso_pads_single_digits():
    assert DateParser.iso("5/3/2025") == "2025-03-05"


def test_iso_of_an_empty_cell_is_an_empty_string():
    assert DateParser.iso(None) == ""


def test_iso_shows_an_unrecognised_value_as_it_came():
    """Better a visible oddity in the table than a silently dropped row."""
    assert DateParser.iso("proximamente") == "proximamente"


def test_iso_ordering_matches_chronological_ordering():
    dates = ["30/09/2025", "2026-01-05", dt.datetime(2025, 12, 31)]
    assert sorted(DateParser.iso(d) for d in dates) == ["2025-09-30", "2025-12-31", "2026-01-05"]
