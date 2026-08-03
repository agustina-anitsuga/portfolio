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

El filtro de **anio de compra** esta en todas las pestanas y solo lista anios
en los que hubo compras. Una posicion comprada en varios anios aparece en cada
uno de ellos y se muestra entera: el filtro responde "que compre en 2024", no
"cuanto de lo que tengo hoy corresponde a 2024".

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
python3 generar_dashboard_ppi.py portfolio.xlsx --out-html portfolio.html
```

## Archivos

| Archivo | Descripcion |
| --- | --- |
| `generar_dashboard_ppi.py` | Script generador del dashboard |
| `portfolio.xlsx` | Planilla de transacciones (entrada) |
| `portfolio.html` | Dashboard generado (salida) |

> `portfolio.xlsx` y `portfolio.html` son datos de ejemplo, no posiciones
> reales: sirven de referencia del formato esperado. Reemplaza el `.xlsx` por
> tu propia planilla para generar tu dashboard.
