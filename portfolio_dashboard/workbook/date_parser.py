# -*- coding: utf-8 -*-
"""Reading the dates in the transaction sheets."""

import datetime as dt


class DateParser:
    """The sheets mix formats depending on how each row was entered: real Excel
    date cells, ISO ('2026-11-06') and dd/mm/yyyy ('30/09/2025'), so all three
    have to be handled. When the date comes as text and does NOT start with the
    year, day-first (local format) is assumed, which is how the sheets are
    filled in."""

    SEPARATORS = ("/", "-", ".")

    @classmethod
    def parse(cls, value):
        """(year, month, day), or None when it cannot be read."""
        if value is None:
            return None
        if isinstance(value, (dt.datetime, dt.date)):
            return (value.year, value.month, value.day)
        parts = cls._split(str(value).strip())
        if parts is None:
            return None
        return cls._validated(parts)

    @classmethod
    def _split(cls, text):
        if not text:
            return None
        text = text.split()[0]  # drop the time when it comes attached ('2025-01-15 00:00:00')
        for separator in cls.SEPARATORS:
            text = text.replace(separator, " ")
        parts = text.split()
        if len(parts) < 3 or not all(p.isdigit() for p in parts[:3]):
            return None
        return parts[:3]

    @staticmethod
    def _validated(parts):
        a, b, c = (int(p) for p in parts)
        year, month, day = (a, b, c) if len(parts[0]) == 4 else (c, b, a)
        if year < 100:
            return None                 # 2-digit year: ambiguous, discarded
        if not (1 <= month <= 12 and 1 <= day <= 31):
            return None
        return (year, month, day)

    @classmethod
    def year(cls, value):
        """The year ('2024') of a date, or None. Returned as a string so it
        compares directly against the value of a <select> in the HTML."""
        parsed = cls.parse(value)
        return str(parsed[0]) if parsed else None

    @classmethod
    def iso(cls, value):
        """Dates ALWAYS as YYYY-MM-DD. That is what makes the "Fecha" column
        sort properly: the table sorts strings, and in that format the
        alphabetical order matches the chronological one."""
        if value is None:
            return ""
        parsed = cls.parse(value)
        if parsed is None:
            return str(value)           # unrecognized format: shown as it came
        return "%04d-%02d-%02d" % parsed
