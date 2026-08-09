# -*- coding: utf-8 -*-
import pytest

from portfolio.watchlist.target_price_signal import TargetPriceSignal


def signal(price, low=100.0, high=200.0):
    return TargetPriceSignal(price, low, high)


def test_the_targets_sit_at_half_and_at_85_percent_of_the_range():
    """The rule of the original spreadsheet: (high-low)*ratio + low."""
    target = signal(150.0)
    assert target.target_buy == pytest.approx(150.0)
    assert target.target_sell == pytest.approx(185.0)


def test_the_targets_match_the_spreadsheet_for_a_real_row():
    target = signal(313.33, low=219.25, high=344.57)   # AAPL
    assert target.target_buy == pytest.approx(281.91)
    assert target.target_sell == pytest.approx(325.772)


def test_below_the_buy_target_it_says_buy():
    assert signal(120.0).signal == "Buy"


def test_above_the_sell_target_it_says_sell():
    assert signal(190.0).signal == "Sell"


def test_in_between_it_says_hold():
    assert signal(170.0).signal == "Hold"


def test_exactly_on_a_target_is_hold():
    assert signal(150.0).signal == "Hold"
    assert signal(185.0).signal == "Hold"


def test_without_a_price_there_is_no_signal():
    assert TargetPriceSignal(None, 100.0, 200.0).signal is None


def test_without_the_52_week_range_there_is_no_signal():
    assert TargetPriceSignal(150.0, None, 200.0).signal is None
    assert TargetPriceSignal(150.0, 100.0, None).target_buy is None


def test_a_degenerate_range_is_not_measurable():
    """A brand new listing can report the same low and high."""
    assert TargetPriceSignal(150.0, 150.0, 150.0).signal is None
