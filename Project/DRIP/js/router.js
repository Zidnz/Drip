/* ============================================
   DRIP — router.js
   SPA navigation: show/hide screens
   ============================================ */

const PAGE_META = {
  dashboard: { title: 'Dashboard',           sub: 'Ciclo PV-2025 · DR-075',          nav: 'dashboard' },
  parcelas:  { title: 'Mis Cultivos',         sub: 'DR-075 Sinaloa · 5 parcelas',      nav: 'parcelas'  },
  riego:     { title: 'Gestión de Riego',     sub: 'Historial y recomendaciones',       nav: 'parcelas'  },
  sensores:  { title: 'Sensores IoT',         sub: '15 dispositivos · DR-075',          nav: 'sensores'  },
  alertas:   { title: 'Alertas',              sub: '3 alertas activas',                 nav: 'alertas'   },
  reportes:  { title: 'Reportes',             sub: 'Análisis Ciclo PV-2025',            nav: 'reportes'  },
  perfil:    { title: 'Mi Perfil',            sub: 'Danae · Admin DR-075',              nav: 'perfil'    },
};

let currentView = null;

function navigateTo(viewId) {
  if (currentView === viewId) return;

  // Ocultar todas las screens
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));

  // Mostrar la screen destino
  const target = document.getElementById('screen-' + viewId);
  if (!target) return;
  target.classList.add('active');

  // Actualizar nav inferior
  document.querySelectorAll('.nav-bottom__item').forEach(item => {
    item.classList.toggle('active', item.dataset.view === (PAGE_META[viewId]?.nav || viewId));
  });

  // Actualizar topbar (si existe y si es vista con navbar)
  const meta = PAGE_META[viewId];
  const topbarTitle = document.getElementById('topbar-title');
  const topbarSub   = document.getElementById('topbar-sub');
  if (meta && topbarTitle) topbarTitle.textContent = meta.title;
  if (meta && topbarSub)   topbarSub.textContent   = meta.sub;

  currentView = viewId;

  // Lazy-render de la vista
  renderView(viewId);

  // Scroll al top
  target.scrollTo({ top: 0, behavior: 'smooth' });
  window.scrollTo(0, 0);

  featherReplace();
}

// ── Lazy render control ───────────────────────────────────────────────────────
const RENDERED = {};

function renderView(viewId) {
  if (RENDERED[viewId]) return;
  RENDERED[viewId] = true;

  switch (viewId) {
    case 'dashboard': renderDashboard(); break;
    case 'parcelas':  renderParcelas();  break;
    case 'riego':     renderRiego();     break;
    case 'sensores':  renderSensores();  break;
    case 'alertas':   renderAlertas();   break;
    case 'reportes':  renderReportes();  break;
    case 'perfil':    renderPerfil();    break;
  }
}

// ── Go back helper ────────────────────────────────────────────────────────────
function goBack() {
  const fallback = 'dashboard';
  navigateTo(fallback);
}
