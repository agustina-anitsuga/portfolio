# -*- coding: utf-8 -*-
from portfolio.watchlist.fundamentals import Fundamentals
from portfolio.watchlist.parameter_score import ParameterScore

# every rule passing: PE<10, current ratio>1, RSI<50, debt/equity<1, P/B<3
PERFECT = dict(pe=8.0, current_ratio=2.0, rsi=40.0, debt_to_equity=0.5, price_to_book=1.5)


def score_of(**overrides):
    values = dict(PERFECT)
    values.update(overrides)
    return ParameterScore(Fundamentals(**values))


def test_all_five_rules_passing_is_a_strong_buy():
    assert score_of().score == 5
    assert score_of().signal == "Strong buy"


def test_none_passing_is_a_strong_sell():
    result = score_of(pe=30.0, current_ratio=0.5, rsi=70.0, debt_to_equity=2.0, price_to_book=9.0)
    assert result.score == 0
    assert result.signal == "Strong Sell"


def test_each_rule_is_worth_one_point():
    assert score_of(pe=30.0).score == 4
    assert score_of(current_ratio=0.5).score == 4
    assert score_of(rsi=70.0).score == 4
    assert score_of(debt_to_equity=2.0).score == 4
    assert score_of(price_to_book=9.0).score == 4


def test_the_score_maps_to_the_signal_of_the_spreadsheet():
    assert score_of(pe=30.0).signal == "Buy"                              # 4
    assert score_of(pe=30.0, current_ratio=0.5).signal == "Hold"          # 3
    assert score_of(pe=30.0, current_ratio=0.5, rsi=70.0).signal == "Hold"  # 2
    assert score_of(pe=30.0, current_ratio=0.5, rsi=70.0,
                    debt_to_equity=2.0).signal == "Sell"                  # 1


def test_a_value_exactly_on_the_threshold_does_not_pass():
    assert score_of(pe=10.0).score == 4
    assert score_of(current_ratio=1.0).score == 4


def test_a_missing_parameter_leaves_the_score_undefined():
    """An ETF has no PE and no debt. The original spreadsheet read those blanks
    as zero, and a zero passes every "less than" rule, so an instrument with no
    data came out as a strong buy."""
    assert score_of(pe=None).score is None
    assert score_of(pe=None).signal is None


def test_an_empty_instrument_scores_nothing():
    assert ParameterScore(Fundamentals.empty()).score is None
