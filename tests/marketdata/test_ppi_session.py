# -*- coding: utf-8 -*-
import io

import pytest

from portfolio.marketdata import ppi_session as module
from portfolio.marketdata.ppi_session import NO_CLIENT, PpiSession
from portfolio.settings import Settings


class FakeClient:
    def __init__(self):
        self.account = self
        self.logged_in_with = None

    def login_api(self, public, private):
        self.logged_in_with = (public, private)


@pytest.fixture
def stderr():
    return io.StringIO()


@pytest.fixture
def logged_in(monkeypatch, settings, stderr):
    client = FakeClient()
    monkeypatch.setattr(module, "HAVE_PPI", True)
    monkeypatch.setattr(module, "PPI", lambda sandbox: client, raising=False)
    return PpiSession(settings, stderr=stderr), client


def test_logs_in_once_and_reuses_the_client(logged_in):
    session, client = logged_in
    assert session.client is client
    assert session.client is client
    assert client.logged_in_with == ("pub", "priv")


def test_without_the_package_it_warns_once_and_stays_unavailable(monkeypatch, settings, stderr):
    monkeypatch.setattr(module, "HAVE_PPI", False)
    session = PpiSession(settings, stderr=stderr)
    assert session.available is False
    assert session.client is None
    assert stderr.getvalue().count("Aviso:") == 1
    assert "ppi-client" in stderr.getvalue()


def test_without_credentials_it_warns_and_stays_unavailable(monkeypatch, stderr):
    monkeypatch.setattr(module, "HAVE_PPI", True)
    session = PpiSession(Settings(pause=0), stderr=stderr)
    assert session.available is False
    assert "credenciales" in stderr.getvalue()


def test_a_login_failure_is_swallowed_and_reported(monkeypatch, settings, stderr):
    def explode(sandbox):
        raise RuntimeError("503")

    monkeypatch.setattr(module, "HAVE_PPI", True)
    monkeypatch.setattr(module, "PPI", explode, raising=False)
    session = PpiSession(settings, stderr=stderr)
    assert session.client is None
    assert "no se pudo autenticar" in stderr.getvalue()
    assert "503" in stderr.getvalue()


def test_call_returns_the_value_when_the_request_succeeds(logged_in):
    session, _ = logged_in
    assert session.call(lambda: (42, None)) == (42, None)


def test_call_without_a_client_does_not_even_try(monkeypatch, settings, stderr):
    monkeypatch.setattr(module, "HAVE_PPI", False)
    session = PpiSession(settings, stderr=stderr)
    attempts = []
    value, reason = session.call(lambda: attempts.append(1) or (1, None))
    assert (value, reason) == (None, NO_CLIENT)
    assert attempts == []


def test_call_retries_while_the_request_reports_a_reason(monkeypatch, stderr):
    """PPI throttling answers fine but without a price, so a plain reason (not
    an exception) has to trigger the retry."""
    monkeypatch.setattr(module, "HAVE_PPI", True)
    monkeypatch.setattr(module, "PPI", lambda sandbox: FakeClient(), raising=False)
    monkeypatch.setattr(module.time, "sleep", lambda seconds: None)
    session = PpiSession(Settings(public_key="p", private_key="k", pause=0, retries=3, backoff=0),
                         stderr=stderr)

    answers = iter([(None, "vacio"), (None, "vacio"), (7, None)])
    value, reason = session.call(lambda: next(answers))
    assert (value, reason) == (7, None)


def test_call_gives_up_after_the_configured_attempts(monkeypatch, stderr):
    monkeypatch.setattr(module, "HAVE_PPI", True)
    monkeypatch.setattr(module, "PPI", lambda sandbox: FakeClient(), raising=False)
    monkeypatch.setattr(module.time, "sleep", lambda seconds: None)
    session = PpiSession(Settings(public_key="p", private_key="k", pause=0, retries=2, backoff=0),
                         stderr=stderr)

    tries = []
    value, reason = session.call(lambda: tries.append(1) or (None, "vacio"))
    assert value is None
    assert reason == "vacio (tras 2 intentos)"
    assert len(tries) == 2


def test_an_exception_becomes_a_reason_instead_of_escaping(logged_in):
    session, _ = logged_in

    def explode():
        raise ValueError("boom")

    value, reason = session.call(explode)
    assert value is None
    assert reason.startswith("error consultando PPI: ValueError: boom")


def test_backoff_grows_between_attempts(monkeypatch, stderr):
    monkeypatch.setattr(module, "HAVE_PPI", True)
    monkeypatch.setattr(module, "PPI", lambda sandbox: FakeClient(), raising=False)
    slept = []
    monkeypatch.setattr(module.time, "sleep", slept.append)
    session = PpiSession(Settings(public_key="p", private_key="k", pause=0, retries=4, backoff=0.5),
                         stderr=stderr)

    session.call(lambda: (None, "vacio"))
    assert slept == [0.5, 1.0, 2.0]  # no wait before the first attempt


def test_requests_are_spaced_by_the_configured_pause(monkeypatch, stderr):
    monkeypatch.setattr(module, "HAVE_PPI", True)
    monkeypatch.setattr(module, "PPI", lambda sandbox: FakeClient(), raising=False)
    clock = iter([100.0, 100.0, 100.1, 100.1])   # second call comes 0.1s later
    slept = []
    monkeypatch.setattr(module.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(module.time, "sleep", slept.append)
    session = PpiSession(Settings(public_key="p", private_key="k", pause=0.35, retries=1),
                         stderr=stderr)

    session.call(lambda: (1, None))
    session.call(lambda: (1, None))
    assert slept == [pytest.approx(0.25)]  # waits the remainder of the pause


def test_no_pause_means_no_sleeping(monkeypatch, settings, stderr):
    monkeypatch.setattr(module, "HAVE_PPI", True)
    monkeypatch.setattr(module, "PPI", lambda sandbox: FakeClient(), raising=False)
    slept = []
    monkeypatch.setattr(module.time, "sleep", slept.append)
    PpiSession(settings, stderr=stderr).call(lambda: (1, None))
    assert slept == []
