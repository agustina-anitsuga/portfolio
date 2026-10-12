// Solapa "Aporte mensual": cuanto comprar este mes de cada instrumento, en
// pesos y en dolar CCL. Es un panel fijo, sin tabla ni filtros.

function contributionHtml() {
  const c = DATA.contribution;
  if (!c) {
    return `<div class="approx-note">Falta la hoja "aporte" en la planilla (monto mensual en ARS y, debajo, ticker / % / moneda ARS o CCL).</div>`;
  }
  const usd = (n) => n === null || n === undefined ? '—' : 'US$ ' + fmt(n);
  const ars = (n) => '$ ' + fmt(n);
  const hasCcl = !!c.ccl_rate;

  const warnings = [];
  if (Math.abs(c.pct_total - 100) > 0.01) {
    warnings.push(`Los porcentajes suman ${c.pct_total.toFixed(2)}% y no 100%: revisá la hoja "aporte".`);
  }
  if (!hasCcl) {
    warnings.push(`Dólar CCL no disponible (${c.ccl_source}): los montos en dólares quedan vacíos. Podés cargar una fila "USD/CCL" en la hoja config como respaldo.`);
  }

  const rows = c.rows.map(r => `<tr>
    <td><strong>${r.ticker}</strong></td>
    <td>${r.pct.toFixed(2)}%</td>
    <td>${r.currency === 'CCL' ? 'Dólar CCL' : 'Pesos'}</td>
    <td>${ars(r.ars)}</td>
    <td>${usd(r.usd)}</td>
  </tr>`).join('');

  return `
    <div class="fxbar">Dólar CCL: ${hasCcl ? `1 USD = ${fmt(c.ccl_rate)} ARS (${c.ccl_source})` : 'no disponible'}</div>
    ${warnings.map(w => `<div class="unpriced-note">${w}</div>`).join('')}
    <div class="kpis">
      <div class="kpi"><div class="label">Aporte del mes</div><div class="val">${ars(c.monthly_ars)}</div><div class="label">${usd(c.monthly_usd)}</div></div>
      <div class="kpi"><div class="label">1. Cambiar a CCL</div><div class="val">${ars(c.ars_to_ccl)}</div><div class="label">te dan ${usd(c.usd_from_ccl)}</div></div>
      <div class="kpi"><div class="label">2. Comprar en pesos</div><div class="val">${ars(c.ars_direct)}</div><div class="label">directo en ARS</div></div>
    </div>
    <div class="table-wrap"><table>
      <thead><tr><th>Ticker</th><th>%</th><th>Se compra en</th><th>Monto (ARS)</th><th>Monto (USD CCL)</th></tr></thead>
      <tbody>${rows}</tbody>
    </table></div>
    <div class="approx-note">Los montos en dólares usan el CCL cotizado al generar el dashboard; no incluyen spread ni comisiones de la compra de CCL.</div>`;
}
