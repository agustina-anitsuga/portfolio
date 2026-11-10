# -*- coding: utf-8 -*-
"""Configuration read from the environment."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """PPI credentials, request pacing and where the spreadsheet lives.

    PPI rate-limits requests. Without spacing them out, a run of ~50 calls in a
    row loses close to half the responses and the instruments end up "without
    price" with no visible error. Pausing between requests and retrying
    recovers them.
    """

    public_key: str = ""
    private_key: str = ""
    sandbox: bool = False
    pause: float = 0.35      # seconds between requests
    retries: int = 3         # attempts per request
    backoff: float = 0.8     # initial wait before retrying
    # Google Drive: the spreadsheet ID and the service account key, either as
    # a path to the JSON file (local runs) or as its content (Lambda/secrets).
    sheet_id: str = ""
    google_service_account_file: str = ""
    google_service_account_json: str = ""

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        return cls(
            public_key=env.get("PPI_PUBLIC_KEY", ""),
            private_key=env.get("PPI_PRIVATE_KEY", ""),
            sandbox=env.get("PPI_SANDBOX", "false").lower() == "true",
            pause=float(env.get("PPI_PAUSE", "0.35")),
            retries=int(env.get("PPI_RETRIES", "3")),
            backoff=float(env.get("PPI_BACKOFF", "0.8")),
            sheet_id=env.get("PORTFOLIO_SHEET_ID", ""),
            google_service_account_file=env.get("GOOGLE_SERVICE_ACCOUNT_FILE", ""),
            google_service_account_json=env.get("GOOGLE_SERVICE_ACCOUNT_JSON", ""),
        )

    @property
    def has_credentials(self):
        return bool(self.public_key and self.private_key)

    @property
    def attempts(self):
        return max(1, self.retries)
