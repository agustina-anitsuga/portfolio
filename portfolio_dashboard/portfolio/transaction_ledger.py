# -*- coding: utf-8 -*-
"""The rows of the "Transacciones" tab."""

from ..market import CURRENCIES

NO_PRICE = {"current_price_ars": None, "current_price_usd": None,
            "current_price_source": "no disponible"}


class TransactionLedger:
    """One row per trade (not aggregated), with today's quote next to it so it
    can be compared against the price the trade was made at. The prices come
    from the reports already computed: it makes no extra request."""

    def __init__(self, transactions, reports):
        self._transactions = transactions
        self._current_prices = self._price_lookup(reports)

    @staticmethod
    def _price_lookup(reports):
        return {row["key"]: {"current_price_ars": row["price_ars"],
                             "current_price_usd": row["price_usd"],
                             "current_price_source": row["price_source"]}
                for report in reports.values() for row in report.rows}

    def rows(self):
        rows = [self._row(tx) for tx in self._transactions if tx.op]
        rows.sort(key=lambda r: (r["date"] or "", r["ticker"]), reverse=True)
        return rows

    def _row(self, tx):
        row = tx.as_dict()
        row.update(self._current_prices.get(tx.ticker, NO_PRICE))
        for currency in CURRENCIES:
            row[f"pl_pct_{currency}"] = self._pl_pct(tx, row, currency)
        return row

    @staticmethod
    def _pl_pct(tx, row, currency):
        """P&L % of that single trade: the price it was bought at against
        today's quote.

        Only purchases have one. On a sale the position is already closed, so
        comparing the sale price against today's quote would not be a result:
        it would be a what-if of having held on.
        """
        if not tx.is_buy:
            return None
        price = row[f"price_{currency}"]
        current = row[f"current_price_{currency}"]
        return (current - price) / price * 100 if (price and current is not None) else None
