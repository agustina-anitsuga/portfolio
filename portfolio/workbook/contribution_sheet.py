# -*- coding: utf-8 -*-
"""Hoja "aporte"."""

SHEET = "aporte"
AMOUNT_LABEL = "monto"
CURRENCIES = ("ARS", "CCL")


class ContributionSheet:
    """Cuanto se aporta por mes y como se reparte.

    Una fila "Monto mensual ARS" con el monto en la segunda columna, y debajo
    una fila por ticker: Ticker, % y Moneda de compra (ARS o CCL). Las filas
    que no encajan (encabezados, notas) se ignoran. Los porcentajes se aceptan
    como 35 o como 35% (0.35). La hoja es opcional.
    """

    def __init__(self, workbook):
        self._workbook = workbook

    def plan(self):
        """{"monthly_ars": float, "rows": [{"ticker", "pct", "currency"}]},
        or None when the sheet is missing or has no amount."""
        if SHEET not in self._workbook.sheetnames:
            return None
        monthly, rows = None, []
        for row in self._workbook[SHEET].iter_rows(values_only=True):
            if not row or not row[0]:
                continue
            label = str(row[0]).strip()
            if AMOUNT_LABEL in label.lower() and self._number(row[1]) is not None:
                monthly = self._number(row[1])
            elif self._is_allocation(row):
                rows.append({"ticker": label, "pct": self._number(row[1]),
                             "currency": str(row[2]).strip().upper()})
        if monthly is None:
            return None
        return {"monthly_ars": monthly, "rows": self._as_percentages(rows)}

    @classmethod
    def _is_allocation(cls, row):
        return (len(row) >= 3 and cls._number(row[1]) is not None
                and row[2] and str(row[2]).strip().upper() in CURRENCIES)

    @staticmethod
    def _number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return float(value)

    @staticmethod
    def _as_percentages(rows):
        """A sheet formatted as % hands back fractions (0.35); detect it by the
        total being 1 instead of 100."""
        total = sum(r["pct"] for r in rows)
        if rows and abs(total - 1) < 1e-6:
            return [{**r, "pct": r["pct"] * 100} for r in rows]
        return rows
