# -*- coding: utf-8 -*-
"""Builds the positions by walking the trades in chronological order."""

from ..market import Market
from ..workbook.transaction import BUY, SELL
from .position import Position


class PositionTracker:
    """Average cost tracking BOTH currencies at once, trade by trade.

    When a trade has the real amount recorded in the other currency (cedears
    always carry @Local and @Origin; Merval carries ARS and USD as of the day
    of the trade), that real historical amount is used: no approximation
    involved. Only when it is missing (typically old tx-usd rows that were
    never recorded in ARS) is THAT trade converted at TODAY's exchange rate,
    and the position gets flagged so the dashboard can say so.

    `scope_year` does not filter the history: it is walked in full anyway, and
    only the trades of that year are reported. That is why the numbers of each
    year add up exactly to the total portfolio.
    """

    def __init__(self, fx, scope_year=None):
        self._fx = fx
        self._scope_year = scope_year

    def track_all(self, workbook):
        return {market.key: self.track(workbook.transactions(market)) for market in Market.all()}

    def track(self, transactions):
        positions = {}
        for tx in transactions:
            if not tx.op or tx.units is None:
                continue
            position = positions.setdefault(tx.ticker, Position())
            self._apply(position, tx)
        return positions

    def _apply(self, position, tx):
        amounts = self._amounts(position, tx)
        in_scope = self._scope_year is None or tx.year == self._scope_year
        if tx.op == BUY:
            position.buy(tx.units, amounts, tx.year, in_scope)
        elif tx.op == SELL:
            position.sell(tx.units, amounts, in_scope)

    def _amounts(self, position, tx):
        """The amount of the trade in both currencies, approximating only when
        needed (and flagging the position when it does)."""
        native, other = tx.market.native_currency, tx.market.other_currency
        native_amount = tx.amount(native) or 0.0
        other_amount = tx.amount(other)
        if other_amount is None:
            position.approximated = True
            other_amount = self._fx.convert(native_amount, other) if self._fx else 0.0
        return {native: native_amount, other: other_amount}
