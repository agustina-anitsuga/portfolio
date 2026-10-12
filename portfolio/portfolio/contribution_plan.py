# -*- coding: utf-8 -*-
"""The monthly contribution, split into what to buy and in which currency."""


class ContributionPlan:
    """Turns the "aporte" sheet and today's CCL dollar into amounts.

    Tickers bought in CCL need pesos converted to CCL dollars first; the rest
    is bought straight in pesos. The CCL conversion is taken at the quoted
    rate: spread and fees are not included. Without a CCL rate the dollar
    amounts are left empty instead of made up.
    """

    def __init__(self, contribution, ccl):
        self._contribution = contribution
        self._ccl = ccl

    def as_dict(self):
        if not self._contribution:
            return None
        monthly = self._contribution["monthly_ars"]
        rows = [self._row(r, monthly) for r in self._contribution["rows"]]
        ccl_rows = [r for r in rows if r["currency"] == "CCL"]
        ars_to_ccl = sum(r["ars"] for r in ccl_rows)
        return {
            "monthly_ars": monthly,
            "monthly_usd": self._to_usd(monthly),
            "rows": rows,
            "pct_total": sum(r["pct"] for r in rows),
            "ars_to_ccl": ars_to_ccl,
            "usd_from_ccl": self._to_usd(ars_to_ccl),
            "ars_direct": sum(r["ars"] for r in rows if r["currency"] == "ARS"),
            "ccl_rate": self._ccl.value if self._ccl else None,
            "ccl_source": self._ccl.source if self._ccl is not None else "no disponible",
        }

    def _row(self, row, monthly):
        ars = monthly * row["pct"] / 100
        return {**row, "ars": ars, "usd": self._to_usd(ars)}

    def _to_usd(self, ars):
        return self._ccl.to_usd(ars) if self._ccl else None
