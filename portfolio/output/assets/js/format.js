const DATA = __DATA_JSON__;

const fmt = (n) => n === null || n === undefined ? '—' :
  n.toLocaleString('es-AR', {minimumFractionDigits:2, maximumFractionDigits:2});
const fmtPct = (n) => n === null || n === undefined ? '—' : (n>=0?'+':'') + n.toFixed(2) + '%';
const plClass = (n) => n === null || n === undefined ? '' : (n >= 0 ? 'pos' : 'neg');
// "live" covers both PPI and the Yahoo Finance fallback (the second source
// for USD instruments PPI does not quote or has no data for right now).
const isLiveSource = (s) => s === 'PPI (en vivo)' || s === 'Yahoo Finance';

document.getElementById('generatedAt').textContent = 'Generado ' + DATA.generated_at;
document.getElementById('fxBar').textContent = DATA.fx_rate
  ? `Tipo de cambio usado: 1 USD = ${fmt(DATA.fx_rate)} ARS (${DATA.fx_source})`
  : `Tipo de cambio no disponible (${DATA.fx_source}) -- las columnas convertidas quedan vacías`;

