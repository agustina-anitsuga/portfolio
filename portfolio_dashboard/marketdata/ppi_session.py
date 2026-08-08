# -*- coding: utf-8 -*-
"""Connection to PPI: lazy login, pacing and retries."""

import sys
import time

try:
    from ppi_client.ppi import PPI
    HAVE_PPI = True
except ImportError:
    HAVE_PPI = False

NO_CLIENT = "sin cliente PPI (sin credenciales o paquete ppi-client no instalado)"


class PpiSession:
    """Best-effort PPI client: any failure just means "no live price", never an
    exception escaping outwards.

    It also spaces out requests and retries them, because PPI's throttling does
    not look like an error: it answers fine but without a price.
    """

    def __init__(self, settings, stderr=sys.stderr):
        self._settings = settings
        self._stderr = stderr
        self._client = None
        self._logged_in = False
        self._last_call = 0.0

    @property
    def available(self):
        """Without a client there is no point looking any further: that is the
        reason to report, even when some instrument metadata is missing too."""
        return self.client is not None

    @property
    def client(self):
        if not self._logged_in:
            self._logged_in = True
            self._client = self._login()
        return self._client

    def _login(self):
        if not HAVE_PPI:
            return self._warn("paquete 'ppi-client' no instalado (pip install ppi-client).")
        if not self._settings.has_credentials:
            return self._warn("no hay credenciales PPI_PUBLIC_KEY/PPI_PRIVATE_KEY configuradas.")
        try:
            client = PPI(sandbox=self._settings.sandbox)
            client.account.login_api(self._settings.public_key, self._settings.private_key)
            return client
        except Exception as e:
            return self._warn(f"no se pudo autenticar con PPI ({e}).")

    def _warn(self, reason):
        print(f"Aviso: {reason} Se usaran solo precios manuales.", file=self._stderr)
        return None

    def call(self, request):
        """Run request() with a preceding pause and retries with backoff.

        request() returns (value, reason); if the reason is not None it is
        retried. That covers both network or rate-limit errors (an exception)
        and empty responses.
        """
        if self.client is None:
            return None, NO_CLIENT
        reason = None
        for attempt in range(self._settings.attempts):
            if attempt:
                time.sleep(self._settings.backoff * (2 ** (attempt - 1)))
            self._throttle()
            value, reason = self._attempt(request)
            if reason is None:
                return value, None
        return None, f"{reason} (tras {self._settings.attempts} intentos)"

    @staticmethod
    def _attempt(request):
        try:
            return request()
        except Exception as e:
            return None, f"error consultando PPI: {type(e).__name__}: {e}"

    def _throttle(self):
        """Space out requests so they do not hit PPI's rate limit."""
        if self._settings.pause <= 0:
            return
        elapsed = time.monotonic() - self._last_call
        if elapsed < self._settings.pause:
            time.sleep(self._settings.pause - elapsed)
        self._last_call = time.monotonic()
