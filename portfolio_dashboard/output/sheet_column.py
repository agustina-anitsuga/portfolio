# -*- coding: utf-8 -*-
"""Definition of an Excel column."""

from dataclasses import dataclass

PERCENT_FORMAT = "0.00%"
MONEY_FORMAT = "#,##0.00"


@dataclass(frozen=True)
class SheetColumn:
    key: str
    header: str
    width: int
    number_format: str = None

    @property
    def is_percent(self):
        return self.number_format == PERCENT_FORMAT

    def cell_value(self, row):
        """Excel expects percentages as a fraction, everything else as is."""
        value = row.get(self.key)
        if self.is_percent and value is not None:
            return value / 100.0
        return value
