# -*- coding: utf-8 -*-
"""Lambda behind the HTTP API. Every route is already authenticated: API
Gateway validates the Cognito JWT before the call gets here.

    GET  /status     state of the regeneration
    GET  /dashboard  state + a short-lived link to the generated HTML
    POST /refresh    starts a regeneration in the background (202)

It only depends on boto3 (bundled with the Lambda runtime), so it ships
without pandas & co. and starts fast."""

import json
import os

from .status import DASHBOARD_KEY, RefreshStatus

LINK_SECONDS = 300


class DashboardApi:

    def __init__(self, s3, lambda_client, bucket, worker_function):
        self._s3 = s3
        self._lambda = lambda_client
        self._bucket = bucket
        self._worker = worker_function
        self._status = RefreshStatus(s3, bucket)

    def handle(self, event):
        route = event.get("routeKey", "")
        if route == "GET /status":
            return _response(200, self._status.read())
        if route == "GET /dashboard":
            return _response(200, self._dashboard())
        if route == "POST /refresh":
            return self._refresh()
        return _response(404, {"error": f"ruta desconocida: {route}"})

    def _dashboard(self):
        status = self._status.read()
        url = None
        if status.get("dashboard"):
            url = self._s3.generate_presigned_url(
                "get_object", Params={"Bucket": self._bucket, "Key": DASHBOARD_KEY},
                ExpiresIn=LINK_SECONDS)
        return {"status": status, "url": url}

    def _refresh(self):
        status = self._status.read()
        if self._status.is_running(status):
            return _response(409, status)
        status = self._status.start()
        try:
            self._lambda.invoke(FunctionName=self._worker, InvocationType="Event")
        except Exception as error:
            return _response(502, self._status.fail(f"No se pudo lanzar el recalculo: {error}"))
        return _response(202, status)


def _response(code, body):
    return {"statusCode": code, "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body)}


_api = None


def handler(event, context):
    global _api
    if _api is None:
        import boto3
        _api = DashboardApi(boto3.client("s3"), boto3.client("lambda"),
                            os.environ["DATA_BUCKET"], os.environ["WORKER_FUNCTION"])
    return _api.handle(event)
