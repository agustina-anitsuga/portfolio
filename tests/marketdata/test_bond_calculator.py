# -*- coding: utf-8 -*-
import pytest

from doubles import FakeSession
from portfolio.marketdata import bond_calculator as module
from portfolio.marketdata.bond_calculator import QUOTE_NOMINAL, BondCalculator
from portfolio.marketdata.fx_rate import FxRate

FX = FxRate(1500.0, "test")
ANSWER = {"tir": 0.077477, "currentCoupon": 0.06, "parity": 0.969786, "md": 2.074276,
          "expirationDate": "31/10/2028",
          "flows": [{"cuttingDate": "2026-08-31T00:00:00-03:00", "rent": 5.16}]}


class FakeMarketData:
    def __init__(self, answer=ANSWER):
        self._answer = answer
        self.requests = []

    def estimate_bonds(self, parameters):
        self.requests.append(parameters)
        if isinstance(self._answer, Exception):
            raise self._answer
        return self._answer


class FakeClient:
    def __init__(self, marketdata):
        self.marketdata = marketdata


def calculator(answer=ANSWER, available=True):
    feed = FakeMarketData(answer)
    return BondCalculator(FakeSession(FakeClient(feed), available=available)), feed


def test_the_calculator_answer_becomes_analytics():
    bonds, _ = calculator()
    analytics = bonds.analytics("AO28", unit_price=1474.5, units=1032, fx=FX)
    assert analytics.tir == pytest.approx(7.7477)
    assert analytics.maturity == "2028-10-31"


def test_the_price_is_sent_on_the_per_100_nominal_convention():
    """The rest of the dashboard works per unit; the calculator does not."""
    bonds, feed = calculator()
    bonds.analytics("AO28", unit_price=1474.5, units=1032, fx=FX)
    assert feed.requests[0].price == pytest.approx(1474.5 * QUOTE_NOMINAL)


def test_the_exchange_rate_travels_with_the_request():
    """Without it the yield is computed against cash flows in another currency
    and comes out absurd (-96% instead of 7.7%)."""
    bonds, feed = calculator()
    bonds.analytics("AO28", unit_price=1474.5, units=1032, fx=FX)
    assert feed.requests[0].exchangeRate == 1500.0
    assert feed.requests[0].exchangeRateAmortization == 1500.0


def test_the_position_size_travels_too():
    bonds, feed = calculator()
    bonds.analytics("AO28", unit_price=1474.5, units=1032, fx=FX)
    assert feed.requests[0].quantity == 1032
    assert feed.requests[0].quantityType == "PAPELES"


def test_without_an_exchange_rate_nothing_is_asked():
    bonds, feed = calculator()
    analytics = bonds.analytics("AO28", 1474.5, 1032, FxRate.unavailable("cerrado"))
    assert analytics.tir is None
    assert feed.requests == []


def test_without_a_price_nothing_is_asked():
    bonds, feed = calculator()
    assert bonds.analytics("AO28", None, 1032, FX).tir is None
    assert feed.requests == []


def test_without_units_nothing_is_asked():
    bonds, feed = calculator()
    assert bonds.analytics("AO28", 1474.5, 0, FX).tir is None
    assert feed.requests == []


def test_without_a_ppi_session_the_columns_stay_empty():
    bonds, feed = calculator(available=False)
    assert bonds.analytics("AO28", 1474.5, 1032, FX).tir is None


def test_a_broken_answer_does_not_reach_the_user():
    bonds, _ = calculator(answer="<html>error</html>")
    assert bonds.analytics("AO28", 1474.5, 1032, FX).tir is None


def test_an_answer_without_bond_data_is_discarded():
    bonds, _ = calculator(answer={"message": "sin datos"})
    assert bonds.analytics("AO28", 1474.5, 1032, FX).tir is None


def test_an_exception_is_swallowed():
    bonds, _ = calculator(answer=RuntimeError("503"))
    assert bonds.analytics("AO28", 1474.5, 1032, FX).tir is None


def test_without_the_ppi_package_nothing_is_attempted(monkeypatch):
    monkeypatch.setattr(module, "HAVE_PPI", False)
    bonds, feed = calculator()
    assert bonds.analytics("AO28", 1474.5, 1032, FX).tir is None
    assert feed.requests == []
