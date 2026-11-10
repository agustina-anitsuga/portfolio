# -*- coding: utf-8 -*-
"""The AWS handlers, with S3/SSM/Lambda replaced by in-memory doubles."""

import datetime as dt
import json

import pytest

from doubles import FakeSheet

from portfolio.cloud.api import DashboardApi
from portfolio.cloud.status import DASHBOARD_KEY, STATUS_KEY, RefreshStatus
from portfolio.cloud.worker import DashboardWorker

NOW = dt.datetime(2026, 11, 10, 15, 0, tzinfo=dt.timezone.utc)
AR = dt.timezone(dt.timedelta(hours=-3))


class FakeS3:
    class exceptions:
        class NoSuchKey(Exception):
            pass

    def __init__(self):
        self.objects = {}

    def get_object(self, Bucket, Key):
        if Key not in self.objects:
            raise self.exceptions.NoSuchKey(Key)
        body = self.objects[Key]["Body"]

        class Stream:
            def read(self):
                return body
        return {"Body": Stream()}

    def put_object(self, Bucket, Key, Body, **kwargs):
        self.objects[Key] = {"Body": Body, **kwargs}

    def generate_presigned_url(self, op, Params, ExpiresIn):
        return f"https://s3/{Params['Key']}?expires={ExpiresIn}"

    def status(self):
        return json.loads(self.objects[STATUS_KEY]["Body"])


class FakeLambda:
    def __init__(self, error=None):
        self.invocations = []
        self._error = error

    def invoke(self, **kwargs):
        if self._error:
            raise self._error
        self.invocations.append(kwargs)


class FakeDashboard:
    generated_at = "2026-11-10 12:00"

    def __init__(self, html="<html>ok</html>"):
        self._html = html

    def render(self):
        return self._html


class FakeSsm:
    def __init__(self, values):
        self.values = values
        self.asked = []

    def get_parameter(self, Name, WithDecryption=False):
        self.asked.append((Name, WithDecryption))
        return {"Parameter": {"Value": self.values[Name]}}


def route(api, key):
    response = api.handle({"routeKey": key})
    return response["statusCode"], json.loads(response["body"])


@pytest.fixture
def s3():
    return FakeS3()


def make_api(s3, lambda_client=None):
    api = DashboardApi(s3, lambda_client or FakeLambda(), "bucket", "worker-fn")
    api._status = RefreshStatus(s3, "bucket", clock=lambda: NOW)
    return api


# ------------------------------------------------------------------ status

def test_without_a_status_file_nothing_has_run_yet(s3):
    assert RefreshStatus(s3, "bucket").read() == {"state": "idle", "dashboard": None}


def test_a_stale_run_does_not_block_a_new_one(s3):
    clock = [NOW]
    status = RefreshStatus(s3, "bucket", clock=lambda: clock[0])
    status.start()
    assert status.is_running()
    clock[0] = NOW + dt.timedelta(minutes=20)
    assert not status.is_running()


def test_a_failure_keeps_the_last_good_dashboard(s3):
    status = RefreshStatus(s3, "bucket", clock=lambda: NOW)
    status.finish("2026-11-10 12:00", "2026-11-10T11:30:00-03:00")
    status.start()
    failed = status.fail("PPI caido")
    assert failed["state"] == "error"
    assert failed["error"] == "PPI caido"
    assert failed["dashboard"]["generated_at"] == "2026-11-10 12:00"


# --------------------------------------------------------------------- api

def test_refresh_launches_the_worker_in_the_background(s3):
    lambdas = FakeLambda()
    code, body = route(make_api(s3, lambdas), "POST /refresh")
    assert code == 202
    assert body["state"] == "running"
    assert lambdas.invocations == [{"FunctionName": "worker-fn", "InvocationType": "Event"}]


def test_refresh_while_running_does_not_launch_another(s3):
    lambdas = FakeLambda()
    api = make_api(s3, lambdas)
    route(api, "POST /refresh")
    code, body = route(api, "POST /refresh")
    assert code == 409
    assert len(lambdas.invocations) == 1


def test_a_failed_launch_is_reported_and_unblocks_the_button(s3):
    api = make_api(s3, FakeLambda(error=RuntimeError("throttled")))
    code, body = route(api, "POST /refresh")
    assert code == 502
    assert body["state"] == "error"
    assert "throttled" in body["error"]


def test_dashboard_has_no_link_until_one_was_generated(s3):
    code, body = route(make_api(s3), "GET /dashboard")
    assert code == 200
    assert body["url"] is None


def test_dashboard_links_to_the_generated_html(s3):
    RefreshStatus(s3, "bucket").finish("2026-11-10 12:00", "2026-11-10T11:30:00-03:00")
    _, body = route(make_api(s3), "GET /dashboard")
    assert body["url"].startswith(f"https://s3/{DASHBOARD_KEY}")
    assert body["status"]["dashboard"]["generated_at"] == "2026-11-10 12:00"


def test_status_route(s3):
    code, body = route(make_api(s3), "GET /status")
    assert (code, body["state"]) == (200, "idle")


def test_unknown_route(s3):
    code, _ = route(make_api(s3), "DELETE /everything")
    assert code == 404


# ------------------------------------------------------------------ worker

ENV = {"DATA_BUCKET": "bucket", "PORTFOLIO_SHEET_ID": "SHEET", "PPI_PARAM": "/p/ppi",
       "GOOGLE_CREDENTIALS_PARAM": "/p/google"}


def make_worker(s3, build):
    ssm = FakeSsm({"/p/ppi": json.dumps({"public_key": "pub", "private_key": "priv"})})
    seen = {}

    def sheet_factory(settings):
        seen["settings"] = settings
        return FakeSheet(path="/tmp/portfolio.xlsx",
                         modified_time=dt.datetime(2026, 11, 10, 11, 30, tzinfo=AR))
    return DashboardWorker(s3, ssm, ENV, build_dashboard=build, sheet_factory=sheet_factory), ssm, seen


def test_the_worker_publishes_the_dashboard_and_reports_done(s3):
    built = []

    def build(settings, path):
        built.append(path)
        return FakeDashboard()

    worker, ssm, seen = make_worker(s3, build)
    result = worker.run()
    assert built == ["/tmp/portfolio.xlsx"]
    assert s3.objects[DASHBOARD_KEY]["Body"] == b"<html>ok</html>"
    assert s3.objects[DASHBOARD_KEY]["ContentType"].startswith("text/html")
    assert result["state"] == "done"
    assert s3.status()["dashboard"] == {"generated_at": "2026-11-10 12:00",
                                        "sheet_modified_at": "2026-11-10T11:30:00-03:00"}
    assert ("/p/ppi", True) in ssm.asked


def test_the_worker_takes_ppi_keys_and_sheet_from_its_configuration(s3):
    worker, _, seen = make_worker(s3, lambda settings, path: FakeDashboard())
    worker.run()
    settings = seen["settings"]
    assert (settings.public_key, settings.private_key) == ("pub", "priv")
    assert settings.sheet_id == "SHEET"


def test_a_failing_run_is_reported_and_leaves_the_old_dashboard(s3):
    s3.objects[DASHBOARD_KEY] = {"Body": b"<html>old</html>"}

    def build(settings, path):
        raise RuntimeError("PPI no responde")

    worker, _, _ = make_worker(s3, build)
    result = worker.run()
    assert result["state"] == "error"
    assert result["error"] == "PPI no responde"
    assert s3.objects[DASHBOARD_KEY]["Body"] == b"<html>old</html>"
