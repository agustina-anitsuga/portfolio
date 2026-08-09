# -*- coding: utf-8 -*-
"""RSI de Wilder."""

DEFAULT_PERIODS = 14


class RelativeStrengthIndex:
    """Yahoo is the only figure of the watchlist Yahoo does not publish, so it
    is computed from the closing prices with Wilder's smoothing -- the same
    definition Finviz and every charting tool use."""

    def __init__(self, periods=DEFAULT_PERIODS):
        self._periods = periods

    def of(self, closes):
        """None when there is not enough history to measure anything."""
        deltas = self._deltas(closes)
        if deltas is None:
            return None
        average_gain, average_loss = self._seed(deltas)
        for delta in deltas[self._periods:]:
            average_gain = self._smooth(average_gain, max(delta, 0.0))
            average_loss = self._smooth(average_loss, max(-delta, 0.0))
        if not average_loss:
            return 100.0    # only gains in the window
        return 100 - (100 / (1 + average_gain / average_loss))

    def _deltas(self, closes):
        closes = [c for c in (closes or []) if c is not None]
        if len(closes) <= self._periods:
            return None
        return [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    def _seed(self, deltas):
        """The first average is a plain mean; from there Wilder smooths."""
        window = deltas[:self._periods]
        return (sum(max(d, 0.0) for d in window) / self._periods,
                sum(max(-d, 0.0) for d in window) / self._periods)

    def _smooth(self, average, value):
        return (average * (self._periods - 1) + value) / self._periods
