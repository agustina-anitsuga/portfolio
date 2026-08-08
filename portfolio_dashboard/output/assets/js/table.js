// 30-day trend line as inline SVG. The scale is relative to EACH instrument
// (its own minimum and maximum), so the shape reads well even when one paper
// trades at 5 and another at 70000; what you canNOT do is compare heights
// across rows. The final dot marks where the series ends.
function sparkline(series, pct) {
  if (!series || series.length < 2) return '—';
  const w = 72, h = 22, pad = 3;
  const min = Math.min(...series), max = Math.max(...series);
  const span = (max - min) || 1;          // flat series: the line sits in the middle
  const dx = (w - pad * 2) / (series.length - 1);
  const y = p => (max === min ? h / 2 : h - pad - ((p - min) / span) * (h - pad * 2));
  const pts = series.map((p, i) => `${(pad + i * dx).toFixed(1)},${y(p).toFixed(1)}`);
  const cls = pct > 0 ? 'pos' : (pct < 0 ? 'neg' : 'spark-flat');
  const last = pts[pts.length - 1].split(',');
  return `<svg class="spark ${cls}" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">`
    + `<polyline points="${pts.join(' ')}"/>`
    + `<circle cx="${last[0]}" cy="${last[1]}" r="1.8"/>`
    + `</svg>`;
}

function renderRows(marketKey, rows, cols) {
  const currency = tableState[marketKey].currency;
  const tbody = document.querySelector(`#table-${marketKey} tbody`);
  tbody.innerHTML = rows.map(r => {
    const rowClass = r.market ? 'row-link' : '';
    const rowAttr = r.market ? ` data-market-link="${r.market}"` : '';
    return `<tr class="${rowClass}"${rowAttr}>${cols.map(c => {
    let v = cellValue(r, c, currency);
    if (c.key === 'key') {
      return `<td><strong class="ticker-link" data-ticker="${r.key}">${r.key}</strong> <span class="tag ${isLiveSource(r.price_source)?'live':''}">${r.price_source||''}</span></td>`;
    }
    if (c.key === 'ticker') {
      const src = r.current_price_source;
      const tag = src ? `<span class="tag ${isLiveSource(src)?'live':''}">${src}</span>` : '';
      return `<td><strong class="ticker-link" data-ticker="${v}">${v}</strong> ${tag}</td>`;
    }
    if (c.key === 'label') return `<td><strong>${v}</strong></td>`;
    if (c.key === 'market') return `<td>${TAB_LABELS[v] || v}</td>`;
    if (c.key === 'op') return `<td class="${v==='BUY'?'pos':(v==='SELL'?'neg':'')}">${v}</td>`;
    if (c.spark) return `<td class="${plClass(v)}" title="${v===null||v===undefined?'sin datos':fmtPct(v)+' en 30 dias'}">${sparkline(r.trend_series, v)}</td>`;
    if (v === null || v === undefined) return `<td>—</td>`;
    if (c.pct) return `<td class="${c.pl?plClass(v):''}">${fmtPct(v)}</td>`;
    if (c.pl) return `<td class="${plClass(v)}">${fmt(v)}</td>`;
    if (c.num) return `<td>${fmt(v)}</td>`;
    return `<td>${v}</td>`;
    }).join('')}</tr>`;
  }).join('');
  const countEl = document.querySelector(`[data-role="count"][data-market="${marketKey}"]`);
  if (countEl) {
    const total = marketKey === 'tx' ? DATA.transactions.length : DATA.markets[marketKey].rows.length;
    countEl.textContent = `${rows.length} de ${total}`;
  }
}

// Rows that pass the active filters (search/sector/type) of that tab, not
// sorted yet -- used by both the table and the charts, so the two always stay
// in sync with whatever the user is filtering by.
function filterRows(marketKey) {
  const currency = tableState[marketKey].currency;

  if (marketKey === 'general') {
    return buildGeneralRows(currency);
  }
  if (marketKey === 'tx') {
    const searchEl = document.querySelector(`[data-role="search"][data-market="tx"]`);
    const typeEl = document.querySelector(`[data-role="type"][data-market="tx"]`);
    const search = (searchEl.value || '').toLowerCase();
    const type = typeEl.value;
    // here each row IS a trade, so the year filter applies to the date of the
    // trade itself.
    const year = currentYear('tx');
    return DATA.transactions.filter(r => {
      if (search && !r.ticker.toLowerCase().includes(search)) return false;
      if (type && r.market !== type) return false;
      if (year && r.year !== year) return false;
      return true;
    });
  }
  // the year filter does not drop rows: it swaps the whole set for the one
  // recomputed with only that year's trades.
  const allRows = marketRows(marketKey, currentYear(marketKey));
  const searchEl = document.querySelector(`[data-role="search"][data-market="${marketKey}"]`);
  const sectorEl = document.querySelector(`[data-role="sector"][data-market="${marketKey}"]`);
  const instTypeEl = document.querySelector(`[data-role="insttype"][data-market="${marketKey}"]`);
  const search = (searchEl.value || '').toLowerCase();
  const sector = sectorEl.value;
  const instType = instTypeEl ? instTypeEl.value : '';
  return allRows.filter(r => {
    if (search && !(`${r.key} ${r.name}`.toLowerCase().includes(search))) return false;
    if (sector && r.sector !== sector) return false;
    if (instType && r.instrument_type !== instType) return false;
    return true;
  });
}

function applyFilters(marketKey, cols) {
  const currency = tableState[marketKey].currency;
  let rows = filterRows(marketKey);

  const sortState = tableState[marketKey].sort;
  if (sortState) {
    const { key, dir, dual } = sortState;
    const resolveKey = r => dual ? r[`${key}_${currency}`] : r[key];
    rows = [...rows].sort((a, b) => {
      let av = resolveKey(a), bv = resolveKey(b);
      const aNull = av === null || av === undefined || av === '';
      const bNull = bv === null || bv === undefined || bv === '';
      if (aNull && bNull) return 0;
      if (aNull) return 1;
      if (bNull) return -1;
      if (typeof av === 'string') return dir * av.localeCompare(bv);
      return dir * (av - bv);
    });
  }

  renderRows(marketKey, rows, cols);
  // the charts and the KPI pills (absent in Transacciones) are recomputed with
  // the same filtered subset shown in the table.
  if (marketKey !== 'general' && marketKey !== 'tx') renderCharts(marketKey, rows);
  if (marketKey !== 'tx') {
    renderKpis(marketKey, rows);
    renderUnpricedNote(marketKey, rows);
    renderScopeNote(marketKey, rows);
  }
}

