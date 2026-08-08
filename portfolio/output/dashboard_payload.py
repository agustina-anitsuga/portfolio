# -*- coding: utf-8 -*-
"""The JSON embedded in the dashboard."""

import datetime as dt

from ..market import Market


class DashboardPayload:
    """What the HTML reads as `DATA`: for every market its rows and KPIs, plus
    the same set recomputed per year, the trades and the exchange rate."""

    def __init__(self, snapshot, now=None):
        self._snapshot = snapshot
        self._now = now or dt.datetime.now()

    def as_dict(self):
        return {
            "markets": {m.key: self._market(m) for m in Market.all()},
            "general": self._general(),
            "transactions": self._snapshot.transactions,
            "years": self._snapshot.years,
            "fx_rate": self._snapshot.fx.value,
            "fx_source": self._snapshot.fx.source,
            "generated_at": self._now.strftime("%Y-%m-%d %H:%M"),
        }

    def _market(self, market):
        report = self._snapshot.report(market.key)
        by_year = self._snapshot.reports_by_year
        return {
            "label": market.label,
            "kpis": report.kpis_payload(),
            "rows": report.rows,
            # same content as "rows"/"kpis" but recomputed with only the trades
            # of each year; the year filter swaps the whole set.
            "rows_by_year": {y: by_year[y][market.key].rows for y in by_year},
            "kpis_by_year": {y: by_year[y][market.key].kpis_payload() for y in by_year},
        }

    def _general(self):
        rows = self._snapshot.all_rows()
        rows.sort(key=lambda r: (r["pl_abs_ars"] is None, -(r["pl_abs_ars"] or -1e18)))
        return rows
