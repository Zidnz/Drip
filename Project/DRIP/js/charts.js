/* ============================================
   DRIP — charts.js
   Gráficas con Chart.js
   ============================================ */

const CH = {}; // store de instancias

const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    y: { grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { font: { size: 10, family: 'Inter' } } },
    x: { grid: { display: false }, ticks: { font: { size: 10, family: 'Inter' }, maxTicksLimit: 8 } },
  },
};

// ── Gráfica humedad del suelo (30 días) ───────────────────────────────────────
function renderChartHumedad(canvasId, parcela) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  if (CH[canvasId]) { CH[canvasId].destroy(); }

  CH[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: LABELS_30,
      datasets: [
        {
          label: 'Humedad %',
          data: genHum(parcela.humedad, parcela.objetivo),
          borderColor: parcela.color,
          backgroundColor: parcela.color + '18',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          borderWidth: 2,
        },
        {
          label: 'Objetivo',
          data: Array(30).fill(parcela.objetivo),
          borderColor: '#7C9CA8',
          borderDash: [5, 5],
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
        },
        {
          label: 'Estrés',
          data: Array(30).fill(parcela.estres),
          borderColor: '#D45B3A',
          borderDash: [5, 5],
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
        },
      ],
    },
    options: {
      ...CHART_DEFAULTS,
      scales: {
        y: { min: 0, max: 100, ...CHART_DEFAULTS.scales.y, ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => v + '%' } },
        x: CHART_DEFAULTS.scales.x,
      },
    },
  });
}

// ── Gráfica consumo mensual (m³) ──────────────────────────────────────────────
function renderChartConsumo(canvasId) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  if (CH[canvasId]) { CH[canvasId].destroy(); }

  CH[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
      datasets: [{
        data: [4200, 3800, 5100, 6800, 7200, 6400],
        backgroundColor: 'rgba(123,155,53,0.7)',
        borderColor: '#7B9B35',
        borderWidth: 2,
        borderRadius: 6,
      }],
    },
    options: CHART_DEFAULTS,
  });
}

// ── Gráfica ahorro semanal ────────────────────────────────────────────────────
function renderChartAhorro(canvasId) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  if (CH[canvasId]) { CH[canvasId].destroy(); }

  CH[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
      datasets: [{
        data: [142, 128, 165, 88, 203, 145, 118],
        backgroundColor: 'rgba(123,155,53,0.7)',
        borderColor: '#7B9B35',
        borderWidth: 2,
        borderRadius: 6,
      }],
    },
    options: CHART_DEFAULTS,
  });
}

// ── Gráfica rendimiento por cultivo (donut) ───────────────────────────────────
function renderChartRendimiento(canvasId) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  if (CH[canvasId]) { CH[canvasId].destroy(); }

  CH[canvasId] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: PARCELAS.map(p => p.cultivo),
      datasets: [{
        data: PARCELAS.map(p => p.rend),
        backgroundColor: PARCELAS.map(p => p.color),
        borderWidth: 0,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: { font: { size: 11, family: 'Inter' }, padding: 10, boxWidth: 12 },
        },
      },
    },
  });
}

// ── Gráfica ET₀ diaria ────────────────────────────────────────────────────────
function renderChartET0(canvasId) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  if (CH[canvasId]) { CH[canvasId].destroy(); }

  CH[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: LABELS_30,
      datasets: [{
        label: 'ET₀ mm/día',
        data: Array.from({ length: 30 }, () => +(3.5 + Math.random() * 4).toFixed(2)),
        borderColor: '#E8A838',
        backgroundColor: 'rgba(232,168,56,0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        borderWidth: 2,
      }],
    },
    options: {
      ...CHART_DEFAULTS,
      scales: {
        y: { ...CHART_DEFAULTS.scales.y },
        x: { ...CHART_DEFAULTS.scales.x, ticks: { ...CHART_DEFAULTS.scales.x.ticks, maxTicksLimit: 10 } },
      },
    },
  });
}
