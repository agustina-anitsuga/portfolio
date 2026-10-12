# -*- coding: utf-8 -*-
""""config" sheet."""

SHEET = "config"
MANUAL_FX_LABEL = "usd/ars"
MANUAL_CCL_LABEL = "ccl"


class ConfigSheet:
    """Loose parameters of the spreadsheet. For now only the manual exchange
    rate, used as a fallback when PPI cannot compute the MEP dollar."""

    def __init__(self, workbook):
        self._workbook = workbook

    def manual_fx(self):
        return self._value_of(MANUAL_FX_LABEL)

    def manual_ccl(self):
        """Fallback for the CCL dollar, used when PPI cannot compute it."""
        return self._value_of(MANUAL_CCL_LABEL)

    def _value_of(self, label):
        if SHEET not in self._workbook.sheetnames:
            return None
        value = None
        for row in self._workbook[SHEET].iter_rows(min_row=2, values_only=True):
            if row and row[0] and label in str(row[0]).lower():
                value = row[1]
        return value
