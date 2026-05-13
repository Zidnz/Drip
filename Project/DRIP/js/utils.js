/* ============================================
   DRIP — utils.js
   Utilidades generales
   ============================================ */

// ── Icon helper (Feather Icons) ───────────────────────────────────────────────
const ic = (name, size = 16, color = 'currentColor', sw = 2) =>
  (typeof feather !== 'undefined' && feather.icons[name])
    ? feather.icons[name].toSvg({ width: size, height: size, stroke: color, 'stroke-width': sw })
    : `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="${sw}"></svg>`;

// ── Estado badge ──────────────────────────────────────────────────────────────
function estadoBadge(estado) {
  const cfg = {
    optimo:         { cls: 'badge--success', label: 'Óptimo',         icon: 'check-circle',   c: '#5F7D2B' },
    atencion:       { cls: 'badge--warning', label: 'Atención',        icon: 'clock',          c: '#B07E1A' },
    estres_hidrico: { cls: 'badge--danger',  label: 'Estrés hídrico',  icon: 'alert-triangle', c: '#D45B3A' },
  };
  const e = cfg[estado] || cfg.optimo;
  return `<span class="badge ${e.cls}">${ic(e.icon, 11, e.c, 2.5)} ${e.label}</span>`;
}

// ── Format date ───────────────────────────────────────────────────────────────
function fmtDate(dateStr) {
  const [y, m, d] = dateStr.split('-');
  const months = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
  return `${d} ${months[parseInt(m) - 1]}`;
}

// ── Greeting by hour ──────────────────────────────────────────────────────────
function greeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Buenos días';
  if (h < 19) return 'Buenas tardes';
  return 'Buenas noches';
}

// ── Debounce ──────────────────────────────────────────────────────────────────
function debounce(fn, delay = 200) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}

// ── Clamp number ──────────────────────────────────────────────────────────────
const clamp = (val, min, max) => Math.min(max, Math.max(min, val));

// ── Feather replace safe ──────────────────────────────────────────────────────
function featherReplace() {
  if (typeof feather !== 'undefined') feather.replace();
}
