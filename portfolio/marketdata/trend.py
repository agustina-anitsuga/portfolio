# -*- coding: utf-8 -*-
"""30-day trend of an instrument."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Trend:
    """Percentage change and the price series that draws the dashboard line."""

    pct: float = None
    series: list = field(default_factory=list)

    @classmethod
    def empty(cls):
        return cls(None, [])

    @classmethod
    def from_series(cls, prices):
        """None when the series cannot yield a variation.

        Prices are rounded so the JSON embedded in the HTML does not blow up,
        and the percentage is computed AFTER rounding so the number in the
        tooltip is exactly the one at the ends of the line being drawn.
        """
        prices = [round(p, 4) for p in prices]
        if not prices[0]:
            return None
        return cls((prices[-1] - prices[0]) / prices[0] * 100, prices)
