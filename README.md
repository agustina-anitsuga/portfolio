# Portfolio Dashboard PPI

Genera un dashboard HTML interactivo de un portfolio de inversiones a partir de
una planilla de transacciones, consultando precios en vivo con la API de
[PPI (Portfolio Personal Inversiones)](https://www.portfoliopersonal.com/).

## Que hace

Lee una planilla Excel con las hojas `instrumentos`, `config`, `tx-usd`,
`tx-cedears`, `tx-merval` y `tx-rsu`, y produce un HTML autocontenido con una
pestana por tipo de instrumento (US Stocks, Cedears, Acciones Merval, RSU JPM,
Bonos), mas una pestana general y una de transacciones.

Cada pestana muestra:

- Precio promedio de compra, precio actual, dinero invertido, valor actual,
  P&L en $ y en %, **todo en pesos (ARS) y en dolares (USD) a la vez**.
- Tratamiento de ventas: unidades vendidas, costo de ventas, ingreso de ventas
  y P&L realizado, tambien en ambas monedas.
- Buscador, filtro por sector, por tipo de instrumento y por moneda, columnas
  ordenables por click, y graficos.

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
3. Copia `setkeys.example.txt` a `setkeys.txt`, completa las claves y cargalas:

```bash
cp setkeys.example.txt setkeys.txt
# editar setkeys.txt con tus claves
source setkeys.txt
```

`setkeys.txt` esta en `.gitignore`, asi que tus claves no se commitean.

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
| `setkeys.example.txt` | Plantilla de credenciales PPI |
