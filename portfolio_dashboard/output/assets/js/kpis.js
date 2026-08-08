function buildKpiGroup(k) {
  const items = [
    ['Invertido', fmt(k.invested), ''],
    ['Valor Actual', fmt(k.value), ''],
    ['P&L No Realiz.', fmt(k.pl_abs), plClass(k.pl_abs)],
    ['P&L No Realiz. %', fmtPct(k.pl_pct), plClass(k.pl_pct)],
    ['P&L Realizado', fmt(k.realized), plClass(k.realized)],
  ];
  return `<div class="kpis">${items.map(([label,val,cls]) =>
    `<div class="kpi"><div class="label">${label}</div><div class="val ${cls}">${val}</div></div>`
  ).join('')}</div>`;
}

function renderKpis(marketKey, filteredRows) {
  const currency = tableState[marketKey].currency;
  const k = marketKey === 'general'
    ? computeGeneralTotals(currency)
    : computeMarketKpis(filteredRows || filterRows(marketKey), currency);
  const title = currency === 'ars' ? 'En Pesos (ARS)' : 'En Dolares (USD)';
  document.getElementById(`kpis-${marketKey}`).innerHTML =
    `<h3 class="kpi-title">${title}</h3>${buildKpiGroup(k)}`;
}

function uniqueSorted(rows, key) {
  return [...new Set(rows.map(r => r[key]).filter(v => v !== null && v !== undefined && v !== ''))].sort();
}

// "Instrumentos sin precio" has to follow the slice currently on screen (year
// + search + sector), not the portfolio total.
function renderUnpricedNote(marketKey, filteredRows) {
  const el = document.getElementById(`unpricednote-${marketKey}`);
  if (!el) return;
  const n = marketKey === 'general' ? computeGeneralUnpriced() : _unpricedCount(filteredRows);
  el.textContent = n > 0 ? `Instrumentos sin precio: ${n}` : '';
}

// Warning about an inconsistency in the spreadsheet: more units were sold than
// were ever bought, so part of that sale has no purchase cost and its realized
// P&L ends up inflated. It has nothing to do with the year filter.
function renderScopeNote(marketKey, filteredRows) {
  const el = document.getElementById(`scopenote-${marketKey}`);
  if (!el) return;
  const source = marketKey === 'general'
    ? PORTFOLIO_KEYS.flatMap(m => generalMarketRows(m))
    : filteredRows;
  const affected = [...new Set(source.filter(r => r.oversold).map(r => r.key))];
  if (!affected.length) { el.style.display = 'none'; el.textContent = ''; return; }
  el.style.display = '';
  el.textContent = `Revisa las transacciones de ${affected.join(', ')}: figuran mas unidades vendidas que compradas, `
    + `asi que parte de esa venta queda sin costo de compra y su P&L realizado aparece inflado.`;
}

// Years with purchases in any portfolio (Python already sorts them from newest
// to oldest). Used by the general and transactions tabs, which do not belong to
// a single instrument type.
function allBuyYears() {
  return DATA.years;
}

// Years THAT portfolio actually had activity in, so no option leaves the table
// empty.
function marketYears(m) {
  return DATA.years.filter(y => (DATA.markets[m].rows_by_year[y] || []).length > 0);
}

function yearSelectHtml(marketKey, years) {
  return `<select data-role="year" data-market="${marketKey}">
        <option value="">Todos los anios</option>
        ${years.map(y => `<option value="${y}">Comprado en ${y}</option>`).join('')}
      </select>`;
}

// Year selected in that tab ('' = no filter).
function currentYear(marketKey) {
  const el = document.querySelector(`[data-role="year"][data-market="${marketKey}"]`);
  return el ? el.value : '';
}

