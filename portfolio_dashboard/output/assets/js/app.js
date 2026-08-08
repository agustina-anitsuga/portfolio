function initPage(marketKey) {
  const isGeneral = marketKey === 'general';
  const isTx = marketKey === 'tx';
  const cols = getCols(marketKey);
  tableState[marketKey] = {
    currency: DEFAULT_CURRENCY[marketKey] || 'ars',
    sort: {
      key: isGeneral ? 'pl_abs' : (isTx ? 'date' : 'value'),
      dir: -1,
      dual: !isGeneral && !isTx,
    },
  };

  renderHead(marketKey);
  applyFilters(marketKey, cols); // also triggers renderCharts and renderKpis with the filtered set
  wireHScroll(marketKey);

  if (isTx) {
    document.querySelector(`[data-role="search"][data-market="tx"]`)
      .addEventListener('input', () => applyFilters('tx', cols));
    document.querySelector(`[data-role="type"][data-market="tx"]`)
      .addEventListener('change', () => applyFilters('tx', cols));
  } else if (!isGeneral) {
    document.querySelector(`[data-role="search"][data-market="${marketKey}"]`)
      .addEventListener('input', () => applyFilters(marketKey, cols));
    document.querySelector(`[data-role="sector"][data-market="${marketKey}"]`)
      .addEventListener('change', () => applyFilters(marketKey, cols));
    document.querySelector(`[data-role="insttype"][data-market="${marketKey}"]`)
      .addEventListener('change', () => applyFilters(marketKey, cols));
  }

  // the year filter exists in all three kinds of tab (general, per instrument
  // type and transactions), so it is wired once here.
  const yearEl = document.querySelector(`[data-role="year"][data-market="${marketKey}"]`);
  if (yearEl) {
    yearEl.addEventListener('change', () => applyFilters(marketKey, cols));
  }

  const currencyEl = document.querySelector(`[data-role="currency"][data-market="${marketKey}"]`);
  if (currencyEl) {
    currencyEl.addEventListener('change', (e) => {
      tableState[marketKey].currency = e.target.value;
      renderHead(marketKey);
      applyFilters(marketKey, cols); // also triggers renderCharts and renderKpis with the filtered set
      if (hscrollSync[marketKey]) setTimeout(hscrollSync[marketKey], 0);
    });
  }
}

// Click any ticker (in the per-type tables or in general) -> jump to the
// Transacciones tab filtered by that ticker.
function goToTicker(ticker) {
  selectTab('tx');
  const searchEl = document.querySelector(`[data-role="search"][data-market="tx"]`);
  searchEl.value = ticker;
  applyFilters('tx', getCols('tx'));
}

pagesEl.addEventListener('click', (e) => {
  const t = e.target.closest('.ticker-link');
  if (t) { goToTicker(t.dataset.ticker); return; }

  // click on a row of the general tab (not the Total) -> go to its detail
  const row = e.target.closest('tr[data-market-link]');
  if (row) { selectTab(row.dataset.marketLink); }
});

const tabEls = {};

function selectTab(key) {
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  tabEls[key].classList.add('active');
  document.getElementById('page-'+key).classList.add('active');
  // the page was display:none until now, so its scrollWidth/clientWidth
  // were unreadable -- recompute the slider range now that it's visible.
  if (hscrollSync[key]) setTimeout(hscrollSync[key], 0);
}

MARKET_KEYS.forEach((key, i) => {
  const tab = document.createElement('div');
  tab.className = 'tab' + (i===0 ? ' active' : '');
  tab.textContent = TAB_LABELS[key];
  tab.addEventListener('click', () => selectTab(key));
  tabsEl.appendChild(tab);
  tabEls[key] = tab;

  const page = buildPage(key);
  if (i===0) page.classList.add('active');
  pagesEl.appendChild(page);
});

MARKET_KEYS.forEach(initPage);
