# -*- coding: utf-8 -*-
import pytest

from portfolio.marketdata.trend import Trend


def test_empty_trend_has_no_percentage_and_no_series():
    trend = Trend.empty()
    assert trend.pct is None
    assert trend.series == []


def test_percentage_is_measured_between_the_ends_of_the_series():
    trend = Trend.from_series([100.0, 50.0, 125.0])
    assert trend.pct == pytest.approx(25.0)


def test_a_falling_series_gives_a_negative_percentage():
    assert Trend.from_series([200.0, 150.0]).pct == pytest.approx(-25.0)


def test_prices_are_rounded_to_four_decimals():
    """Keeps the JSON embedded in the HTML from ballooning."""
    assert Trend.from_series([1.123456789, 2.987654321]).series == [1.1235, 2.9877]


def test_percentage_is_computed_after_rounding():
    """So the tooltip number matches exactly the ends of the drawn line."""
    trend = Trend.from_series([1.000049, 2.0])
    assert trend.pct == pytest.approx((2.0 - 1.0) / 1.0 * 100)


def test_a_series_starting_at_zero_has_no_measurable_variation():
    assert Trend.from_series([0.0, 10.0]) is None


def test_a_flat_series_gives_zero():
    trend = Trend.from_series([10.0, 10.0, 10.0])
    assert trend.pct == 0.0
    assert trend.series == [10.0, 10.0, 10.0]


def test_each_empty_trend_gets_its_own_series_list():
    """A shared default list would leak points between instruments."""
    first, second = Trend.empty(), Trend.empty()
    first.series.append(1.0)
    assert second.series == []
