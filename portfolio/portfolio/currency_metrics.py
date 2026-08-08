# -*- coding: utf-8 -*-
"""The metrics of a position, in one currency."""

from dataclasses import asdict, dataclass

from .position import EPSILON


@dataclass(frozen=True)
class CurrencyMetrics:
    """The same numbers are computed twice per position, once per currency: the
    dashboard shows ARS and USD and can switch between them without
    recomputing anything."""

    avg_cost: float = None
    price: float = None
    invested: float = None
    value: float = None
    pl_abs: float = None
    pl_pct: float = None
    cost_of_sales: float = None
    income_from_sales: float = None
    realized_abs: float = None
    realized_pct: float = None

    @classmethod
    def compute(cls, position, currency, units, price):
        invested = position.cost_basis[currency]
        cost_of_sales = position.cost_of_sales[currency]
        realized_abs = position.income_from_sales[currency] - cost_of_sales
        value = price * units if price is not None else None
        pl_abs = (value - invested) if value is not None else None
        return cls(
            avg_cost=invested / units if units > EPSILON else None,
            price=price,
            invested=invested,
            value=value,
            pl_abs=pl_abs,
            pl_pct=_percent(pl_abs, invested),
            cost_of_sales=cost_of_sales,
            income_from_sales=position.income_from_sales[currency],
            realized_abs=realized_abs,
            realized_pct=_percent(realized_abs, cost_of_sales),
        )

    def as_dict(self, currency):
        return {f"{field}_{currency}": value for field, value in asdict(self).items()}


def _percent(amount, base):
    return (amount / base * 100) if (amount is not None and base) else None
