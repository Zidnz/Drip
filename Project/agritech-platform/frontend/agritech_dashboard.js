// ── ICON HELPER ───────────────────────────────────────────────────────────────
const ic = (name, size = 14, color = 'currentColor', sw = 2) =>
  feather.icons[name]?.toSvg({ width: size, height: size, stroke: color, 'stroke-width': sw }) ?? '';

// ── DATA ──────────────────────────────────────────────────────────────────────
const PARCELAS = [
  {
    id: 'P001', nombre: 'Maíz – Lote 1',     cultivo: 'Maíz',     area: 8.5, sistema: 'Goteo',
    humedad: 72, objetivo: 65, estres: 30, estado: 'optimo',          etapa: 'Desarrollo', dia: 42,
    etc: 5.8,  wue: 1.5,  cwsi: .08, rend: 52.3, agua_m3: 18420, costo: 12800, ingreso: 287650,
    suelo: 'Franco-arcilloso', color: '#52b788', ic_color: '#15803d',
  },
  {
    id: 'P002', nombre: 'Chile – Lote 2',    cultivo: 'Chile',    area: 3.2, sistema: 'Microaspersión',
    humedad: 58, objetivo: 70, estres: 35, estado: 'atencion',         etapa: 'Media',      dia: 68,
    etc: 6.1,  wue: 4.7,  cwsi: .28, rend: 18.9, agua_m3: 9840,  costo: 7620,  ingreso: 378000,
    suelo: 'Franco-arenoso',  color: '#f59e0b', ic_color: '#b45309',
  },
  {
    id: 'P003', nombre: 'Papa – Lote 3',     cultivo: 'Papa',     area: 5.0, sistema: 'Goteo',
    humedad: 68, objetivo: 65, estres: 30, estado: 'optimo',          etapa: 'Media',      dia: 55,
    etc: 4.2,  wue: 4.6,  cwsi: .05, rend: 31.5, agua_m3: 14200, costo: 9850,  ingreso: 315000,
    suelo: 'Franco',          color: '#3b82f6', ic_color: '#1d4ed8',
  },
  {
    id: 'P004', nombre: 'Jitomate – Inv. 1', cultivo: 'Jitomate', area: 2.1, sistema: 'Goteo',
    humedad: 75, objetivo: 70, estres: 35, estado: 'optimo',          etapa: 'Desarrollo', dia: 38,
    etc: 5.5,  wue: 20.4, cwsi: .03, rend: 29.4, agua_m3: 5620,  costo: 4120,  ingreso: 441000,
    suelo: 'Limoso',          color: '#a855f7', ic_color: '#7e22ce',
  },
  {
    id: 'P005', nombre: 'Frijol – Lote 5',   cultivo: 'Frijol',   area: 6.8, sistema: 'Aspersión',
    humedad: 22, objetivo: 55, estres: 25, estado: 'estres_hidrico',  etapa: 'Inicial',    dia: 18,
    etc: 2.8,  wue: 0.3,  cwsi: .61, rend: 9.9,  agua_m3: 4180,  costo: 3240,  ingreso: 118800,
    suelo: 'Franco-arcilloso', color: '#ef4444', ic_color: '#b91c1c',
  },
];

