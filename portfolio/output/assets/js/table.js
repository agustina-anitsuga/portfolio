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

// Rows of the Anual tab. With "Excluir RSU" on, every year is rebuilt from its
// instruments (the same sums Python does) leaving the RSU ones out.
function annualRows() {
  const el = document.querySelector('[data-role="excludersu"][data-market="annual"]');
  if (!el || !el.checked) return DATA.annual;
  return DATA.annual.map(r => {
    const detail = r.detail.filter(d => d.market !== 'rsu');
    const row = { year: r.year, detail };
    for (const c of ['ars', 'usd']) {
      const sum = key => detail.reduce((s, d) => s + d[`${key}_${c}`], 0);
      const all = key => detail.every(d => d[`${key}_${c}`] !== null);
      const net = sum('invested_net');
      const close = all('close_value') ? sum('close_value') : null;
      const gain = all('gain') ? sum('gain') : null;
      row[`invested_gross_${c}`] = sum('invested_gross');
      row[`invested_net_${c}`] = net;
      row[`close_value_${c}`] = close;
      row[`year_pct_${c}`] = (close !== null && net) ? (close - net) / net * 100 : null;
      row[`gain_${c}`] = gain;
      row[`gain_pct_${c}`] = (gain !== null && net) ? gain / net * 100 : null;
    }
    return row;
  }).filter(r => r.detail.length);
}

// Years of the Anual tab that are open to show their instruments.
const annualExpanded = new Set();

function annualCellHtml(r, c, currency) {
  const v = cellValue(r, c, currency);
  if (c.key === 'year') {
    if (r.detail) return `<td><strong>${annualExpanded.has(r.year) ? '▾' : '▸'} ${v}</strong></td>`;
    return `<td class="detail-name"><strong class="ticker-link" data-ticker="${r.key}">${r.key}</strong> `
      + `<span class="tag">${TAB_LABELS[r.market] || r.market}</span> ${r.name || ''}</td>`;
  }
  if (v === null || v === undefined) return '<td>—</td>';
  if (c.pct) return `<td class="${plClass(v)}">${fmtPct(v)}</td>`;
  return `<td class="${c.pl ? plClass(v) : ''}">${fmt(v)}</td>`;
}

// One row per year; the open ones are followed by one row per instrument.
function renderAnnualRows(rows, cols, currency) {
  return rows.map(r => {
    const open = annualExpanded.has(r.year);
    const head = `<tr class="row-link" data-year="${r.year}">${cols.map(c => annualCellHtml(r, c, currency)).join('')}</tr>`;
    if (!open) return head;
    const detail = [...r.detail]
      .sort((a, b) => (b[`invested_net_${currency}`] || 0) - (a[`invested_net_${currency}`] || 0))
      .map(d => `<tr class="detail-row">${cols.map(c => annualCellHtml(d, c, currency)).join('')}</tr>`);
    return head + detail.join('');
  }).join('');
}

function renderRows(marketKey, rows, cols) {
  const currency = tableState[marketKey].currency;
  const tbody = document.querySelector(`#table-${marketKey} tbody`);
  if (marketKey === 'annual') {
    tbody.innerHTML = renderAnnualRows(rows, cols, currency);
    const countEl = document.querySelector(`[data-role="count"][data-market="annual"]`);
    if (countEl) countEl.textContent = `${rows.length} años`;
    return;
  }
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
    if (c.signal) return `<td class="signal-cell">${signalBadge(v)}</td>`;
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
    const total = marketKey === 'tx' ? DATA.transactions.length
                : marketKey === 'watch' ? DATA.watchlist.length
                : marketKey === 'annual' ? DATA.annual.length
                : DATA.markets[marketKey].rows.length;
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
  if (marketKey === 'annual') return annualRows();
  if (marketKey === 'watch') {
    const searchEl = document.querySelector(`[data-role="search"][data-market="watch"]`);
    const search = (searchEl.value || '').toLowerCase();
    return DATA.watchlist.filter(r => !search ||
      `${r.ticker} ${r.name || ''}`.toLowerCase().includes(search));
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
  if (marketKey !== 'tx' && marketKey !== 'watch' && marketKey !== 'annual') {
    renderCharts(marketKey, rows);
    renderKpis(marketKey, rows);
    renderUnpricedNote(marketKey, rows);
    renderScopeNote(marketKey, rows);
  }
}

