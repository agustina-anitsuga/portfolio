# -*- coding: utf-8 -*-
"""Metodo #2: puntaje por parametros fundamentales."""

# (campo, umbral, aprueba_si_es_menor) -- las cinco reglas de la planilla
RULES = (
    ("pe", 10, True),
    ("current_ratio", 1, False),
    ("rsi", 50, True),
    ("debt_to_equity", 1, True),
    ("price_to_book", 3, True),
)

SIGNALS = {5: "Strong buy", 4: "Buy", 3: "Hold", 2: "Hold", 1: "Sell", 0: "Strong Sell"}


class ParameterScore:
    """Un punto por cada parametro que pasa su umbral, de 0 a 5.

    Si falta alguno no hay puntaje: es lo que pasa con los ETF, que no tienen
    PE ni deuda. La planilla original contaba los faltantes como cero, y un
    cero pasa todos los umbrales de "menor que", asi que un instrumento sin
    datos terminaba con puntaje alto. Aca se prefiere no opinar.
    """

    def __init__(self, fundamentals):
        self._fundamentals = fundamentals

    @property
    def complete(self):
        return all(getattr(self._fundamentals, field) is not None for field, _, _ in RULES)

    @property
    def score(self):
        if not self.complete:
            return None
        return sum(self._passes(field, threshold, lower_is_better)
                   for field, threshold, lower_is_better in RULES)

    def _passes(self, field, threshold, lower_is_better):
        value = getattr(self._fundamentals, field)
        return int(value < threshold if lower_is_better else value > threshold)

    @property
    def signal(self):
        return SIGNALS.get(self.score)
