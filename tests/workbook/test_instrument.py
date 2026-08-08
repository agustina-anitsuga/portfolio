# -*- coding: utf-8 -*-
from portfolio_dashboard.workbook.instrument import Instrument

FULL_ROW = ("AAA", "Alpha Corp", "CEDEARS", "A-48HS", 20, "Technology", "USD", 1500.0, "Stock")


def test_reads_every_column_of_the_row():
    instrument = Instrument.from_row(FULL_ROW)
    assert instrument.key == "AAA"
    assert instrument.name == "Alpha Corp"
    assert instrument.ppi_type == "CEDEARS"
    assert instrument.settlement == "A-48HS"
    assert instrument.ratio == 20
    assert instrument.sector == "Technology"
    assert instrument.currency == "USD"
    assert instrument.manual_price == 1500.0
    assert instrument.instrument_type == "Stock"


def test_an_empty_name_falls_back_to_the_ticker():
    assert Instrument.from_row(("AAA", None)).name == "AAA"


def test_missing_optional_columns_become_empty_text():
    instrument = Instrument.from_row(("AAA",))
    assert instrument.ppi_type == ""
    assert instrument.settlement == ""
    assert instrument.sector == ""
    assert instrument.instrument_type == ""


def test_a_missing_manual_price_stays_none_rather_than_zero():
    """None means "no manual price"; a zero would be used as a real price."""
    assert Instrument.from_row(("AAA",)).manual_price is None


def test_an_unknown_ticker_is_still_displayable():
    """Tickers traded but absent from the instruments sheet must not vanish."""
    instrument = Instrument.unknown("ZZZ")
    assert instrument.key == "ZZZ"
    assert instrument.name == "ZZZ"
    assert instrument.manual_price is None
    assert instrument.ppi_type == ""
