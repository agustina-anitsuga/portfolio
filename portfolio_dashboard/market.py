# -*- coding: utf-8 -*-
"""The instrument types the dashboard handles."""

from dataclasses import dataclass

ARS = "ars"
USD = "usd"
CURRENCIES = (ARS, USD)


def other_currency(currency):
    return USD if currency == ARS else ARS


@dataclass(frozen=True)
class Market:
    """One instrument type: its transaction sheet, its native currency and
    which columns of that sheet hold the amount in each currency.

    `native_currency` is the currency the instrument actually trades in
    (cedears and Merval stocks trade in ARS even when the underlying is in
    USD), and it is the one PPI/Yahoo/the manual price quote exactly: the other
    one is derived using today's exchange rate.
    """

    key: str
    label: str
    native_currency: str
    sheet: str
    ars_column: int
    usd_column: int

    @property
    def other_currency(self):
        return other_currency(self.native_currency)

    def amount_column(self, currency):
        return self.ars_column if currency == ARS else self.usd_column

    @classmethod
    def all(cls):
        return _MARKETS

    @classmethod
    def keys(cls):
        return [m.key for m in _MARKETS]

    @classmethod
    def get(cls, key):
        return _BY_KEY[key]

    @classmethod
    def labels(cls):
        return {m.key: m.label for m in _MARKETS}


_MARKETS = (
    # tx-usd / tx-rsu: col5 = Total amount (@Origin, USD), always present;
    # col6 = Total amount (ARS), optional -- old transactions never recorded
    # it, so for those there is no historical ARS amount.
    Market("usd", "US Stocks", USD, "tx-usd", ars_column=6, usd_column=5),
    # tx-cedears: col4 = Total amount (@Local, ARS), what actually trades on
    # BYMA; col6 = Total amount (@Origin, USD), the real USD cost of each
    # transaction. Using both real amounts (instead of doing Ratio math) avoids
    # the ~60x inflated P&L bug we hit earlier.
    Market("cedears", "Cedears", ARS, "tx-cedears", ars_column=4, usd_column=6),
    # tx-merval: col5 = Total amount (ARS), always present; col6 = Total amount
    # (USD), computed with the exchange rate of the DAY of the trade, so real.
    Market("merval", "Acciones Merval", ARS, "tx-merval", ars_column=5, usd_column=6),
    Market("rsu", "RSU", USD, "tx-rsu", ars_column=6, usd_column=5),
    # tx-bonds: bonds like AO28 quote and settle in both currencies on BYMA, so
    # both amounts come from the real trade.
    Market("bonds", "Bonos", ARS, "tx-bonds", ars_column=5, usd_column=6),
)

_BY_KEY = {m.key: m for m in _MARKETS}
