# -*- coding: utf-8 -*-
"""Today's USD/ARS exchange rate."""

from dataclasses import dataclass

from ..market import ARS


@dataclass(frozen=True)
class FxRate:
    """How many ARS one USD is worth, and where that number came from.

    Falsy when there is no quote: the converted columns are left empty instead
    of showing a made-up number.
    """

    value: float = None
    source: str = "no disponible"

    def __bool__(self):
        return bool(self.value)

    @classmethod
    def unavailable(cls, reason):
        return cls(None, reason or "no disponible")

    def to_ars(self, usd_amount):
        return usd_amount * self.value

    def to_usd(self, ars_amount):
        return ars_amount / self.value

    def convert(self, amount, to_currency):
        return self.to_ars(amount) if to_currency == ARS else self.to_usd(amount)
