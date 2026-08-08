// Rows of a portfolio for a given year. This is NOT a subset of the full
// rows: it is the portfolio recomputed in Python using only that year trades,
// so units, average cost, invested amount and P&L correspond exclusively to
// what was bought/sold that year. '' = everything.
function marketRows(m, year) {
  if (!year) return DATA.markets[m].rows;
  return DATA.markets[m].rows_by_year[year] || [];
}

// Rows of a portfolio as the general tab sees them, honouring its own year
// filter.
function generalMarketRows(m) {
  return marketRows(m, currentYear('general'));
}

function _unpricedCount(rows) {
  // same criterion as Kpis in Python: no value in either currency.
  return rows.filter(r => r.value_ars === null && r.value_usd === null).length;
}

function buildGeneralRows(currency) {
  const totalValue = computeGeneralTotals(currency).value;
  return PORTFOLIO_KEYS.map(m => {
    const rows = generalMarketRows(m);
    const k = computeMarketKpis(rows, currency);
    return {
      label: TAB_LABELS[m],
      market: m,
      count: rows.length,
      unpriced: _unpricedCount(rows),
      invested: k.invested, value: k.value,
      pct_portfolio: totalValue ? (k.value / totalValue * 100) : null,
      pl_abs: k.pl_abs,
      pl_pct: k.pl_pct, realized: k.realized,
    };
  });
}

// Combined totals of every portfolio, for the pills at the top of the general
// tab (the same total the "Total" row used to show).
function computeGeneralTotals(currency) {
  const parts = PORTFOLIO_KEYS.map(m => computeMarketKpis(generalMarketRows(m), currency));
  const invested = parts.reduce((s, k) => s + (k.invested || 0), 0);
  const value = parts.reduce((s, k) => s + (k.value || 0), 0);
  const pl_abs = value - invested;
  const pl_pct = invested ? (pl_abs / invested * 100) : null;
  const realized = parts.reduce((s, k) => s + (k.realized || 0), 0);
  return { invested, value, pl_abs, pl_pct, realized };
}

function computeGeneralUnpriced() {
  return PORTFOLIO_KEYS.reduce((s, m) => s + _unpricedCount(generalMarketRows(m)), 0);
}

function _sumOrNone(rows, key) {
  let has = false, sum = 0;
  for (const r of rows) {
    const v = r[key];
    if (v !== null && v !== undefined) { has = true; sum += v; }
  }
  return has ? sum : null;
}

// Recomputes the KPIs of a per-instrument-type tab from any subset of rows
// (e.g. whatever is left after searching or filtering by sector), so the pills
// at the top always reflect what the table below is showing -- same logic as
// the Kpis class in Python.
function computeMarketKpis(rows, currency) {
  const invested = _sumOrNone(rows, `invested_${currency}`);
  const value = _sumOrNone(rows, `value_${currency}`);
  const pl_abs = (value !== null && invested !== null) ? (value - invested) : null;
  const pl_pct = (pl_abs !== null && invested) ? (pl_abs / invested * 100) : null;
  const realized = _sumOrNone(rows, `realized_abs_${currency}`);
  return { invested, value, pl_abs, pl_pct, realized };
}

function cellValue(r, c, currency) {
  return c.dual ? r[`${c.key}_${currency}`] : r[c.key];
}

