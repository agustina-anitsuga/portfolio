# -*- coding: utf-8 -*-
"""Metodo #1: precio objetivo dentro del rango de 52 semanas."""

BUY_RATIO = 0.50
SELL_RATIO = 0.85

BUY = "Buy"
SELL = "Sell"
HOLD = "Hold"


class TargetPriceSignal:
    """Sitúa el precio de hoy dentro del rango de 52 semanas.

    Comprar por debajo de la mitad del rango, vender pasado el 85%: es la
    regla de la planilla original, tal cual.
    """

    def __init__(self, price, low52, high52):
        self._price = price
        self._low = low52
        self._high = high52

    @property
    def measurable(self):
        return None not in (self._price, self._low, self._high) and self._high > self._low

    @property
    def target_buy(self):
        return self._target(BUY_RATIO)

    @property
    def target_sell(self):
        return self._target(SELL_RATIO)

    def _target(self, ratio):
        if not self.measurable:
            return None
        return (self._high - self._low) * ratio + self._low

    @property
    def signal(self):
        if not self.measurable:
            return None
        if self._price > self.target_sell:
            return SELL
        if self._price < self.target_buy:
            return BUY
        return HOLD
