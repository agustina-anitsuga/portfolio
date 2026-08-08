# -*- coding: utf-8 -*-
"""Price fallback via Yahoo Finance."""

try:
    import yfinance as yf
    HAVE_YFINANCE = True
except ImportError:
    HAVE_YFINANCE = False

NOT_INSTALLED = "yfinance no esta instalado (pip install yfinance)"


class YahooMarketData:
    """Second source for USD instruments that PPI does not quote, or that have
    no price because the US market is closed (PPI often only has data for USD
    instruments during the session). It needs no API key and returns the last
    available price even when the market is closed.

    It tries several routes because the shape of fast_info/info changes quite a
    bit between yfinance versions.
    """

    def price(self, ticker):
        """(price, reason_if_it_failed)."""
        if not HAVE_YFINANCE:
            return None, NOT_INSTALLED
        last_error = None
        for probe in (self._from_fast_info, self._from_info, self._from_history):
            price, error = probe(ticker)
            if price is not None:
                return price, None
            last_error = error or last_error
        return None, self._failure_reason(ticker, last_error)

    @staticmethod
    def _failure_reason(ticker, last_error):
        reason = f"Yahoo Finance no devolvio precio para '{ticker}'"
        return reason + f" ({last_error})" if last_error is not None else reason

    @staticmethod
    def _from_fast_info(ticker):
        try:
            fast_info = yf.Ticker(ticker).fast_info
        except Exception as e:
            return None, e
        for key in ("last_price", "lastPrice", "regularMarketPrice"):
            try:
                value = fast_info[key]
            except Exception:
                value = getattr(fast_info, key, None)
            if value:
                return float(value), None
        return None, None

    @staticmethod
    def _from_info(ticker):
        try:
            info = yf.Ticker(ticker).info
        except Exception as e:
            return None, e
        if isinstance(info, dict):
            for key in ("regularMarketPrice", "currentPrice", "previousClose"):
                if info.get(key):
                    return float(info[key]), None
        return None, None

    @staticmethod
    def _from_history(ticker):
        try:
            history = yf.Ticker(ticker).history(period="5d")
        except Exception as e:
            return None, e
        if history is not None and not history.empty:
            closes = history["Close"].dropna()
            if len(closes):
                return float(closes.iloc[-1]), None
        return None, None
