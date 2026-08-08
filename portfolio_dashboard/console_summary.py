# -*- coding: utf-8 -*-
"""Summary printed when the run finishes."""

import sys

from .market import Market


class ConsoleSummary:
    """Reports what was generated, what ended up without a price and why, so
    the spreadsheet or the credentials can be fixed without guessing."""

    def __init__(self, snapshot, out=sys.stdout):
        self._snapshot = snapshot
        self._out = out

    def print_report(self, generated_paths):
        for path in generated_paths:
            self._line(f"Listo: {path}")
        self._print_positions()
        self._print_fx()

    def _print_positions(self):
        unpriced = self._snapshot.unpriced_rows()
        self._line(f"  {self._snapshot.position_count} posiciones procesadas, "
                   f"{len(unpriced)} sin precio disponible.")
        if not unpriced:
            return
        listed = ", ".join(f"{r['key']} ({Market.get(r['market']).label})" for r in unpriced)
        self._line(f"    Sin precio: {listed}")
        self._line('    -> Cargales un precio en la columna "Precio Manual" de la hoja '
                   "instrumentos, o revisa que el Key coincida exactamente con el ticker "
                   "real (PPI y/o Yahoo Finance) para que puedan cotizar solos.")
        for row in unpriced:
            if row["price_debug_note"]:
                self._line(f"      - {row['key']}: {row['price_debug_note']}")

    def _print_fx(self):
        fx = self._snapshot.fx
        self._line(f"  Tipo de cambio: {fx.value if fx else 'N/D'} ({fx.source})")
        if not fx:
            self._line("    -> Ni PPI (dolar MEP AL30/AL30D) ni la hoja config tienen un tipo de "
                       "cambio disponible. Revisa tus credenciales PPI_PUBLIC_KEY/PPI_PRIVATE_KEY, "
                       'o cargue un valor en config!B2 ("USD/ARS Manual") como respaldo. Mientras '
                       "tanto, las columnas convertidas a la otra moneda quedan vacias.")

    def _line(self, text):
        print(text, file=self._out)
