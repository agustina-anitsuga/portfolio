# -*- coding: utf-8 -*-
"""Render of the self-contained HTML dashboard."""

import json
from pathlib import Path

from .dashboard_payload import DashboardPayload

ASSETS = Path(__file__).parent / "assets"


class HtmlDashboard:
    """Builds a single HTML file with the styles, the code and the data
    embedded: it opens with a double click, no server and no dependencies."""

    # order matters: the modules are concatenated into a single <script>.
    JS_MODULES = ("format.js", "columns.js", "rows.js", "kpis.js",
                  "page.js", "table.js", "charts.js", "app.js")

    def __init__(self, snapshot, now=None):
        self._payload = DashboardPayload(snapshot, now)

    def render(self):
        page = self._asset("dashboard.html")
        page = page.replace("__STYLES__", self._asset("dashboard.css"))
        page = page.replace("__SCRIPT__", self._script())
        return page.replace("__DATA_JSON__", self._data_json())

    def write(self, path):
        Path(path).write_text(self.render(), encoding="utf-8")

    def _script(self):
        return "".join(self._asset(f"js/{module}") for module in self.JS_MODULES)

    def _data_json(self):
        return json.dumps(self._payload.as_dict(), ensure_ascii=False)

    @staticmethod
    def _asset(name):
        return (ASSETS / name).read_text(encoding="utf-8")
