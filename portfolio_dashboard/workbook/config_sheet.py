# -*- coding: utf-8 -*-
""""config" sheet."""

SHEET = "config"
MANUAL_FX_LABEL = "usd/ars"


class ConfigSheet:
    """Loose parameters of the spreadsheet. For now only the manual exchange
    rate, used as a fallback when PPI cannot compute the MEP dollar."""

    def __init__(self, workbook):
        self._workbook = workbook

    def manual_fx(self):
        if SHEET not in self._workbook.sheetnames:
            return None
        manual_fx = None
        for row in self._workbook[SHEET].iter_rows(min_row=2, values_only=True):
            if row and row[0] and MANUAL_FX_LABEL in str(row[0]).lower():
                manual_fx = row[1]
        return manual_fx
