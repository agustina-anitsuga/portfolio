# -*- coding: utf-8 -*-
"""The spreadsheet read straight from Google Drive."""

import datetime as dt
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

DRIVE_FILES = "https://www.googleapis.com/drive/v3/files/"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
READ_ONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
TIMEOUT = 60  # seconds


class SheetSourceError(Exception):
    """The spreadsheet could not be read from Drive; the message says why and
    what to fix."""


class GoogleSheet:
    """A Google Sheet exported as .xlsx, so `PortfolioWorkbook` reads it
    exactly like the local file. Google computes the formulas before
    exporting, which is what `load_workbook(data_only=True)` needs.

    Access goes through a service account that only sees the files shared
    with it, with a read-only scope: it can neither see the rest of the Drive
    nor change the spreadsheet. No key file is needed: the account is
    impersonated through Application Default Credentials."""

    def __init__(self, sheet_id, http, account_email=""):
        self._sheet_id = sheet_id
        self._http = http
        self._account_email = account_email
        self.modified_time = None

    @classmethod
    def from_settings(cls, settings, sheet_id=None):
        sheet_id = sheet_id or settings.sheet_id
        if not sheet_id:
            raise SheetSourceError(
                "No se indico la planilla de Google Drive: defini PORTFOLIO_SHEET_ID "
                "(o usa --sheet-id), o pasa la ruta de un .xlsx local.")
        try:
            from google.auth.transport.requests import AuthorizedSession
        except ImportError as error:  # pragma: no cover - depends on the install
            raise SheetSourceError(
                "Falta la libreria google-auth: pip install -r requirements.txt") from error
        credentials = cls._credentials(settings)
        account = getattr(credentials, "service_account_email", "") or ""
        return cls(sheet_id, AuthorizedSession(credentials), account)

    @classmethod
    def _credentials(cls, settings):
        """A service account key when one is configured; otherwise Application
        Default Credentials, which need no key file: locally `gcloud auth
        application-default login --impersonate-service-account=...`, and in
        AWS a Workload Identity Federation config."""
        if settings.google_service_account_json or settings.google_service_account_file:
            from google.oauth2 import service_account
            return service_account.Credentials.from_service_account_info(
                cls._service_account_info(settings), scopes=[READ_ONLY_SCOPE])
        import google.auth
        from google.auth.exceptions import DefaultCredentialsError
        try:
            credentials, _ = google.auth.default(scopes=[READ_ONLY_SCOPE])
        except DefaultCredentialsError as error:
            raise SheetSourceError(
                "Faltan las credenciales de Google. Corre una vez:\n"
                "  gcloud auth application-default login "
                "--impersonate-service-account=<email de la cuenta de servicio>\n"
                "(ver README, \"Planilla en Google Drive\").") from error
        return credentials

    @staticmethod
    def _service_account_info(settings):
        if settings.google_service_account_json:
            raw, origin = settings.google_service_account_json, "GOOGLE_SERVICE_ACCOUNT_JSON"
        else:
            origin = settings.google_service_account_file
            try:
                raw = Path(origin).read_text(encoding="utf-8")
            except OSError as error:
                raise SheetSourceError(
                    f"No se pudo leer la clave de la cuenta de servicio ({origin}): {error}"
                ) from error
        try:
            return json.loads(raw)
        except ValueError as error:
            raise SheetSourceError(f"La clave de la cuenta de servicio ({origin}) no es un "
                                   "JSON valido.") from error

    @contextmanager
    def downloaded(self):
        """Yields the path of a temporary .xlsx copy, deleted on exit. The
        workbook is read into memory in one go, so nothing needs it after."""
        self.modified_time = self._fetch_modified_time()
        with tempfile.TemporaryDirectory(prefix="portfolio-") as folder:
            path = Path(folder) / "portfolio.xlsx"
            path.write_bytes(self._get("/export", {"mimeType": XLSX}).content)
            yield str(path)

    def _fetch_modified_time(self):
        """When the spreadsheet was last edited, in local time: it tells
        whether a run already includes the latest trade."""
        stamp = self._get("", {"fields": "modifiedTime"}).json()["modifiedTime"]
        return dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone()

    def _get(self, suffix, params):
        try:
            response = self._http.get(DRIVE_FILES + self._sheet_id + suffix,
                                      params=params, timeout=TIMEOUT)
        except Exception as error:  # network or token errors
            if "iam.serviceAccounts.getAccessToken" in str(error):
                account = self._account_email or "la cuenta de servicio"
                raise SheetSourceError(
                    f"Tu usuario no puede actuar como {account}. En Google Cloud → IAM → "
                    "Cuentas de servicio → esa cuenta → Permisos, otorga a tu email el rol "
                    "\"Creador de tokens de cuenta de servicio\" "
                    "(roles/iam.serviceAccountTokenCreator). Puede tardar unos minutos en "
                    "aplicarse.") from error
            raise SheetSourceError(f"No se pudo conectar con Google Drive: {error}") from error
        if response.status_code in (403, 404):
            shared_with = f" ({self._account_email})" if self._account_email else ""
            raise SheetSourceError(
                f"Google Drive no encontro la planilla {self._sheet_id} o no da acceso a ella "
                f"(HTTP {response.status_code}). Revisa el ID y que este compartida como lector "
                f"con la cuenta de servicio{shared_with}.")
        if response.status_code != 200:
            raise SheetSourceError(f"Google Drive respondio HTTP {response.status_code}: "
                                   f"{response.text[:200]}")
        return response
