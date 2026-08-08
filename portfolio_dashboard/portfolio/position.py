# -*- coding: utf-8 -*-
"""The position of a ticker, by average cost and in both currencies."""

from ..market import CURRENCIES

EPSILON = 1e-9


class Position:
    """It keeps two states in parallel.

    The REAL state (`_real_*`) advances with every trade of the whole history:
    that is where average cost comes from, so a 2026 sale of units bought in
    2025 is valued at the real cost of those units.

    The REPORTED state (everything else) only accumulates the trades that fall
    inside the requested scope -- everything, or a single year.
    """

    def __init__(self):
        self.units = 0.0
        self.units_sold = 0.0
        self.cost_basis = _zero()
        self.cost_of_sales = _zero()
        self.income_from_sales = _zero()
        self.oversold = False
        self.approximated = False
        self._real_units = 0.0
        self._real_cost = _zero()
        self._buy_years = set()

    @property
    def buy_years(self):
        return sorted(self._buy_years)

    @property
    def dual_real(self):
        """True when every amount came from the spreadsheet; False when some
        trade was converted at today's exchange rate as an approximation."""
        return not self.approximated

    @property
    def is_empty(self):
        return self.units <= EPSILON and self.units_sold <= EPSILON

    @property
    def reported_units(self):
        return max(self.units, 0.0)

    def buy(self, units, amounts, year, in_scope):
        self._real_units += units
        for currency in CURRENCIES:
            self._real_cost[currency] += amounts[currency]
        if year:
            self._buy_years.add(year)
        if not in_scope:
            return
        self.units += units
        for currency in CURRENCIES:
            self.cost_basis[currency] += amounts[currency]

    def sell(self, units, amounts, in_scope):
        if units > self._real_units + EPSILON:
            self.oversold = True   # more units sold than were ever bought
        cost = {c: self._average_cost(c) * units for c in CURRENCIES}
        self._real_units -= units
        for currency in CURRENCIES:
            self._real_cost[currency] -= cost[currency]
        if not in_scope:
            return
        self.units -= units
        self.units_sold += units
        for currency in CURRENCIES:
            self.cost_basis[currency] -= cost[currency]
            self.cost_of_sales[currency] += cost[currency]
            self.income_from_sales[currency] += amounts[currency]

    def _average_cost(self, currency):
        """REAL average cost at this point of the history."""
        if self._real_units <= EPSILON:
            return 0.0
        return self._real_cost[currency] / self._real_units


def _zero():
    return {currency: 0.0 for currency in CURRENCIES}
