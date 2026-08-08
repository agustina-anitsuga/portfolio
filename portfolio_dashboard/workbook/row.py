# -*- coding: utf-8 -*-
"""Forgiving cell access: spreadsheet rows do not always carry every optional
column."""


def cell(row, index):
    return row[index] if index < len(row) else None


def number(row, index):
    value = cell(row, index)
    return float(value) if value is not None else None
