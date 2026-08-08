# -*- coding: utf-8 -*-
"""Current price of an instrument, in both currencies."""

from dataclasses import dataclass

from ..market import ARS, USD, other_currency

UNAVAILABLE = "no disponible"


@dataclass(frozen=True)
class Quote:
    """The instrument's native currency (what PPI/Yahoo/the manual price
    actually quote) is exact; the other one is derived using today's exchange
    rate. `debug_note` is only filled in when it ends up without a price, so
    the console can show why every source that was tried failed."""

    price_ars: float = None
    price_usd: float = None
    source: str = UNAVAILABLE
    debug_note: str = None

    @classmethod
    def from_native(cls, price, currency, source, fx):
        derived = other_currency(currency)
        prices = {currency: price}
        prices[derived] = fx.convert(price, derived) if (price is not None and fx) else None
        return cls(prices[ARS], prices[USD], source)

    @classmethod
    def unavailable(cls, debug_note):
        return cls(None, None, UNAVAILABLE, debug_note)

    def price(self, currency):
        return self.price_ars if currency == ARS else self.price_usd
