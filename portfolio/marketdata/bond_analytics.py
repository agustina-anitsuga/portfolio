# -*- coding: utf-8 -*-
"""Bond-specific figures: yield, coupon, maturity, duration."""

from dataclasses import dataclass

from ..workbook.date_parser import DateParser


@dataclass(frozen=True)
class BondAnalytics:
    """What PPI's bond calculator answers, normalized.

    `tir`, `parity` and `duration` depend on the exchange rate handed to the
    calculator, because a bond quoted in pesos can pay its coupons in dollars:
    without it the calculator subtracts pesos from dollars and the yield comes
    out absurd. Coupon, maturity and the payment dates do not depend on it.

    Rates arrive as fractions (0.0775) and are kept as percentages (7.75), the
    same convention the rest of the dashboard uses.
    """

    tir: float = None
    coupon: float = None
    parity: float = None
    duration: float = None
    maturity: str = None
    next_payment: str = None

    @classmethod
    def empty(cls):
        return cls()

    @classmethod
    def from_response(cls, data):
        return cls(
            tir=_percent(data.get("tir")),
            coupon=_percent(data.get("currentCoupon")),
            parity=_percent(data.get("parity")),
            duration=_number(data.get("md")),
            maturity=_date(data.get("expirationDate")),
            next_payment=_next_payment(data.get("flows")),
        )

    def as_dict(self):
        return {
            "bond_tir": self.tir, "bond_coupon": self.coupon, "bond_parity": self.parity,
            "bond_duration": self.duration, "bond_maturity": self.maturity,
            "bond_next_payment": self.next_payment,
        }


def _number(value):
    return float(value) if value is not None else None


def _percent(value):
    return float(value) * 100 if value is not None else None


def _date(value):
    """Always ISO, so the column sorts chronologically."""
    if not value:
        return None
    # the calculator answers "31/10/2028" for maturity and full timestamps
    # ("2026-08-31T00:00:00-03:00") inside the cash flow.
    return DateParser.iso(str(value).split("T")[0]) or None


def _next_payment(flows):
    """The first future cash flow: the calculator returns them in order."""
    if not flows:
        return None
    return _date(flows[0].get("cuttingDate"))
