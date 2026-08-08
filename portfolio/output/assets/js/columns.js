const MARKET_KEYS = ['general', 'usd', 'cedears', 'merval', 'rsu', 'bonds', 'tx'];
const TAB_LABELS = { general: 'General', usd: 'US Stocks', cedears: 'Cedears', merval: 'Acciones Merval', rsu: 'RSU', bonds: 'Bonos', tx: 'Transacciones' };

// "real" portfolios (not general/tx) -- used to build the combined totals of
// the General tab without repeating the list everywhere.
const PORTFOLIO_KEYS = ['usd', 'cedears', 'merval', 'rsu', 'bonds'];

const tabsEl = document.getElementById('tabs');
const pagesEl = document.getElementById('pages');

// Each table shows ONE currency at a time (the base columns plus the 10
// "dual" columns resolved by that tab own currency filter).
const DEFAULT_CURRENCY = { general: 'usd', usd: 'usd', cedears: 'ars', merval: 'ars', rsu: 'usd', bonds: 'ars' };

const COLUMNS_BASE = [
  {key:'key', label:'Ticker'},
  {key:'name', label:'Nombre'},
  {key:'sector', label:'Sector'},
  {key:'instrument_type', label:'Tipo'},
  {key:'units', label:'Unid.', num:true},
  {key:'units_sold', label:'Unid. Vend.', num:true},
  // drawn as a line (spark), but the value is still the % -- that is what
  // sorts the column on click and what shows up in the tooltip.
  {key:'trend_30d', label:'Tend. 30d', num:true, pct:true, spark:true},
];
const COLUMNS_DUAL = [
  {key:'pct_portfolio', label:'% Portfolio', num:true, pct:true, dual:true},
  {key:'avg_cost', label:'Prom. Compra', num:true, dual:true},
  {key:'price', label:'Precio Actual', num:true, dual:true},
  {key:'invested', label:'Invertido', num:true, dual:true},
  {key:'value', label:'Valor Actual', num:true, dual:true},
  {key:'pl_abs', label:'P&L $', num:true, pl:true, dual:true},
  {key:'pl_pct', label:'P&L %', num:true, pl:true, pct:true, dual:true},
  {key:'cost_of_sales', label:'Costo Ventas', num:true, dual:true},
  {key:'income_from_sales', label:'Ingreso Ventas', num:true, dual:true},
  {key:'realized_abs', label:'P&L Realiz. $', num:true, pl:true, dual:true},
  {key:'realized_pct', label:'P&L Realiz. %', num:true, pl:true, pct:true, dual:true},
];

// The general tab shows ONE row per portfolio (USD/Cedears/Merval), not one
// row per product -- they are the totals of each table above.
const GENERAL_COLUMNS = [
  {key:'label', label:'Portfolio'},
  {key:'count', label:'Instrumentos', num:true},
  {key:'pct_portfolio', label:'% Portfolio', num:true, pct:true},
  {key:'unpriced', label:'Sin Precio', num:true},
  {key:'invested', label:'Invertido', num:true, showCurrency:true},
  {key:'value', label:'Valor Actual', num:true, showCurrency:true},
  {key:'pl_abs', label:'P&L $', num:true, pl:true, showCurrency:true},
  {key:'pl_pct', label:'P&L %', num:true, pl:true, pct:true, showCurrency:true},
  {key:'realized', label:'P&L Realizado', num:true, pl:true, showCurrency:true},
];

// "Transacciones" tab: one row per trade (BUY/SELL), not aggregated.
const TX_COLUMNS = [
  {key:'ticker', label:'Ticker'},
  {key:'market', label:'Tipo'},
  {key:'op', label:'Operacion'},
  {key:'date', label:'Fecha'},
  {key:'units', label:'Unidades', num:true},
  // everything in ARS first, then everything in USD (same order as the
  // per-instrument-type tables).
  {key:'price_ars', label:'Precio Operacion (ARS)', num:true},
  {key:'amount_ars', label:'Monto (ARS)', num:true},
  {key:'current_price_ars', label:'Cotizacion Actual (ARS)', num:true},
  {key:'pl_pct_ars', label:'P&L % (ARS)', num:true, pct:true, pl:true},
  {key:'price_usd', label:'Precio Operacion (USD)', num:true},
  {key:'amount_usd', label:'Monto (USD)', num:true},
  {key:'current_price_usd', label:'Cotizacion Actual (USD)', num:true},
  {key:'pl_pct_usd', label:'P&L % (USD)', num:true, pct:true, pl:true},
];

function getCols(marketKey) {
  if (marketKey === 'general') return GENERAL_COLUMNS;
  if (marketKey === 'tx') return TX_COLUMNS;
  return [...COLUMNS_BASE, ...COLUMNS_DUAL];
}

