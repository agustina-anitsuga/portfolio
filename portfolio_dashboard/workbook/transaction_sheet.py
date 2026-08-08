# -*- coding: utf-8 -*-
"""tx-* sheets (one per instrument type)."""

from .transaction import Transaction


class TransactionSheet:
    """The trades of one market. The sheet may not exist (for instance a
    spreadsheet with no RSU and no bonds): in that case there simply are no
    trades."""

    def __init__(self, workbook, market):
        self._workbook = workbook
        self._market = market

    def rows(self):
        """In the order they are entered in the spreadsheet."""
        if self._market.sheet not in self._workbook.sheetnames:
            return []
        sheet = self._workbook[self._market.sheet]
        return [Transaction.from_row(self._market, row)
                for row in sheet.iter_rows(min_row=2, values_only=True) if row and row[0]]

    def chronological(self):
        """Sorted by date, which is how they have to be processed.

        Average cost depends on the order: a sale has to be processed AFTER the
        purchases that supply it, otherwise it gets assigned a cost that does
        not exist yet. The sheets are not always sorted by date (tx-cedears is
        not). Rows with an unreadable date go last, in the order they were in.
        """
        return sorted(self.rows(), key=lambda tx: (tx.iso_date == "", tx.iso_date))
