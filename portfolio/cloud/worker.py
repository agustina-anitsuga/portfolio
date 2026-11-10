# -*- coding: utf-8 -*-
"""Lambda that regenerates the dashboard: reads the spreadsheet from Google
Drive, prices it, renders the HTML and leaves it in S3. It is launched
asynchronously by the API, so it is not bound by API Gateway's 29 s."""

import dataclasses
import json
import os
import time
import traceback
from pathlib import Path

from .status import DASHBOARD_KEY, RefreshStatus

# Argentina, UTC-3 with no DST. A POSIX rule instead of a zone name, so it does
# not depend on the zoneinfo files of the runtime image. Every "today" of the
# calculation (current year, PPI date ranges) and the "generated at" stamp
# must be Argentine time, not the UTC the Lambda runs in.
ARGENTINA_TZ = "<-03>3"
GOOGLE_CREDENTIALS_PATH = "/tmp/google-credentials.json"


class DashboardWorker:

    def __init__(self, s3, ssm, env, build_dashboard=None, sheet_factory=None):
        self._s3 = s3
        self._ssm = ssm
        self._env = env
        self._bucket = env["DATA_BUCKET"]
        self._status = RefreshStatus(s3, self._bucket)
        self._build_dashboard = build_dashboard or _build_dashboard
        self._sheet_factory = sheet_factory

    def run(self):
        try:
            settings = self._settings()
            sheet = self._sheet(settings)
            with sheet.downloaded() as xlsx_path:
                dashboard = self._build_dashboard(settings, xlsx_path)
            self._s3.put_object(Bucket=self._bucket, Key=DASHBOARD_KEY,
                                Body=dashboard.render().encode("utf-8"),
                                ContentType="text/html; charset=utf-8",
                                CacheControl="no-store")
            modified = sheet.modified_time.isoformat(timespec="seconds")
            return self._status.finish(dashboard.generated_at, modified)
        except Exception as error:  # report every failure to the page
            traceback.print_exc()
            return self._status.fail(str(error) or error.__class__.__name__)

    def _settings(self):
        """PPI keys from Parameter Store, never from the Lambda configuration."""
        from ..settings import Settings
        ppi = json.loads(self._parameter(self._env["PPI_PARAM"], decrypt=True))
        return dataclasses.replace(Settings.from_env(self._env),
                                   public_key=ppi.get("public_key", ""),
                                   private_key=ppi.get("private_key", ""),
                                   sheet_id=self._env["PORTFOLIO_SHEET_ID"])

    def _sheet(self, settings):
        """Google access through Workload Identity Federation: the parameter
        holds a credentials *configuration* (no secret in it) that trades the
        Lambda's own AWS identity for a token of the service account."""
        if self._sheet_factory:
            return self._sheet_factory(settings)
        from ..sources.google_sheet import GoogleSheet
        config = self._parameter(self._env["GOOGLE_CREDENTIALS_PARAM"])
        Path(GOOGLE_CREDENTIALS_PATH).write_text(config, encoding="utf-8")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS_PATH
        return GoogleSheet.from_settings(settings)

    def _parameter(self, name, decrypt=False):
        return self._ssm.get_parameter(Name=name, WithDecryption=decrypt)["Parameter"]["Value"]


def _build_dashboard(settings, xlsx_path):
    from ..app import PortfolioApp
    from ..output.html_dashboard import HtmlDashboard
    return HtmlDashboard(PortfolioApp(settings).snapshot(xlsx_path))


def handler(event, context):
    os.environ["TZ"] = ARGENTINA_TZ
    time.tzset()
    import boto3
    worker = DashboardWorker(boto3.client("s3"), boto3.client("ssm"), dict(os.environ))
    return worker.run()
