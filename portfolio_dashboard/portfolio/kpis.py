# -*- coding: utf-8 -*-
"""Totals of a set of positions."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Kpis:
    """The numbers in the pills at the top of each tab. None (and not zero)
    when there is no data at all: that is the difference between "you invested
    nothing" and "nothing could be quoted"."""

    invested: float = None
    value: float = None
    pl_abs: float = None
    pl_pct: float = None
    realized: float = None

    @classmethod
    def from_holdings(cls, holdings, currency):
        metrics = [h.metrics[currency] for h in holdings]
        invested = _total(metrics, "invested")
        value = _total(metrics, "value")
        pl_abs = (value - invested) if (value is not None and invested is not None) else None
        return cls(
            invested=invested,
            value=value,
            pl_abs=pl_abs,
            pl_pct=(pl_abs / invested * 100) if (pl_abs is not None and invested) else None,
            realized=_total(metrics, "realized_abs"),
        )

    def as_dict(self):
        return asdict(self)


def _total(metrics, field):
    values = [getattr(m, field) for m in metrics if getattr(m, field) is not None]
    return sum(values) if values else None
