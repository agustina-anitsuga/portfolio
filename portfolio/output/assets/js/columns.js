const MARKET_KEYS = ['general', 'usd', 'cedears', 'merval', 'rsu', 'bonds', 'tx', 'annual', 'watch'];
const TAB_LABELS = { general: 'General', usd: 'US Stocks', cedears: 'Cedears', merval: 'Acciones Merval', rsu: 'RSU', bonds: 'Bonos', tx: 'Transacciones', annual: 'Anual', watch: 'Watchlist' };

// "real" portfolios (not general/tx) -- used to build the combined totals of
// the General tab without repeating the list everywhere.
const PORTFOLIO_KEYS = ['usd', 'cedears', 'merval', 'rsu', 'bonds'];

const tabsEl = document.getElementById('tabs');
const pagesEl = document.getElementById('pages');

// Each table shows ONE currency at a time (the base columns plus the 10
// "dual" columns resolved by that tab own currency filter).
const DEFAULT_CURRENCY = { general: 'usd', usd: 'usd', cedears: 'ars', merval: 'ars', rsu: 'usd', bonds: 'ars', annual: 'usd' };

const COLUMNS_BASE = [
  {key:'key', label:'Ticker'},
  {key:'name', label:'Nombre'},
  {key:'sector', label:'Sector'},
  {key:'instrument_type', label:'Tipo'},
  {key:'units', label:'Unid.', num:true},
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
  {key:'units_sold', label:'Unid. Vend.', num:true},
  {key:'cost_of_sales', label:'Costo Ventas', num:true, dual:true},
  {key:'income_from_sales', label:'Ingreso Ventas', num:true, dual:true},
  {key:'realized_abs', label:'P&L Realiz. $', num:true, pl:true, dual:true},
  {key:'realized_pct', label:'P&L Realiz. %', num:true, pl:true, pct:true, dual:true},
];

// "Anual" tab: one row per year with purchases. Each year is its own scope
// (the same one the year filter uses): what was bought that year, gross and
// net of what was sold that year, what that net position was worth at the
// close of the year, and what it is worth today.
const ANNUAL_COLUMNS = [
  {key:'year', label:'Año'},
  {key:'units_bought', label:'Unid. Compradas', num:true},
  {key:'units', label:'Unid. al Cierre', num:true},
  {key:'invested_gross', label:'Compras', num:true, dual:true},
  {key:'invested_net', label:'Invertido Neto', num:true, dual:true},
  {key:'close_price', label:'Precio al Cierre', num:true, dual:true},
  {key:'close_value', label:'Valor al Cierre', num:true, dual:true},
  {key:'year_pct', label:'P&L % del Año', num:true, pl:true, pct:true, dual:true},
  {key:'gain', label:'P&L $ a la Fecha', num:true, pl:true, dual:true},
  {key:'gain_pct', label:'P&L % a la Fecha', num:true, pl:true, pct:true, dual:true},
];

// Only bonds have these: they come from PPI's bond calculator. TIR, parity and
// duration are computed against today's exchange rate, because a bond quoted
// in pesos can pay its coupons in dollars.
const BOND_COLUMNS = [
  {key:'bond_tir', label:'TIR', num:true, pct:true},
  {key:'bond_coupon', label:'Cupon', num:true, pct:true},
  {key:'bond_next_payment', label:'Prox. Pago'},
  {key:'bond_maturity', label:'Vencimiento'},
  {key:'bond_duration', label:'Duration', num:true},
  {key:'bond_parity', label:'Paridad', num:true, pct:true},
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

// Solapa "Watchlist": instrumentos que se siguen sin tenerlos en cartera, con
// las dos señales de la planilla original. Metodo #1 ubica el precio dentro
// del rango de 52 semanas; metodo #2 puntua cinco parametros fundamentales.
// Los dos metodos se distinguen por color en una fila de encabezado que va
// arriba de los nombres de columna, igual que en la planilla original.
const COLUMN_GROUPS = {
  m1: 'Metodo #1: precio dentro del rango de 52 semanas',
  m2: 'Metodo #2: analisis de parametros',
};

const WATCHLIST_COLUMNS = [
  {key:'ticker', label:'Ticker'},
  {key:'name', label:'Nombre'},
  {key:'price', label:'Precio', num:true},
  {key:'change_pct', label:'% Dia', num:true, pct:true, pl:true},
  {key:'market_cap', label:'Market Cap (B)', num:true},
  {key:'eps', label:'EPS', num:true},
  {key:'signal_price', label:'Signal', signal:true, group:'m1'},
  {key:'low52', label:'Min. 52s', num:true, group:'m1'},
  {key:'high52', label:'Max. 52s', num:true, group:'m1'},
  {key:'target_buy', label:'Target Compra', num:true, group:'m1'},
  {key:'target_sell', label:'Target Venta', num:true, group:'m1'},
  {key:'signal_score', label:'Signal', signal:true, group:'m2'},
  {key:'earnings', label:'Earnings', group:'m2'},
  {key:'pe', label:'PE', num:true, group:'m2'},
  {key:'current_ratio', label:'Current Ratio', num:true, group:'m2'},
  {key:'rsi', label:'RSI (14)', num:true, group:'m2'},
  {key:'debt_to_equity', label:'Debt/Equity', num:true, group:'m2'},
  {key:'price_to_book', label:'Price/Book', num:true, group:'m2'},
  {key:'score', label:'Score', num:true, group:'m2'},
];

function getCols(marketKey) {
  if (marketKey === 'general') return GENERAL_COLUMNS;
  if (marketKey === 'tx') return TX_COLUMNS;
  if (marketKey === 'annual') return ANNUAL_COLUMNS;
  if (marketKey === 'watch') return WATCHLIST_COLUMNS;
  if (marketKey === 'bonds') return [...COLUMNS_BASE, ...BOND_COLUMNS, ...COLUMNS_DUAL];
  return [...COLUMNS_BASE, ...COLUMNS_DUAL];
}

