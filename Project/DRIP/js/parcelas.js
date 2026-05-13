/* ============================================
   DRIP — parcelas.js
   Render: grid de parcelas, detalle, sensores
   ============================================ */

let detChart = null;

function renderParcelas() {
  const grid = document.getElementById('grid-parc');
  if (!grid || grid.children.length) return;

  PARCELAS.forEach(p => {
    const hc  = humColorHex(p.humedad);
    const div = document.createElement('article');
    div.className = 'parc-card anim-fade';
    div.setAttribute('role', 'button');
    div.setAttribute('tabindex', '0');
    div.onclick = () => showParcelaDetalle(p);
    div.innerHTML = `
      <div class="parc-card__header">
        <div>
          <div class="parc-card__icon" style="background:${p.color}18;">
            ${ic('leaf', 22, p.color, 2)}
          </div>
          <div class="parc-card__name">${p.nombre}</div>
          <div class="parc-card__meta">${p.area} ha · ${p.sistema}</div>
        </div>
        ${estadoBadge(p.estado)}
      </div>

      <div class="hum-label-row">
        <span class="hum-label-text">Humedad suelo</span>
        <span class="hum-label-value" style="color:${hc};">${p.humedad}%</span>
      </div>
      <div class="hum-track">
        <div class="hum-marker" style="left:${p.objetivo}%;"></div>
        <div class="hum-fill" style="width:${Math.min(100, p.humedad)}%;background:${hc};"></div>
      </div>
      <div class="hum-range">
        <span>0%</span><span>Obj: ${p.objetivo}%</span><span>100%</span>
      </div>

      <div class="parc-metrics">
        <div class="pm-cell">
          <div style="display:flex;justify-content:center;margin-bottom:3px;">${ic('droplet',12,'#7C9CA8')}</div>
          <div class="pm-cell__value">${p.etc}</div>
          <div class="pm-cell__label">mm/día</div>
        </div>
        <div class="pm-cell">
          <div style="display:flex;justify-content:center;margin-bottom:3px;">${ic('zap',12,'#E8A838')}</div>
          <div class="pm-cell__value">${p.wue}</div>
          <div class="pm-cell__label">kg/m³</div>
        </div>
        <div class="pm-cell">
          <div style="display:flex;justify-content:center;margin-bottom:3px;">${ic('calendar',12,p.color)}</div>
          <div class="pm-cell__value" style="color:${p.color};">Día ${p.dia}</div>
          <div class="pm-cell__label">${p.etapa}</div>
        </div>
      </div>

      <div class="parc-card__timestamp">
        ${ic('clock', 11, 'var(--gray-soft)')} Última lectura: hace 5 min
      </div>`;

    grid.appendChild(div);
  });

  featherReplace();
  initFadeAnimations();
}

function showParcelaDetalle(p) {
  const det = document.getElementById('parc-detalle');
  if (!det) return;

  det.style.display = 'block';
  document.getElementById('det-titulo').innerHTML =
    `${ic('map-pin', 16, 'var(--green-primary)')} ${p.nombre} · Indicadores`;

  // Estadísticas clave
  const statsEl = document.getElementById('det-stats');
  if (statsEl) {
    statsEl.innerHTML = [
      ['Cultivo',           p.cultivo],
      ['Área',              p.area + ' ha'],
      ['Tipo de suelo',     p.suelo],
      ['Sistema de riego',  p.sistema],
      ['Estado',            estadoBadge(p.estado)],
      ['Etapa fenológica',  `${p.etapa} · Día ${p.dia}`],
      ['Humedad actual',    `<span style="font-weight:800;color:${humColorHex(p.humedad)};">${p.humedad}%</span>`],
      ['Humedad objetivo',  p.objetivo + '%'],
      ['ETc prom. 30d',     p.etc + ' mm/día'],
      ['WUE',               p.wue + ' kg/m³'],
      ['CWSI',              p.cwsi],
      ['Agua total',        (p.agua_m3 / 1000).toFixed(0) + ' m³'],
      ['Rendimiento est.',  p.rend + ' ton'],
      ['Ingreso estimado',  fmtMXN(p.ingreso) + ' MXN'],
    ].map(([l, v]) =>
      `<div class="stat-row"><span class="stat-lbl">${l}</span><span class="stat-val">${v}</span></div>`
    ).join('');
  }

  // Gráfica detalle
  if (detChart) detChart.destroy();
  const ctx = document.getElementById('ch-det');
  if (ctx) {
    detChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: LABELS_30,
        datasets: [
          { label: 'Humedad %', data: genHum(p.humedad, p.objetivo), borderColor: p.color, backgroundColor: p.color + '18', fill: true, tension: 0.4, pointRadius: 0, borderWidth: 2 },
          { label: 'Objetivo',  data: Array(30).fill(p.objetivo), borderColor: '#7C9CA8', borderDash: [5, 5], borderWidth: 1.5, pointRadius: 0, fill: false },
          { label: 'Estrés',    data: Array(30).fill(p.estres),   borderColor: '#D45B3A', borderDash: [5, 5], borderWidth: 1.5, pointRadius: 0, fill: false },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { min: 0, max: 100, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { callback: v => v + '%', font: { size: 10 } } },
          x: { grid: { display: false }, ticks: { font: { size: 10 }, maxTicksLimit: 8 } },
        },
      },
    });
  }

  det.scrollIntoView({ behavior: 'smooth', block: 'start' });
  featherReplace();
}

// ── Riego view ────────────────────────────────────────────────────────────────
function renderRiego() {
  const tb = document.getElementById('t-riegos');
  if (!tb || tb.children.length) return;

  RIEGOS.forEach(r => {
    const p = PARCELAS.find(x => x.id === r.pid);
    tb.innerHTML += `
      <tr>
        <td style="font-size:12px;">${fmtDate(r.fecha)}</td>
        <td>
          <div style="display:flex;align-items:center;gap:6px;">
            <span style="width:22px;height:22px;border-radius:6px;background:${p.color}20;
              display:flex;align-items:center;justify-content:center;flex-shrink:0;">
              ${ic('leaf', 12, p.color)}
            </span>
            <span style="font-size:12px;">${p.nombre}</span>
          </div>
        </td>
        <td><span class="badge badge--info">${r.metodo}</span></td>
        <td style="font-weight:700;font-size:12px;">${fmtL(r.litros)}</td>
        <td style="font-size:12px;">${r.dur} min</td>
        <td style="font-size:12px;">${fmtMXN(r.ca)}</td>
        <td style="font-size:12px;">${fmtMXN(r.ce)}</td>
        <td style="font-size:12px;color:var(--gray-soft);">${r.motivo}</td>
      </tr>`;
  });

  renderChartConsumo('ch-consumo');

  const ef = document.getElementById('ef-list');
  if (ef) {
    PARCELAS.forEach(p => {
      const pct = Math.min(98, 55 + Math.round(p.wue * 3 + 5));
      ef.innerHTML += `
        <div class="prog-row" style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
          <span style="width:100px;font-size:12px;color:var(--gray-soft);display:flex;align-items:center;gap:4px;">
            ${ic('leaf', 12, p.color)} ${p.cultivo}
          </span>
          <div style="flex:1;height:7px;border-radius:4px;background:var(--beige-light);overflow:hidden;">
            <div style="height:100%;border-radius:4px;background:${p.color};width:${pct}%;"></div>
          </div>
          <span style="width:38px;text-align:right;font-size:12px;font-weight:700;">${pct}%</span>
        </div>`;
    });
  }

  featherReplace();
}
