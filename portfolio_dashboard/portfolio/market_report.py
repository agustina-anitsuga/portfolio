# -*- coding: utf-8 -*-
"""The report of one tab: its positions already sorted, plus its totals."""

from ..market import ARS, CURRENCIES, USD
from .kpis import Kpis


class MarketReport:
    """The positions of a market, sorted from largest to smallest value and
    with the weight of each one over the tab total already computed."""

    def __init__(self, market, holdings):
        self.market = market
        self.holdings = sorted(holdings, key=_by_value_desc)
        self._assign_portfolio_shares()
        self._rows = None

    def _assign_portfolio_shares(self):
        for currency in CURRENCIES:
            total = sum(h.value(currency) for h in self.holdings if h.value(currency) is not None)
            for holding in self.holdings:
                value = holding.value(currency)
                share = (value / total * 100) if (value is not None and total) else None
                holding.set_portfolio_share(currency, share)

    @property
    def rows(self):
        if self._rows is None:
            self._rows = [h.as_dict() for h in self.holdings]
        return self._rows

    def kpis(self, currency):
        return Kpis.from_holdings(self.holdings, currency)

    @property
    def unpriced_count(self):
        return sum(1 for h in self.holdings if h.unpriced)

    def kpis_payload(self):
        payload = {c: self.kpis(c).as_dict() for c in CURRENCIES}
        payload["unpriced"] = self.unpriced_count
        return payload


def _by_value_desc(holding):
    """Positions without a price in either currency go last."""
    return (holding.unpriced, -(holding.value(ARS) or holding.value(USD) or 0))
