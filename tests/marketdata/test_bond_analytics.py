# -*- coding: utf-8 -*-
import pytest

from portfolio.marketdata.bond_analytics import BondAnalytics

# trimmed from a real answer of PPI's calculator for AO28
RESPONSE = {
    "tir": 0.077477, "currentCoupon": 0.06, "parity": 0.969786, "md": 2.074276,
    "expirationDate": "31/10/2028",
    "flows": [
        {"cuttingDate": "2026-08-31T00:00:00-03:00", "rent": 5.16, "amortization": 0},
        {"cuttingDate": "2026-09-30T00:00:00-03:00", "rent": 5.16, "amortization": 0},
    ],
}


def test_rates_are_kept_as_percentages():
    """The calculator answers fractions; the dashboard shows percentages."""
    analytics = BondAnalytics.from_response(RESPONSE)
    assert analytics.tir == pytest.approx(7.7477)
    assert analytics.coupon == pytest.approx(6.0)
    assert analytics.parity == pytest.approx(96.9786)


def test_duration_is_taken_as_is():
    assert BondAnalytics.from_response(RESPONSE).duration == pytest.approx(2.074276)


def test_maturity_is_normalised_to_iso():
    """It arrives as dd/mm/yyyy, and the column has to sort chronologically."""
    assert BondAnalytics.from_response(RESPONSE).maturity == "2028-10-31"


def test_the_next_payment_is_the_first_cash_flow():
    assert BondAnalytics.from_response(RESPONSE).next_payment == "2026-08-31"


def test_a_timestamp_keeps_only_its_date():
    analytics = BondAnalytics.from_response({"flows": [{"cuttingDate": "2026-08-31T00:00:00-03:00"}]})
    assert analytics.next_payment == "2026-08-31"


def test_missing_fields_stay_empty_instead_of_zero():
    """A zero yield would read as a real figure."""
    analytics = BondAnalytics.from_response({})
    assert analytics.tir is None
    assert analytics.coupon is None
    assert analytics.maturity is None
    assert analytics.next_payment is None


def test_a_bond_without_future_flows_has_no_next_payment():
    assert BondAnalytics.from_response({"flows": []}).next_payment is None


def test_an_empty_analytics_has_nothing():
    assert all(value is None for value in BondAnalytics.empty().as_dict().values())


def test_as_dict_prefixes_every_key():
    """So the bond fields never collide with the shared row fields."""
    assert set(BondAnalytics.empty().as_dict()) == {
        "bond_tir", "bond_coupon", "bond_parity", "bond_duration",
        "bond_maturity", "bond_next_payment"}
