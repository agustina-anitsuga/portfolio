# -*- coding: utf-8 -*-
import json
from pathlib import Path

import pytest

from portfolio.settings import Settings
from portfolio.sources.google_sheet import (READ_ONLY_SCOPE, XLSX, GoogleSheet,
                                            SheetSourceError)


class FakeResponse:
    def __init__(self, status_code=200, content=b"", payload=None):
        self.status_code = status_code
        self.content = content
        self.text = content.decode("utf-8", "replace")
        self._payload = payload

    def json(self):
        return self._payload


class FakeHttp:
    """Answers Drive's metadata and export calls; records what was asked."""

    def __init__(self, status_code=200, error=None):
        self.calls = []
        self._status = status_code
        self._error = error

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        if self._error:
            raise self._error
        if self._status != 200:
            return FakeResponse(self._status, b"denied")
        if url.endswith("/export"):
            return FakeResponse(content=b"xlsx-bytes")
        return FakeResponse(payload={"modifiedTime": "2026-11-10T17:32:00.000Z"})


def test_exports_the_sheet_as_xlsx_to_a_temporary_file():
    http = FakeHttp()
    sheet = GoogleSheet("SHEET", http)
    with sheet.downloaded() as path:
        assert Path(path).read_bytes() == b"xlsx-bytes"
    assert not Path(path).exists()
    export_url, export_params = http.calls[-1]
    assert export_url.endswith("/files/SHEET/export")
    assert export_params == {"mimeType": XLSX}


def test_reports_when_the_sheet_was_last_edited():
    sheet = GoogleSheet("SHEET", FakeHttp())
    with sheet.downloaded():
        pass
    assert sheet.modified_time.utcoffset() is not None
    assert sheet.modified_time.timestamp() == pytest.approx(1794331920)


@pytest.mark.parametrize("status", [403, 404])
def test_missing_access_names_the_service_account(status):
    sheet = GoogleSheet("SHEET", FakeHttp(status), account_email="bot@proj.iam.gserviceaccount.com")
    with pytest.raises(SheetSourceError, match="bot@proj.iam.gserviceaccount.com"):
        with sheet.downloaded():
            pass


def test_other_http_errors_are_reported():
    with pytest.raises(SheetSourceError, match="HTTP 500"):
        with GoogleSheet("SHEET", FakeHttp(500)).downloaded():
            pass


def test_network_errors_are_reported():
    with pytest.raises(SheetSourceError, match="conectar"):
        with GoogleSheet("SHEET", FakeHttp(error=OSError("sin red"))).downloaded():
            pass


def test_a_missing_impersonation_role_says_which_role_to_grant():
    error = RuntimeError("Permission 'iam.serviceAccounts.getAccessToken' denied")
    sheet = GoogleSheet("SHEET", FakeHttp(error=error), account_email="bot@p.iam.gserviceaccount.com")
    with pytest.raises(SheetSourceError, match="serviceAccountTokenCreator"):
        with sheet.downloaded():
            pass


def test_a_sheet_id_is_required():
    with pytest.raises(SheetSourceError, match="PORTFOLIO_SHEET_ID"):
        GoogleSheet.from_settings(Settings())


def test_without_a_key_it_uses_application_default_credentials(monkeypatch):
    import google.auth

    class AdcCredentials:
        service_account_email = "bot@proj.iam.gserviceaccount.com"

    asked = []

    def fake_default(scopes=None):
        asked.append(scopes)
        return AdcCredentials(), "proj"

    monkeypatch.setattr(google.auth, "default", fake_default)
    sheet = GoogleSheet.from_settings(Settings(sheet_id="SHEET"))
    assert asked == [[READ_ONLY_SCOPE]]
    assert sheet._account_email == "bot@proj.iam.gserviceaccount.com"


def test_missing_default_credentials_explain_how_to_log_in(monkeypatch):
    import google.auth
    from google.auth.exceptions import DefaultCredentialsError

    def no_credentials(scopes=None):
        raise DefaultCredentialsError("none")

    monkeypatch.setattr(google.auth, "default", no_credentials)
    with pytest.raises(SheetSourceError, match="application-default login"):
        GoogleSheet.from_settings(Settings(sheet_id="SHEET"))


def test_an_unreadable_key_file_is_reported(tmp_path):
    settings = Settings(sheet_id="SHEET", google_service_account_file=str(tmp_path / "no.json"))
    with pytest.raises(SheetSourceError, match="No se pudo leer"):
        GoogleSheet.from_settings(settings)


def test_an_invalid_key_is_reported():
    settings = Settings(sheet_id="SHEET", google_service_account_json="not json")
    with pytest.raises(SheetSourceError, match="JSON valido"):
        GoogleSheet.from_settings(settings)


def test_the_cli_sheet_id_wins_over_the_environment(tmp_path):
    """Builds real (offline) credentials from a throwaway key."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()).decode()
    info = {"type": "service_account", "client_email": "bot@proj.iam.gserviceaccount.com",
            "private_key": key, "token_uri": "https://oauth2.googleapis.com/token"}
    settings = Settings(sheet_id="FROM_ENV", google_service_account_json=json.dumps(info))
    sheet = GoogleSheet.from_settings(settings, sheet_id="FROM_CLI")
    assert sheet._sheet_id == "FROM_CLI"
    assert sheet._account_email == "bot@proj.iam.gserviceaccount.com"
