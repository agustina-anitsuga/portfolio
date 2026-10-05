# Portfolio Dashboard PPI

Genera un dashboard HTML interactivo de un portfolio de inversiones a partir de
una planilla de transacciones, consultando precios en vivo con la API de
[PPI (Portfolio Personal Inversiones)](https://www.portfoliopersonal.com/).

## Que hace

Lee una planilla Excel con las hojas `instrumentos`, `config`, `tx-usd`,
`tx-cedears`, `tx-merval` y `tx-rsu`, y produce un HTML autocontenido con una
pestana por tipo de instrumento (US Stocks, Cedears, Acciones Merval, RSU,
Bonos), mas una pestana general y una de transacciones.

Cada pestana muestra:

- Precio promedio de compra, precio actual, dinero invertido, valor actual,
  P&L en $ y en %, **todo en pesos (ARS) y en dolares (USD) a la vez**.
- Tratamiento de ventas: unidades vendidas, costo de ventas, ingreso de ventas
  y P&L realizado, tambien en ambas monedas.
- Buscador, filtro por sector, por tipo de instrumento, por anio de compra y
  por moneda, columnas ordenables por click, y graficos.

El filtro de **anio** esta en todas las pestanas y solo lista anios en los que
hubo compras. No esconde filas: **recalcula el portfolio** usando unicamente
las operaciones de ese anio. Si compraste SPY en 2025 y en 2026, al filtrar
2025 ves las unidades, el costo promedio, lo invertido y el P&L
correspondientes solo al tramo comprado en 2025.

El costo de lo vendido se calcula recorriendo **toda** la historia en orden
cronologico, asi que una venta de 2026 de unidades compradas en 2025 se valua
con el costo real de esas unidades y no con costo cero. Por eso los numeros de
cada anio suman exactamente el total del portfolio completo.

### Conversion ARS / USD

Costo, invertido y ventas se calculan **por operacion**, usando el monto real
cargado en cada moneda. Si a una operacion puntual le falta el monto en la otra
moneda, esa unica operacion se convierte al tipo de cambio de hoy como
aproximacion, y la posicion queda marcada en el dashboard para dejarlo claro.
El precio actual y el valor de mercado siempre usan el tipo de cambio actual.

## Instalacion

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`yfinance` es opcional: sin el, el script funciona igual, solo que pierde el
fallback de Yahoo Finance.

## Credenciales PPI

1. Entra a tu cuenta de PPI → Gestiones → Gestion de servicio API → activar.
2. Vas a obtener una Public Key y una Private Key.
3. Completa las claves y cargalas en tu entorno:

```bash
export PPI_PUBLIC_KEY=""
export PPI_PRIVATE_KEY=""
```

Sin credenciales el script igual corre: usa los fallbacks de precio.

### Orden de fallback de precios

1. PPI en vivo.
2. Yahoo Finance, solo para instrumentos en USD (US Stocks y RSU) — util cuando
   el mercado de EEUU esta cerrado. No aplica a Cedears, porque el precio de la
   Cedear en BYMA no es el de la accion subyacente.
3. Precio manual de la columna `Precio Manual` en la hoja `instrumentos`.
4. `no disponible` si nada de lo anterior funciono.

## Uso

```bash
python3 generate_dashboard.py portfolio.xlsx --out-html portfolio.html
```

## Archivos

| Archivo | Descripcion |
| --- | --- |
| `generate_dashboard.py` | Punto de entrada del generador |
| `portfolio/` | Implementacion (ver detalle abajo) |
| `portfolio.xlsx` | Planilla de transacciones (entrada) |
| `portfolio.html` | Dashboard generado (salida) |

> `portfolio.xlsx` y `portfolio.html` son datos de ejemplo, no posiciones
> reales: sirven de referencia del formato esperado. Reemplaza el `.xlsx` por
> tu propia planilla para generar tu dashboard.

## Estructura del codigo

| Modulo | Responsabilidad |
| --- | --- |
| `settings.py` | Credenciales y limites de pedidos, leidos del entorno |
| `market.py` | Los tipos de instrumento: hoja, moneda nativa y columnas |
| `app.py` | Arma las dependencias y devuelve el portfolio calculado |
| `cli.py`, `console_summary.py` | Linea de comandos y resumen final |
| `marketdata/` | Precios de PPI y Yahoo, tipo de cambio y orden de fallback |
| `workbook/` | Lectura de la planilla (instrumentos, config, tx-*) |
| `portfolio/` | Posiciones por costo promedio, metricas y reportes |
| `watchlist/` | Instrumentos vigilados, señales y puntaje |
| `output/` | Dashboard HTML (`output/assets/`) y planilla Excel |

El HTML no se arma con strings dentro del Python: `output/assets/` tiene la
plantilla, el CSS y los modulos JS por separado, y el renderer los concatena
con los datos embebidos.

## Watchlist

Instrumentos que seguis sin tenerlos en cartera. Se cargan en una hoja
`watchlist` del mismo `.xlsx`, con el ticker en la primera columna (el resto de
las columnas quedan libres para tus notas):

| Ticker | Notas |
| --- | --- |
| AAPL | mirar despues del balance |
| GOOGL | |

La solapa se genera con datos de Yahoo Finance y reproduce los dos metodos de
la planilla original:

- **Signal #1** ubica el precio dentro del rango de 52 semanas. El target de
  compra esta al 50% del rango y el de venta al 85%: por debajo del primero
  dice `Buy`, por encima del segundo `Sell`, en el medio `Hold`.
- **Signal #2** puntua cinco parametros (PE < 10, current ratio > 1, RSI < 50,
  deuda/equity < 1, price/book < 3) y traduce el puntaje: 5 `Strong buy`,
  4 `Buy`, 3 y 2 `Hold`, 1 `Sell`, 0 `Strong Sell`. Si falta algun parametro
  no hay puntaje, que es lo que pasa con los ETF.

Los tickers son los de Yahoo, que no siempre coinciden con los de Google
Finance: `BRK-B` y no `BRKB`, `META` y no `FB`, `BTC-USD` y no `BTC`.

La watchlist se calcula por defecto. Como es la parte mas lenta de la corrida
(dos consultas por instrumento vigilado) y no cambia nada del portfolio, se
puede saltear:

```bash
python3 generate_dashboard.py portfolio.xlsx --out-html portfolio.html --no-watchlist
```

La solapa Anual pide el precio de cierre de cada año de cada instrumento
(muchas consultas a PPI/Yahoo). Para saltearla, y dejarla vacia:

```bash
python3 generate_dashboard.py portfolio.xlsx --out-html portfolio.html --no-annual
```

## Tests

```bash
pip install -r requirements-dev.txt
python3 -m pytest
```

Hay un archivo de test por clase, en `tests/` con la misma estructura que el
paquete. Los tests no salen a la red nunca: PPI y Yahoo se reemplazan por los
dobles de `tests/doubles.py`, asi que un test que falla es un bug de verdad y
no un mercado cerrado.
