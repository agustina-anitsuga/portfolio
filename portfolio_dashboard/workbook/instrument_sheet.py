# -*- coding: utf-8 -*-
""""instrumentos" sheet."""

from .instrument import Instrument

SHEET = "instrumentos"


class InstrumentSheet:
    """The metadata of every ticker, indexed by Key."""

    def __init__(self, workbook):
        self._workbook = workbook

    def read(self):
        if SHEET not in self._workbook.sheetnames:
            return {}
        rows = self._workbook[SHEET].iter_rows(min_row=2, values_only=True)
        return {row[0]: Instrument.from_row(row) for row in rows if row and row[0]}
