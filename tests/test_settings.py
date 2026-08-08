# -*- coding: utf-8 -*-
from portfolio_dashboard.settings import Settings


def test_reads_every_value_from_the_environment():
    settings = Settings.from_env({
        "PPI_PUBLIC_KEY": "pub", "PPI_PRIVATE_KEY": "priv", "PPI_SANDBOX": "TRUE",
        "PPI_PAUSE": "1.5", "PPI_RETRIES": "5", "PPI_BACKOFF": "2",
    })
    assert (settings.public_key, settings.private_key) == ("pub", "priv")
    assert settings.sandbox is True
    assert (settings.pause, settings.retries, settings.backoff) == (1.5, 5, 2.0)


def test_falls_back_to_defaults_when_the_environment_is_empty():
    settings = Settings.from_env({})
    assert settings.public_key == ""
    assert settings.sandbox is False
    assert (settings.pause, settings.retries, settings.backoff) == (0.35, 3, 0.8)


def test_sandbox_is_only_enabled_by_the_word_true():
    assert Settings.from_env({"PPI_SANDBOX": "1"}).sandbox is False
    assert Settings.from_env({"PPI_SANDBOX": "true"}).sandbox is True


def test_credentials_need_both_keys():
    assert Settings(public_key="pub").has_credentials is False
    assert Settings(private_key="priv").has_credentials is False
    assert Settings(public_key="pub", private_key="priv").has_credentials is True


def test_attempts_is_never_below_one():
    """A misconfigured PPI_RETRIES=0 must not skip the request altogether."""
    assert Settings(retries=0).attempts == 1
    assert Settings(retries=-3).attempts == 1
    assert Settings(retries=4).attempts == 4
