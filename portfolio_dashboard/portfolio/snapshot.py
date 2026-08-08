# -*- coding: utf-8 -*-
"""The whole portfolio, already computed."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PortfolioSnapshot:
    """Everything the renderers need: the full reports, the same set recomputed
    for every year with purchases, the exchange rate used and the trades."""

    reports: dict
    reports_by_year: dict = field(default_factory=dict)
    fx: object = None
    transactions: list = field(default_factory=list)

    @property
    def years(self):
        return sorted(self.reports_by_year, reverse=True)

    def report(self, market_key):
        return self.reports[market_key]

    def all_rows(self):
        return [row for report in self.reports.values() for row in report.rows]

    def unpriced_rows(self):
        return [row for row in self.all_rows()
                if row["value_ars"] is None and row["value_usd"] is None]

    @property
    def position_count(self):
        return sum(len(report.rows) for report in self.reports.values())