const SENSORES = [
  { id: 'S001', parc: 'P001', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',          estado: 'activo',      bat: 87, prof: 60, zona: 'Zona A',   hum: 72, temp: 24, ce: 1.4 },
  { id: 'S002', parc: 'P001', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',          estado: 'activo',      bat: 81, prof: 30, zona: 'Zona B',   hum: 74, temp: 25, ce: 1.3 },
  { id: 'S003', parc: 'P001', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',          estado: 'activo',      bat: 79, prof: 90, zona: 'Zona C',   hum: 69, temp: 23, ce: 1.5 },
  { id: 'S004', parc: 'P002', tipo: 'Humedad / Temp / CE', modelo: 'Sentek EnviroSCAN',    estado: 'activo',      bat: 92, prof: 45, zona: 'Zona A',   hum: 58, temp: 26, ce: 2.1 },
  { id: 'S005', parc: 'P002', tipo: 'Humedad / Temp / CE', modelo: 'Sentek EnviroSCAN',    estado: 'bateria_baja',bat: 18, prof: 30, zona: 'Zona B',   hum: 55, temp: 27, ce: 1.9 },
  { id: 'S006', parc: 'P003', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',          estado: 'activo',      bat: 95, prof: 60, zona: 'Zona A',   hum: 68, temp: 23, ce: 1.2 },
  { id: 'S007', parc: 'P003', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',          estado: 'activo',      bat: 88, prof: 30, zona: 'Zona B',   hum: 71, temp: 24, ce: 1.1 },
  { id: 'S008', parc: 'P004', tipo: 'Humedad / Temp / CE', modelo: 'Sentek EnviroSCAN',    estado: 'activo',      bat: 76, prof: 45, zona: 'Zona A',   hum: 75, temp: 25, ce: 1.8 },
  { id: 'S009', parc: 'P004', tipo: 'Humedad / Temp / CE', modelo: 'Sentek EnviroSCAN',    estado: 'activo',      bat: 83, prof: 30, zona: 'Zona B',   hum: 74, temp: 26, ce: 1.7 },
  { id: 'S010', parc: 'P005', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',          estado: 'offline',     bat: 5,  prof: 60, zona: 'Zona A',   hum: 22, temp: 28, ce: 0.8 },
  { id: 'S011', parc: 'P005', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',          estado: 'bateria_baja',bat: 22, prof: 30, zona: 'Zona B',   hum: 24, temp: 29, ce: 0.7 },
  { id: 'S012', parc: 'P005', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',          estado: 'activo',      bat: 71, prof: 90, zona: 'Zona C',   hum: 20, temp: 28, ce: 0.9 },
  { id: 'S013', parc: 'P003', tipo: 'Estación climática',  modelo: 'Davis Vantage Pro',    estado: 'activo',      bat: 96, prof: 0,  zona: 'Estacion', hum: 52, temp: 34, ce: 0   },
  { id: 'S014', parc: 'P001', tipo: 'Caudalímetro',        modelo: 'Seametrics AG3000',    estado: 'activo',      bat: 90, prof: 0,  zona: 'Cabezal',  hum: 0,  temp: 0,  ce: 0   },
  { id: 'S015', parc: 'P002', tipo: 'Caudalímetro',        modelo: 'Seametrics AG3000',    estado: 'activo',      bat: 88, prof: 0,  zona: 'Cabezal',  hum: 0,  temp: 0,  ce: 0   },
];

const RIEGOS = [
  { fecha: '2025-06-15', pid: 'P005', metodo: 'Aspersión',  litros: 15300000, dur: 145, ca: 918, ce: 2142, motivo: 'Estrés hídrico crítico' },
  { fecha: '2025-06-12', pid: 'P002', metodo: 'Microasp.',  litros: 4896000,  dur: 82,  ca: 294, ce: 587,  motivo: 'Programado'             },
  { fecha: '2025-06-10', pid: 'P001', metodo: 'Goteo',      litros: 8160000,  dur: 134, ca: 490, ce: 734,  motivo: 'Programado'             },
  { fecha: '2025-06-08', pid: 'P003', metodo: 'Goteo',      litros: 6800000,  dur: 112, ca: 408, ce: 612,  motivo: 'Déficit hídrico'        },
  { fecha: '2025-06-06', pid: 'P004', metodo: 'Goteo',      litros: 1470000,  dur: 48,  ca: 88,  ce: 132,  motivo: 'Programado'             },
  { fecha: '2025-06-03', pid: 'P005', metodo: 'Aspersión',  litros: 12240000, dur: 116, ca: 734, ce: 1714, motivo: 'Programado'             },
  { fecha: '2025-06-01', pid: 'P001', metodo: 'Goteo',      litros: 9350000,  dur: 153, ca: 561, ce: 842,  motivo: 'Programado'             },
];

const ALERTAS = [
  { p: 'alta',  tipo: 'Estrés hídrico',  pid: 'P005', msg: 'Se detecta déficit de agua en Frijol – Lote 5. Riego urgente en próximas 24h.',       hora: 'Hace 1 hora',  atendida: false },
  { p: 'alta',  tipo: 'Sensor offline',  pid: 'P005', msg: 'Sensor S010 sin comunicación desde hace 6 horas. Verificar batería y conexión.',        hora: 'Hace 6 horas', atendida: false },
  { p: 'media', tipo: 'Humedad elevada', pid: 'P004', msg: 'Humedad en Jitomate – Inv. 1 supera el 75%. Riesgo de enfermedades radiculares.',       hora: 'Hace 3 horas', atendida: false },
  { p: 'baja',  tipo: 'Batería baja',    pid: 'P002', msg: 'Sensor S005 en Chile – Lote 2 con batería al 18%. Reemplazar pronto.',                  hora: 'Hace 1 día',   atendida: true  },
  { p: 'baja',  tipo: 'ETc elevada',     pid: 'P001', msg: 'ETc promedio últimos 7 días supera 6 mm/día. Considerar ajuste en frecuencia.',         hora: 'Hace 2 días',  atendida: true  },
];

// ── HELPERS ───────────────────────────────────────────────────────────────────
const humColor = h => h >= 60 ? '#52b788' : h >= 35 ? '#f59e0b' : '#ef4444';
const fmtL     = l => l >= 1e6 ? (l / 1e6).toFixed(2) + ' ML' : l >= 1000 ? (l / 1000).toFixed(0) + ' m³' : l + ' L';
const fmtMXN   = v => '$' + v.toLocaleString('es-MX');

function estadoBadge(e) {
  const cfg = {
    optimo:         { cls: 'b-opt', label: 'Óptimo',        icon: 'check-circle',  c: '#15803d' },
    atencion:       { cls: 'b-ate', label: 'Atención',       icon: 'clock',         c: '#b45309' },
    estres_hidrico: { cls: 'b-est', label: 'Estrés hídrico', icon: 'alert-triangle', c: '#b91c1c' },
  };
  const { cls, label, icon, c } = cfg[e] || cfg.optimo;
  return `<span class="badge-e ${cls}">${ic(icon, 11, c)} ${label}</span>`;
}

function genHum(base, obj, n = 30) {
  let vals = [], h = base;
  for (let i = 0; i < n; i++) {
    h += (Math.random() - .48) * 3;
    if (h < obj - 18) h += 8;
    if (h > 96) h = 96;
    if (h < 4)  h = 4;
    vals.push(Math.round(h * 10) / 10);
  }
  return vals;
}

const labels30 = Array.from({ length: 30 }, (_, i) => {
  const d = new Date(2025, 4, 16 + i);
  return `${d.getDate()}/${d.getMonth() + 1}`;
});

// ── CHARTS STORE ──────────────────────────────────────────────────────────────
const CH = {};

// ── NAVIGATION ────────────────────────────────────────────────────────────────
const PAGE_META = {
  dashboard: ['Buenas tardes, Omar',    'Resumen de cultivos · Ciclo PV-2025'],
  parcelas:  ['Mis Cultivos',           'DR-075 Sinaloa · 5 parcelas activas'],
  riego:     ['Gestión de Riego',       'Historial y recomendaciones'],
  sensores:  ['Sensores IoT',           '15 dispositivos · DR-075'],
  alertas:   ['Alertas del sistema',    '3 alertas activas requieren atención'],
  reportes:  ['Reportes y Análisis',    'Ciclo Primavera-Verano 2025'],
};

function showView(v) {
  document.querySelectorAll('.view').forEach(x => x.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(x => x.classList.remove('active'));
  document.getElementById('view-' + v).classList.add('active');
  document.getElementById('nav-' + v).classList.add('active');
  document.getElementById('tb-title').textContent = PAGE_META[v][0];
  document.getElementById('tb-sub').textContent   = PAGE_META[v][1];
  feather.replace();

  const renders = {
    dashboard: () => !CH.hum      && renderDashboard(),
    parcelas:  () => !document.getElementById('grid-parc').children.length && renderParcelas(),
    riego:     () => !CH.consumo  && renderRiego(),
    sensores:  () => !document.getElementById('sens-list').children.length && renderSensores(),
    alertas:   () => !document.getElementById('alert-list').children.length && renderAlertas(),
    reportes:  () => !CH.ahorro   && renderReportes(),
  };
  renders[v]?.();
}

// ── DASHBOARD ─────────────────────────────────────────────────────────────────
function renderDashboard() {
  const tb = document.getElementById('t-cultivos');

  PARCELAS.forEach(p => {
    const hc = humColor(p.humedad);
    tb.innerHTML += `<tr>
      <td style="display:flex;align-items:center;gap:8px;padding:11px 14px;">
        <span style="width:28px;height:28px;border-radius:8px;background:${p.color}20;
          display:flex;align-items:center;justify-content:center;">${ic('leaf', 14, p.color, 2)}</span>
        <strong>${p.nombre}</strong>
      </td>
      <td><span class="pill p-blue">${p.etapa} · Día ${p.dia}</span></td>
      <td>${estadoBadge(p.estado)}</td>
      <td>
        <div style="display:flex;align-items:center;gap:8px;">
          <div style="flex:1;height:6px;border-radius:3px;background:#e5e7eb;min-width:80px;overflow:hidden;">
            <div style="height:100%;border-radius:3px;background:${hc};width:${p.humedad}%;"></div>
          </div>
          <span style="font-weight:700;color:${hc};min-width:34px;">${p.humedad}%</span>
        </div>
      </td>
      <td>${p.etc} mm</td>
      <td>${p.estado === 'estres_hidrico'
        ? `<span style="color:var(--red);font-weight:700;display:flex;align-items:center;gap:4px;">${ic('alert-circle', 12, '#ef4444')} Hoy</span>`
        : 'En 2 días'}</td>
      <td><span style="font-weight:700;">${p.wue}</span></td>
    </tr>`;
  });

  CH.hum = new Chart(document.getElementById('ch-hum'), {
    type: 'line',
    data: {
      labels: labels30,
      datasets: [
        { label: 'Humedad %', data: genHum(65, 65), borderColor: '#52b788', backgroundColor: 'rgba(82,183,136,.1)', fill: true, tension: .4, pointRadius: 0, borderWidth: 2 },
        { label: 'Objetivo',  data: Array(30).fill(65), borderColor: '#3b82f6', borderDash: [5, 5], borderWidth: 1.5, pointRadius: 0, fill: false },
        { label: 'Estrés',    data: Array(30).fill(30), borderColor: '#ef4444', borderDash: [5, 5], borderWidth: 1.5, pointRadius: 0, fill: false },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { min: 0, max: 100, grid: { color: 'rgba(0,0,0,.04)' }, ticks: { callback: v => v + '%', font: { size: 10 } } },
        x: { grid: { display: false }, ticks: { font: { size: 10 }, maxTicksLimit: 8 } },
      },
    },
  });
}

// ── PARCELAS ──────────────────────────────────────────────────────────────────
function renderParcelas() {
  const grid = document.getElementById('grid-parc');

  PARCELAS.forEach(p => {
    const hc  = humColor(p.humedad);
    const div = document.createElement('div');
    div.className = 'parc-card';
    div.onclick   = () => showParcelaDetalle(p);
    div.innerHTML = `
      <div class="parc-hdr">
        <div>
          <div class="parc-crop-ic" style="background:${p.color}18;">${ic('leaf', 22, p.color, 2)}</div>
          <div class="parc-name">${p.nombre}</div>
          <div class="parc-meta">${p.area} ha · ${p.sistema}</div>
        </div>
        ${estadoBadge(p.estado)}
      </div>
      <div style="font-size:11px;color:var(--muted);display:flex;justify-content:space-between;margin-bottom:4px;">
        <span>Humedad suelo</span>
        <span style="font-weight:700;color:${hc};">${p.humedad}%</span>
      </div>
      <div class="hum-track">
        <div class="hum-marker" style="left:${p.objetivo}%;"></div>
        <div class="hum-fill" style="width:${Math.min(100, p.humedad)}%;background:${hc};"></div>
      </div>
      <div class="hum-lbl"><span>0%</span><span>Obj: ${p.objetivo}%</span><span>100%</span></div>
      <div class="parc-metrics">
        <div class="pm">
          <div style="display:flex;justify-content:center;margin-bottom:3px;">${ic('droplet', 12, '#3b82f6')}</div>
          <div class="pm-val">${p.etc}</div><div class="pm-lbl">mm/día</div>
        </div>
        <div class="pm">
          <div style="display:flex;justify-content:center;margin-bottom:3px;">${ic('zap', 12, '#f59e0b')}</div>
          <div class="pm-val">${p.wue}</div><div class="pm-lbl">kg/m³</div>
        </div>
        <div class="pm">
          <div style="display:flex;justify-content:center;margin-bottom:3px;">${ic('calendar', 12, p.color)}</div>
          <div class="pm-val" style="color:${p.color};">Día ${p.dia}</div><div class="pm-lbl">${p.etapa}</div>
        </div>
      </div>
      <div style="margin-top:10px;font-size:10px;color:var(--muted);display:flex;align-items:center;gap:4px;">
        ${ic('clock', 10, 'var(--muted)')} Última lectura: hace 5 min
      </div>`;
    grid.appendChild(div);
  });
}

let detChart = null;

function showParcelaDetalle(p) {
  const det = document.getElementById('parc-detalle');
  det.style.display = 'block';
  document.getElementById('det-titulo').innerHTML =
    `${ic('map-pin', 16, 'var(--g600)')} ${p.nombre} · Indicadores`;

  document.getElementById('det-stats').innerHTML = [
    ['Cultivo',           p.cultivo],
    ['Área',              p.area + ' ha'],
    ['Tipo de suelo',     p.suelo],
    ['Sistema de riego',  p.sistema],
    ['Estado',            estadoBadge(p.estado)],
    ['Etapa fenológica',  p.etapa + ' · Día ' + p.dia],
    ['Humedad actual',    `<span style="font-weight:800;color:${humColor(p.humedad)};">${p.humedad}%</span>`],
    ['Humedad objetivo',  p.objetivo + '%'],
    ['ETc promedio 30d',  p.etc + ' mm/día'],
    ['WUE',               p.wue + ' kg/m³'],
    ['CWSI',              p.cwsi],
    ['Agua total',        (p.agua_m3 / 1000).toFixed(0) + ' m³'],
    ['Rendimiento est.',  p.rend + ' ton'],
    ['Ingreso estimado',  fmtMXN(p.ingreso) + ' MXN'],
  ].map(([l, v]) =>
    `<div class="stat-row"><span class="stat-lbl">${l}</span><span class="stat-val">${v}</span></div>`
  ).join('');

  if (detChart) detChart.destroy();
  detChart = new Chart(document.getElementById('ch-det'), {
    type: 'line',
    data: {
      labels: labels30,
      datasets: [
        { label: 'Humedad %', data: genHum(p.humedad, p.objetivo), borderColor: p.color, backgroundColor: p.color + '18', fill: true, tension: .4, pointRadius: 0, borderWidth: 2 },
        { label: 'Objetivo',  data: Array(30).fill(p.objetivo), borderColor: '#3b82f6', borderDash: [5, 5], borderWidth: 1.5, pointRadius: 0, fill: false },
        { label: 'Estrés',    data: Array(30).fill(p.estres),   borderColor: '#ef4444', borderDash: [5, 5], borderWidth: 1.5, pointRadius: 0, fill: false },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { min: 0, max: 100, grid: { color: 'rgba(0,0,0,.04)' }, ticks: { callback: v => v + '%', font: { size: 10 } } },
        x: { grid: { display: false }, ticks: { font: { size: 10 }, maxTicksLimit: 8 } },
      },
    },
  });
  det.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── RIEGO ─────────────────────────────────────────────────────────────────────
function renderRiego() {
  const tb = document.getElementById('t-riegos');

  RIEGOS.forEach(r => {
    const p = PARCELAS.find(x => x.id === r.pid);
    tb.innerHTML += `<tr>
      <td>${r.fecha}</td>
      <td style="display:flex;align-items:center;gap:7px;padding:11px 14px;">
        <span style="width:24px;height:24px;border-radius:6px;background:${p.color}20;
          display:flex;align-items:center;justify-content:center;">${ic('leaf', 12, p.color)}</span>
        ${p.nombre}
      </td>
      <td><span class="pill p-blue">${r.metodo}</span></td>
      <td><strong>${fmtL(r.litros)}</strong></td>
      <td>${r.dur} min</td>
      <td>${fmtMXN(r.ca)}</td>
      <td>${fmtMXN(r.ce)}</td>
      <td style="color:var(--muted);">${r.motivo}</td>
    </tr>`;
  });

  CH.consumo = new Chart(document.getElementById('ch-consumo'), {
    type: 'bar',
    data: {
      labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
      datasets: [{
        data: [4200, 3800, 5100, 6800, 7200, 6400],
        backgroundColor: 'rgba(82,183,136,.7)',
        borderColor: '#52b788',
        borderWidth: 2,
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { grid: { color: 'rgba(0,0,0,.04)' }, ticks: { font: { size: 10 } } },
        x: { grid: { display: false }, ticks: { font: { size: 10 } } },
      },
    },
  });

  const ef = document.getElementById('ef-list');
  PARCELAS.forEach(p => {
    const pct = Math.min(98, 55 + Math.round(p.wue * 3 + 5));
    ef.innerHTML += `<div class="prog-row">
      <span class="prog-lbl">${ic('leaf', 12, p.color)} ${p.cultivo}</span>
      <div class="prog-bar"><div class="prog-fill" style="width:${pct}%;background:${p.color};"></div></div>
      <span class="prog-val">${pct}%</span>
    </div>`;
  });
}

// ── SENSORES ──────────────────────────────────────────────────────────────────
function renderSensores() {
  const list     = document.getElementById('sens-list');
  const statusCfg = {
    activo:       { icon: 'check-circle', color: 'var(--g500)',  label: 'Activo'      },
    bateria_baja: { icon: 'battery',      color: 'var(--amber)', label: 'Batería baja'},
    offline:      { icon: 'wifi-off',     color: 'var(--red)',   label: 'Offline'     },
  };

  SENSORES.forEach(s => {
    const p   = PARCELAS.find(x => x.id === s.parc);
    const sc  = statusCfg[s.estado];
    const bc  = s.bat > 50 ? '#52b788' : s.bat > 20 ? '#f59e0b' : '#ef4444';
    const sensorIcon = s.tipo.includes('climática') ? 'thermometer' : s.tipo.includes('Caudal') ? 'activity' : 'droplet';

    const div = document.createElement('div');
    div.className = 'sens-card';
    div.innerHTML = `
      <div class="sens-ic">${ic(sensorIcon, 20, '#3b82f6')}</div>
      <div style="flex:1;">
        <div style="font-size:13px;font-weight:600;">${s.id} · ${s.tipo}</div>
        <div style="font-size:11px;color:var(--muted);margin-top:2px;">
          ${s.modelo} · ${ic('leaf', 10, p?.color ?? '#52b788')} ${p?.nombre} · ${s.zona}
          ${s.prof ? ` · ${s.prof} cm` : ''}
        </div>
        ${s.hum
          ? `<div style="display:flex;gap:16px;margin-top:6px;font-size:12px;color:var(--muted);">
               <span>${ic('droplet', 12, '#3b82f6')} <strong style="color:var(--text);">${s.hum}%</strong></span>
               <span>${ic('thermometer', 12, '#f59e0b')} <strong style="color:var(--text);">${s.temp}°C</strong></span>
               ${s.ce ? `<span>${ic('zap', 12, '#a855f7')} <strong style="color:var(--text);">${s.ce} dS/m</strong></span>` : ''}
             </div>`
          : '<div style="font-size:11px;color:var(--muted);margin-top:6px;">Lecturas en tiempo real</div>'
        }
      </div>
      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;">
        <span style="color:${sc.color};font-size:12px;font-weight:600;display:flex;align-items:center;gap:4px;">
          ${ic(sc.icon, 12, sc.color)} ${sc.label}
        </span>
        <span style="font-size:11px;color:var(--muted);">Batería ${s.bat}%</span>
        <div class="bat-bar"><div class="bat-fill" style="width:${s.bat}%;background:${bc};"></div></div>
        <span style="font-size:10px;color:var(--muted);display:flex;align-items:center;gap:3px;">
          ${ic('clock', 10, 'var(--muted)')} hace 5 min
        </span>
      </div>`;
    list.appendChild(div);
  });
}

// ── ALERTAS ───────────────────────────────────────────────────────────────────
function renderAlertas() {
  const list = document.getElementById('alert-list');
  const cfg  = {
    alta:  { icon: 'alert-octagon',  icBg: 'var(--red-l)',   icC: 'var(--red)',   pillCls: 'p-red'   },
    media: { icon: 'alert-triangle', icBg: 'var(--amber-l)', icC: 'var(--amber)', pillCls: 'p-amber' },
    baja:  { icon: 'info',           icBg: 'var(--g100)',    icC: 'var(--g600)',  pillCls: 'p-green' },
  };

  ALERTAS.forEach(a => {
    const p                          = PARCELAS.find(x => x.id === a.pid);
    const { icon, icBg, icC, pillCls } = cfg[a.p];
    list.innerHTML += `
      <div class="alert-card ${a.p}" style="${a.atendida ? 'opacity:.5;' : ''}">
        <div class="alert-ic" style="background:${icBg};">${ic(icon, 18, icC)}</div>
        <div style="flex:1;">
          <div style="font-size:13px;font-weight:700;display:flex;align-items:center;gap:6px;">
            ${ic('leaf', 12, p?.color ?? '#52b788')} ${a.tipo} · ${p?.nombre}
          </div>
          <div style="font-size:12px;color:var(--muted);margin-top:4px;">${a.msg}</div>
          <div style="font-size:11px;color:var(--muted);margin-top:6px;display:flex;align-items:center;gap:4px;">
            ${ic('clock', 10, 'var(--muted)')} ${a.hora}
            ${a.atendida ? `<span style="color:var(--g600);margin-left:6px;display:flex;align-items:center;gap:3px;">${ic('check', 10, 'var(--g600)')} Atendida</span>` : ''}
          </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px;">
          <span class="pill ${pillCls}">${a.p.toUpperCase()}</span>
          ${!a.atendida ? `<button class="btn btn-primary btn-sm"
            onclick="this.closest('.alert-card').style.opacity='.5'">${ic('check', 12, '#fff')} Atender</button>` : ''}
        </div>
      </div>`;
  });
}

// ── REPORTES ──────────────────────────────────────────────────────────────────
function renderReportes() {
  CH.ahorro = new Chart(document.getElementById('ch-ahorro'), {
    type: 'bar',
    data: {
      labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
      datasets: [{
        data: [142, 128, 165, 88, 203, 145, 118],
        backgroundColor: 'rgba(82,183,136,.7)',
        borderColor: '#52b788',
        borderWidth: 2,
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { grid: { color: 'rgba(0,0,0,.04)' }, ticks: { font: { size: 10 } } },
        x: { grid: { display: false }, ticks: { font: { size: 10 } } },
      },
    },
  });

  CH.rend = new Chart(document.getElementById('ch-rend'), {
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
      plugins: { legend: { position: 'right', labels: { font: { size: 11 }, padding: 12 } } },
    },
  });

  CH.et0 = new Chart(document.getElementById('ch-et0'), {
    type: 'line',
    data: {
      labels: labels30,
      datasets: [{
        label: 'ET₀ mm/día',
        data: Array.from({ length: 30 }, () => +(3.5 + Math.random() * 4).toFixed(2)),
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245,158,11,.1)',
        fill: true,
        tension: .4,
        pointRadius: 0,
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { grid: { color: 'rgba(0,0,0,.04)' }, ticks: { font: { size: 10 } } },
        x: { grid: { display: false }, ticks: { font: { size: 10 }, maxTicksLimit: 10 } },
      },
    },
  });
}

// ── INIT ──────────────────────────────────────────────────────────────────────
feather.replace();
renderDashboard();
