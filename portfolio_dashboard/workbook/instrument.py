# -*- coding: utf-8 -*-
"""One row of the "instrumentos" sheet."""

from dataclasses import dataclass

from .row import cell


@dataclass(frozen=True)
class Instrument:
    """Metadata of a ticker: how to ask PPI for it and how to display it."""

    key: str
    name: str = ""
    ppi_type: str = ""
    settlement: str = ""
    ratio: str = ""
    sector: str = ""
    currency: str = ""
    manual_price: float = None
    instrument_type: str = ""

    @classmethod
    def from_row(cls, row):
        return cls(
            key=row[0],
            name=cell(row, 1) or row[0],
            ppi_type=cell(row, 2) or "",
            settlement=cell(row, 3) or "",
            ratio=cell(row, 4) or "",
            sector=cell(row, 5) or "",
            currency=cell(row, 6) or "",
            manual_price=cell(row, 7),
            instrument_type=cell(row, 8) or "",
        )

    @classmethod
    def unknown(cls, key):
        """A ticker that shows up in the transactions but not in the
        instruments sheet: it is still displayed, just without metadata."""
        return cls(key=key, name=key)
