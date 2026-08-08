# -*- coding: utf-8 -*-
"""One trade (BUY/SELL) from a tx-* sheet."""

from dataclasses import dataclass

from ..market import ARS, USD
from .date_parser import DateParser
from .row import cell, number

UNITS_COLUMN = 2
DATE_COLUMN = 3

BUY = "BUY"
SELL = "SELL"


@dataclass(frozen=True)
class Transaction:
    """The amount in the market's native currency is always recorded; the one
    in the other currency is optional and, when missing, that single trade is
    approximated at today's exchange rate (see PositionTracker)."""

    market: object
    ticker: str
    op: str
    units: float
    date: object
    amount_ars: float
    amount_usd: float

    @classmethod
    def from_row(cls, market, row):
        return cls(
            market=market,
            ticker=row[0],
            op=cell(row, 1),
            units=number(row, UNITS_COLUMN),
            date=cell(row, DATE_COLUMN),
            amount_ars=number(row, market.ars_column),
            amount_usd=number(row, market.usd_column),
        )

    @property
    def is_buy(self):
        return self.op == BUY

    def amount(self, currency):
        return self.amount_ars if currency == ARS else self.amount_usd

    def price(self, currency):
        amount = self.amount(currency)
        return amount / self.units if (amount is not None and self.units) else None

    @property
    def iso_date(self):
        return DateParser.iso(self.date)

    @property
    def year(self):
        return DateParser.year(self.date)

    def as_dict(self):
        return {
            "ticker": self.ticker, "market": self.market.key, "op": self.op,
            "date": self.iso_date, "year": self.year, "units": self.units,
            "amount_ars": self.amount_ars, "amount_usd": self.amount_usd,
            "price_ars": self.price(ARS), "price_usd": self.price(USD),
        }
