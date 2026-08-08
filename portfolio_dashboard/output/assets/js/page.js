function buildPage(marketKey) {
  const isGeneral = marketKey === 'general';
  const isTx = marketKey === 'tx';
  const defaultCurrency = DEFAULT_CURRENCY[marketKey];

  const page = document.createElement('div');
  page.className = 'page';
  page.id = 'page-' + marketKey;

  let html = '';

  if (isTx) {
    const typeOptions = PORTFOLIO_KEYS;
    html += `<div class="toolbar">
      <input type="text" placeholder="Buscar ticker..." data-role="search" data-market="${marketKey}">
      <select data-role="type" data-market="${marketKey}">
        <option value="">Todos los portfolios</option>
        ${typeOptions.map(t => `<option value="${t}">${TAB_LABELS[t]}</option>`).join('')}
      </select>
      ${yearSelectHtml(marketKey, allBuyYears())}
      <span class="count" data-role="count" data-market="${marketKey}"></span>
    </div>`;
  } else if (isGeneral) {
    const anyApprox = PORTFOLIO_KEYS.some(m => DATA.markets[m].rows.some(r => r.fx_approx));
    html += `<div id="kpis-${marketKey}"></div>`;
    html += `<div class="unpriced-note" id="unpricednote-${marketKey}"></div>`;
    html += `<div class="approx-note" id="scopenote-${marketKey}" style="display:none"></div>`;
    if (anyApprox) {
      html += `<div class="approx-note">Uno o mas portfolios tienen posiciones con montos aproximados en la moneda no nativa (se convirtieron al tipo de cambio de HOY para esa operacion puntual, no historico). Mira el detalle en la pestana de cada tipo de instrumento.</div>`;
    }
    html += `<div class="toolbar">
      ${yearSelectHtml(marketKey, allBuyYears())}
      <select data-role="currency" data-market="${marketKey}">
        <option value="ars" ${defaultCurrency==='ars'?'selected':''}>Moneda: ARS</option>
        <option value="usd" ${defaultCurrency==='usd'?'selected':''}>Moneda: USD</option>
      </select>
    </div>`;
  } else {
    const rows = DATA.markets[marketKey].rows;
    const hasApprox = rows.some(r => r.fx_approx);
    html += `<div id="kpis-${marketKey}"></div>`;
    html += `<div class="unpriced-note" id="unpricednote-${marketKey}"></div>`;
    html += `<div class="approx-note" id="scopenote-${marketKey}" style="display:none"></div>`;
    if (hasApprox) {
      html += `<div class="approx-note">Algunas operaciones de esta posicion no tienen cargado el monto en la otra moneda (columna opcional en la hoja de transacciones), asi que para esas puntualmente se aproximo al tipo de cambio de HOY en vez del historico de esa operacion. El resto usa el monto real que cargaste.</div>`;
    }
    html += `<div class="charts">
      <div class="chart-card"><canvas id="bar-${marketKey}"></canvas></div>
      <div class="chart-card"><canvas id="pie-${marketKey}"></canvas></div>
    </div>`;

    const sectorOptions = uniqueSorted(rows, 'sector');
    const instTypeOptions = uniqueSorted(rows, 'instrument_type');
    html += `<div class="toolbar">
      <input type="text" placeholder="Buscar ticker o nombre..." data-role="search" data-market="${marketKey}">
      <select data-role="sector" data-market="${marketKey}">
        <option value="">Todos los sectores</option>
        ${sectorOptions.map(s => `<option value="${s}">${s}</option>`).join('')}
      </select>
      <select data-role="insttype" data-market="${marketKey}">
        <option value="">Todos los tipos</option>
        ${instTypeOptions.map(t => `<option value="${t}">${t}</option>`).join('')}
      </select>
      ${yearSelectHtml(marketKey, marketYears(marketKey))}
      <select data-role="currency" data-market="${marketKey}">
        <option value="ars" ${defaultCurrency==='ars'?'selected':''}>Moneda: ARS</option>
        <option value="usd" ${defaultCurrency==='usd'?'selected':''}>Moneda: USD</option>
      </select>
      <span class="count" data-role="count" data-market="${marketKey}"></span>
    </div>`;
  }

  html += `<div class="table-wrap" id="wrap-${marketKey}"><table id="table-${marketKey}">
    <thead><tr data-role="thead" data-market="${marketKey}"></tr></thead>
    <tbody></tbody>
  </table></div>
  <input type="range" class="hscroll" id="hscroll-${marketKey}" min="0" max="0" value="0" step="1">`;

  page.innerHTML = html;
  return page;
}

function renderHead(marketKey) {
  const currency = tableState[marketKey].currency;
  const cols = getCols(marketKey);
  const theadRow = document.querySelector(`thead tr[data-role="thead"][data-market="${marketKey}"]`);
  theadRow.innerHTML = cols.map(c => {
    const label = (c.dual || c.showCurrency) ? `${c.label} (${currency.toUpperCase()})` : c.label;
    return `<th data-key="${c.key}" data-market="${marketKey}">${label}</th>`;
  }).join('');
  wireSortHeaders(marketKey);
  const sort = tableState[marketKey].sort;
  const activeTh = theadRow.querySelector(`th[data-key="${sort.key}"]`);
  if (activeTh) activeTh.classList.add(sort.dir === 1 ? 'sorted-asc' : 'sorted-desc');
}

function wireSortHeaders(marketKey) {
  const cols = getCols(marketKey);
  document.querySelectorAll(`#table-${marketKey} th`).forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.key;
      const col = cols.find(c => c.key === key);
      const cur = tableState[marketKey].sort;
      const dir = (cur && cur.key === key) ? -cur.dir : -1;
      tableState[marketKey].sort = { key, dir, dual: !!(col && col.dual) };
      document.querySelectorAll(`#table-${marketKey} th`).forEach(h => h.classList.remove('sorted-asc','sorted-desc'));
      th.classList.add(dir === 1 ? 'sorted-asc' : 'sorted-desc');
      applyFilters(marketKey, cols);
    });
  });
}

const hscrollSync = {};

function wireHScroll(marketKey) {
  const wrap = document.getElementById(`wrap-${marketKey}`);
  const slider = document.getElementById(`hscroll-${marketKey}`);

  const syncMax = () => {
    // page might be display:none (inactive tab) -> scrollWidth/clientWidth
    // both read 0 then; harmless, we resync when the tab becomes active.
    const max = Math.max(0, wrap.scrollWidth - wrap.clientWidth);
    slider.max = max;
    slider.disabled = max <= 0;
    if (Number(slider.value) > max) slider.value = max;
  };

  hscrollSync[marketKey] = syncMax;
  syncMax();
  window.addEventListener('resize', syncMax);
  setTimeout(syncMax, 50);

  slider.addEventListener('input', () => { wrap.scrollLeft = Number(slider.value); });
  wrap.addEventListener('scroll', () => { slider.value = wrap.scrollLeft; }, { passive: true });
}

