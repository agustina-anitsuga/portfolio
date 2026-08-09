# -*- coding: utf-8 -*-
"""Los datos de la watchlist, via Yahoo Finance."""

from .fundamentals import BILLION, Fundamentals
from .relative_strength_index import RelativeStrengthIndex

try:
    import yfinance as yf
    HAVE_YFINANCE = True
except ImportError:
    HAVE_YFINANCE = False

HISTORY_PERIOD = "3mo"      # enough closes to seed and smooth an RSI(14)
DEBT_TO_EQUITY_SCALE = 100.0


class YahooFundamentals:
    """Replaces the two sources of the original spreadsheet -- GOOGLEFINANCE
    for the quote and Finviz for the ratios -- with the one API the dashboard
    already talks to.

    Best-effort per instrument: a ticker that fails leaves its row empty
    instead of stopping the run.
    """

    def __init__(self, rsi=None):
        self._rsi = rsi or RelativeStrengthIndex()

    def of(self, ticker):
        if not HAVE_YFINANCE:
            return Fundamentals.empty()
        info = self._info(ticker)
        if info is None:
            return Fundamentals.empty()
        return Fundamentals(
            name=info.get("longName") or info.get("shortName"),
            price=_number(info.get("currentPrice") or info.get("regularMarketPrice")),
            change_pct=_number(info.get("regularMarketChangePercent")),
            market_cap=_scaled(info.get("marketCap"), BILLION),
            eps=_number(info.get("trailingEps")),
            low52=_number(info.get("fiftyTwoWeekLow")),
            high52=_number(info.get("fiftyTwoWeekHigh")),
            earnings=self._earnings(ticker),
            pe=_number(info.get("trailingPE")),
            current_ratio=_number(info.get("currentRatio")),
            rsi=self._rsi.of(self._closes(ticker)),
            # Yahoo answers a percentage (78.4) where Finviz answers a ratio
            # (0.78), and the scoring rule is written for the ratio.
            debt_to_equity=_scaled(info.get("debtToEquity"), DEBT_TO_EQUITY_SCALE),
            price_to_book=_number(info.get("priceToBook")),
        )

    @staticmethod
    def _info(ticker):
        try:
            info = yf.Ticker(ticker).info
        except Exception:
            return None
        return info if isinstance(info, dict) else None

    @staticmethod
    def _closes(ticker):
        try:
            history = yf.Ticker(ticker).history(period=HISTORY_PERIOD)
        except Exception:
            return []
        if history is None or history.empty:
            return []
        return history["Close"].dropna().tolist()

    @staticmethod
    def _earnings(ticker):
        """Next earnings date, as ISO so the column sorts."""
        try:
            calendar = yf.Ticker(ticker).calendar
        except Exception:
            return None
        dates = calendar.get("Earnings Date") if isinstance(calendar, dict) else None
        if not dates:
            return None
        first = dates[0] if isinstance(dates, (list, tuple)) else dates
        return str(first)[:10] or None


def _number(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _scaled(value, divisor):
    number = _number(value)
    return number / divisor if number is not None else None
