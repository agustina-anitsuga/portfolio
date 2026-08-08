const tableState = {};
const chartInstances = {};

function renderCharts(marketKey, filteredRows) {
  // General (a summary table of a few rows) and Transacciones have no charts.
  if (marketKey === 'general' || marketKey === 'tx') return;

  const currency = tableState[marketKey].currency;
  const cur = currency.toUpperCase();
  if (chartInstances[marketKey]) {
    chartInstances[marketKey].forEach(c => { if (c && typeof c.destroy === 'function') c.destroy(); });
  }

  // when no filtered subset was passed, use the whole portfolio (the init case,
  // before the user applies any filter).
  const rows = filteredRows || DATA.markets[marketKey].rows;
  const top = [...rows].sort((a,b) => (b[`value_${currency}`]||0)-(a[`value_${currency}`]||0)).slice(0, 10);
  const bar = new Chart(document.getElementById(`bar-${marketKey}`), {
    type: 'bar',
    data: { labels: top.map(r=>r.key), datasets: [
      {label:`Invertido (${cur})`, data: top.map(r=>r[`invested_${currency}`]), backgroundColor:'#6ea8fe'},
      {label:`Valor Actual (${cur})`, data: top.map(r=>r[`value_${currency}`]||0), backgroundColor:'#3ddc84'},
    ]},
    options: { plugins:{legend:{labels:{color:'#e7e9ee'}}}, scales:{
      x:{ticks:{color:'#9aa2b1'}}, y:{ticks:{color:'#9aa2b1'}}
    }}
  });
  const palette = ['#6ea8fe','#3ddc84','#ffb84d','#ff5c5c','#c792ea','#4dd0e1','#f78fb3','#a0c980','#ffd166','#8d99ae'];
  const pie = new Chart(document.getElementById(`pie-${marketKey}`), {
    type: 'doughnut',
    data: { labels: top.map(r=>r.key), datasets: [{ data: top.map(r=>r[`value_${currency}`]||0), backgroundColor: palette }] },
    options: { plugins:{legend:{position:'bottom', labels:{color:'#e7e9ee', boxWidth:10, font:{size:10}}}} }
  });
  chartInstances[marketKey] = [bar, pie];
}

