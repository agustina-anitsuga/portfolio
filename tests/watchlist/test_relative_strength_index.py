# -*- coding: utf-8 -*-
import pytest

from portfolio.watchlist.relative_strength_index import RelativeStrengthIndex

RSI = RelativeStrengthIndex()


def test_only_gains_pins_the_index_at_one_hundred():
    assert RSI.of([100 + i for i in range(30)]) == 100.0


def test_only_losses_pins_it_at_zero():
    assert RSI.of([100 - i for i in range(30)]) == pytest.approx(0.0)


def test_a_flat_series_has_no_movement_to_measure():
    """No losses either, so by definition it reads as fully overbought."""
    assert RSI.of([100.0] * 30) == 100.0


def test_the_result_always_sits_between_zero_and_one_hundred():
    closes = [100, 102, 101, 105, 103, 107, 106, 110, 108, 112,
              111, 115, 113, 117, 116, 120, 118, 122, 121, 125]
    assert 0 <= RSI.of(closes) <= 100


def test_alternating_moves_of_the_same_size_land_around_the_middle():
    """Equal gains and losses cancel out; the last move tilts it a little."""
    up = [100 + (2 if i % 2 else 0) for i in range(40)]
    assert RSI.of(up) == pytest.approx(50.0, abs=3.0)
    assert RSI.of(up + [100]) < RSI.of(up)   # closing down lowers it


def test_a_short_history_cannot_be_measured():
    """It needs more closes than periods to seed the averages."""
    assert RSI.of([100, 101, 102]) is None
    assert RSI.of(list(range(14))) is None


def test_no_history_at_all_is_not_an_error():
    assert RSI.of([]) is None
    assert RSI.of(None) is None


def test_missing_closes_are_skipped():
    closes = [100 + i for i in range(30)]
    closes[5] = None
    assert RSI.of(closes) == 100.0


def test_the_window_length_is_configurable():
    closes = [100 + i for i in range(10)]
    assert RelativeStrengthIndex(periods=5).of(closes) == 100.0
    assert RelativeStrengthIndex(periods=20).of(closes) is None
