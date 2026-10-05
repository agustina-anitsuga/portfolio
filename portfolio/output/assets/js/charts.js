const tableState = {};
const chartInstances = {};

// One entry per bar/slice. The general tab's rows are already resolved in the
// chosen currency (one per portfolio); the other tabs carry both currencies
// with a suffix (one per position).
function chartSeries(marketKey, rows, currency) {
  if (marketKey === 'general') {
    return rows.map(r => ({ label: r.label, invested: r.invested, value: r.value }));
  }
  return rows.map(r => ({
    label: r.key, invested: r[`invested_${currency}`], value: r[`value_${currency}`],
  }));
}

// Current value per sector (summed across positions), regardless of what the
// bar/pie charts above are showing. The general tab has no sector of its own
// (its rows are one per portfolio), so there it aggregates the sector of
// every underlying position across all portfolios, honouring the general
// tab's own year filter.
function sectorSeries(marketKey, rows, currency) {
  const bySector = new Map();
  const add = (sector, value) => {
    if (value === null || value === undefined) return;
    bySector.set(sector, (bySector.get(sector) || 0) + value);
  };
  if (marketKey === 'general') {
    generalPortfolioKeys().forEach(m => {
      generalMarketRows(m).forEach(r => add(r.sector, r[`value_${currency}`]));
    });
  } else {
    rows.forEach(r => add(r.sector, r[`value_${currency}`]));
  }
  return [...bySector.entries()]
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value);
}

function renderCharts(marketKey, filteredRows) {
  // Transacciones lists individual trades and Watchlist holds no position, so
  // in both cases there is nothing to aggregate.
  if (marketKey === 'tx' || marketKey === 'watch' || marketKey === 'annual') return;

  const currency = tableState[marketKey].currency;
  const cur = currency.toUpperCase();
  if (chartInstances[marketKey]) {
    chartInstances[marketKey].forEach(c => { if (c && typeof c.destroy === 'function') c.destroy(); });
  }

  // when no filtered subset was passed, use the whole portfolio (the init case,
  // before the user applies any filter).
  const rows = filteredRows || (marketKey === 'general'
    ? buildGeneralRows(currency)
    : DATA.markets[marketKey].rows);
  const top = chartSeries(marketKey, rows, currency)
    .sort((a, b) => (b.value || 0) - (a.value || 0))
    .slice(0, 10);
  const palette = ['#6ea8fe','#3ddc84','#ffb84d','#ff5c5c','#c792ea','#4dd0e1','#f78fb3','#a0c980','#ffd166','#8d99ae'];
  const bar = new Chart(document.getElementById(`bar-${marketKey}`), {
    type: 'bar',
    data: { labels: top.map(r=>r.label), datasets: [
      {label:`Invertido (${cur})`, data: top.map(r=>r.invested), backgroundColor:'#6ea8fe'},
      {label:`Valor Actual (${cur})`, data: top.map(r=>r.value||0), backgroundColor:'#3ddc84'},
    ]},
    options: { plugins:{legend:{labels:{color:'#e7e9ee'}}}, scales:{
      x:{ticks:{color:'#9aa2b1'}}, y:{ticks:{color:'#9aa2b1'}}
    }}
  });
  const pie = new Chart(document.getElementById(`pie-${marketKey}`), {
    type: 'doughnut',
    data: { labels: top.map(r=>r.label), datasets: [{ data: top.map(r=>r.value||0), backgroundColor: palette }] },
    options: { plugins:{legend:{position:'bottom', labels:{color:'#e7e9ee', boxWidth:10, font:{size:10}}}} }
  });
  const sectors = sectorSeries(marketKey, rows, currency);
  const sector = new Chart(document.getElementById(`sector-${marketKey}`), {
    type: 'bar',
    data: { labels: sectors.map(s=>s.label), datasets: [
      { label:`Valor Actual (${cur})`, data: sectors.map(s=>s.value), backgroundColor: palette },
    ]},
    options: { plugins:{legend:{display:false}}, scales:{
      x:{ticks:{color:'#9aa2b1'}}, y:{ticks:{color:'#9aa2b1'}}
    }}
  });
  chartInstances[marketKey] = [bar, pie, sector];
}

