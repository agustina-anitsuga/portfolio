# -*- coding: utf-8 -*-
"""State of the regeneration, shared by the API and the worker through S3."""

import datetime as dt
import json

STATUS_KEY = "status.json"
DASHBOARD_KEY = "dashboard/index.html"
# the worker times out at 15 minutes; a "running" older than this is a run
# that died without reporting, and must not block the button forever.
STALE_AFTER = dt.timedelta(minutes=16)


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


class RefreshStatus:
    """A small JSON document in the data bucket:

        state        idle | running | done | error
        started_at   when the current/last run started (ISO, UTC)
        finished_at  when it ended
        error        why it failed, when state == error
        dashboard    {generated_at, sheet_modified_at} of the last good run

    The last good dashboard survives a failed run, so the page keeps showing
    it next to the error."""

    def __init__(self, s3, bucket, clock=utc_now):
        self._s3 = s3
        self._bucket = bucket
        self._clock = clock

    def read(self):
        try:
            body = self._s3.get_object(Bucket=self._bucket, Key=STATUS_KEY)["Body"].read()
        except self._s3.exceptions.NoSuchKey:
            return {"state": "idle", "dashboard": None}
        return json.loads(body)

    def is_running(self, status=None):
        status = status or self.read()
        if status.get("state") != "running":
            return False
        started = dt.datetime.fromisoformat(status["started_at"])
        return self._clock() - started < STALE_AFTER

    def start(self):
        status = self.read()
        status.update(state="running", started_at=self._stamp(), finished_at=None, error=None)
        return self._write(status)

    def finish(self, generated_at, sheet_modified_at):
        status = self.read()
        status.update(state="done", finished_at=self._stamp(), error=None,
                      dashboard={"generated_at": generated_at,
                                 "sheet_modified_at": sheet_modified_at})
        return self._write(status)

    def fail(self, message):
        status = self.read()
        status.update(state="error", finished_at=self._stamp(), error=message)
        return self._write(status)

    def _stamp(self):
        return self._clock().isoformat(timespec="seconds")

    def _write(self, status):
        self._s3.put_object(Bucket=self._bucket, Key=STATUS_KEY,
                            Body=json.dumps(status).encode("utf-8"),
                            ContentType="application/json", CacheControl="no-store")
        return status
