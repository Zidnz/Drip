const API_BASE = window.DRIP_API_BASE || "http://localhost:8000";

// ---------------------------------------------------------------------------
// DATOS DEMO — se usan cuando el backend no está disponible
// ---------------------------------------------------------------------------
const DEMO_PARCELAS = [
  { id: "P01", nombre: "Culiacan Norte",    municipio: "Culiacan",  cultivo: "Tomate",   variedad: "Saladette", area_ha: 5.2,  lat: 24.79, lon: -107.39 },
  { id: "P02", nombre: "Navolato Sur",      municipio: "Navolato",  cultivo: "Maiz",     variedad: "Hibrido",   area_ha: 8.1,  lat: 24.72, lon: -107.69 },
  { id: "P03", nombre: "El Dorado",         municipio: "Culiacan",  cultivo: "Tomate",   variedad: "Cherry",    area_ha: 3.5,  lat: 24.32, lon: -107.35 },
  { id: "P04", nombre: "Guasave Poniente",  municipio: "Guasave",   cultivo: "Garbanzo", variedad: "Blanco",    area_ha: 12.0, lat: 25.56, lon: -108.46 },
  { id: "P05", nombre: "Los Mochis Norte",  municipio: "Ahome",     cultivo: "Cana",     variedad: "Azucarera", area_ha: 20.0, lat: 25.79, lon: -109.05 },
];

function buildDemoSensores(pid, thetaBase) {
  const sensores = {};
  for (let f = 1; f <= 3; f++) {
    for (let c = 1; c <= 4; c++) {
      const id = `${pid}_F${f}C${c}`;
      const offset = (Math.sin(f * 3 + c * 7 + pid.charCodeAt(1)) * 0.07);
      const theta = Math.max(0.28, Math.min(0.88, thetaBase + offset));
      const valido = !(f === 2 && c === 2);
      sensores[id] = { theta_sensor: +theta.toFixed(4), theta_real: +theta.toFixed(4), valido };
    }
  }
  return sensores;
}

function buildDemoData(pid) {
  const configs = {
    P01: { theta: 0.68, decision: "Sin deficit",         lamina: 0.0, et0: 5.2, temp: 28.5, confianza: 87 },
    P02: { theta: 0.55, decision: "Planificar riego",    lamina: 6.2, et0: 5.8, temp: 31.0, confianza: 75 },
    P03: { theta: 0.42, decision: "Accion inmediata",    lamina: 14.4, et0: 6.1, temp: 30.2, confianza: 69 },
    P04: { theta: 0.72, decision: "Sin deficit",         lamina: 0.0, et0: 4.9, temp: 27.1, confianza: 91 },
    P05: { theta: 0.61, decision: "Planificar riego",    lamina: 4.1, et0: 5.5, temp: 29.8, confianza: 80 },
  };
  const c = configs[pid] || configs.P01;
  const info = DEMO_PARCELAS.find((p) => p.id === pid) || DEMO_PARCELAS[0];

  const sensores = buildDemoSensores(pid, c.theta);
  const n_validos = Object.values(sensores).filter((s) => s.valido).length;

  const explicacion = [
    `RED DE SENSORES: Operativa (${n_validos}/12 sensores validos)`,
    `CLIMA AMBIENTAL: Temperatura: ${Math.round(c.temp - 2)}C. Humedad: 64%. Viento: 2.3 m/s. ET0: ${c.et0} mm/dia`,
    `DECISION: ${c.decision}. Humedad actual: ${Math.round(c.theta * 100)}%. Lamina: ${c.lamina} mm`,
    `PROYECCION: Condiciones ${c.decision === "Sin deficit" ? "estables. Autonomia >7 dias" : "en descenso. Riego recomendado en 24h"}`,
    `SENSORES OPERATIVOS: ${n_validos}/12 activos. Rango: ${Math.round((c.theta - 0.06) * 100)}% - ${Math.round((c.theta + 0.06) * 100)}%`,
    `PRIORIDAD DE RIEGO: ${c.decision === "Accion inmediata" ? "Urgente" : c.decision === "Planificar riego" ? "Alta" : "Baja"} | CONFIANZA DEL SISTEMA: ${c.confianza}%`,
  ].join("\n\n");

  return {
    id: pid,
    nombre: info.nombre,
    municipio: info.municipio,
    cultivo: info.cultivo,
    area_ha: info.area_ha,
    theta: c.theta,
    theta_pct: Math.round(c.theta * 100 * 10) / 10,
    decision: c.decision,
    lamina_mm: c.lamina,
    volumen_m3: +(c.lamina * info.area_ha * 10).toFixed(1),
    n_validos,
    n_total: 12,
    confianza: c.confianza,
    temp_suelo_promedio: c.temp,
    et0: c.et0,
    sensores,
    explicacion,
    umbrales: { umbral_pct: 60.0, critico_pct: 40.0, fc_pct: 85.0 },
    timestamp: new Date().toLocaleString("es-MX", { dateStyle: "medium", timeStyle: "short" }),
  };
}

let demoMode = false;

const state = {
  parcelas: [],
  currentParcela: null,
  parcelaData: null,
  currentTab: "inicio",
  sensorMetric: "humedad",
  alertFilter: "todas",
};

const el = {
  parcelaSelect: document.getElementById("parcela-select"),
  refreshBtn: document.getElementById("btn-refresh"),
  status: document.getElementById("status"),
  error: document.getElementById("error"),
  clock: document.getElementById("clock"),
  contextLine: document.getElementById("context-line"),
  weatherText: document.getElementById("weather-text"),
  navItems: document.querySelectorAll(".nav-item"),
  tabPanels: document.querySelectorAll(".tab-panel"),
  toggleHum: document.getElementById("toggle-humedad"),
  toggleTemp: document.getElementById("toggle-temperatura"),
  sensorBars: document.getElementById("sensor-bars"),
  sensorDonut: document.getElementById("sensor-donut"),
  sensorLegend: document.getElementById("sensor-state-legend"),
  sensorNodes: document.getElementById("sensor-nodes"),
  sensorKpiOptimo: document.getElementById("sensor-kpi-optimo"),
  sensorKpiAtencion: document.getElementById("sensor-kpi-atencion"),
  sensorKpiCritico: document.getElementById("sensor-kpi-critico"),
  chart24h: document.getElementById("chart-24h"),
  chart7d: document.getElementById("chart-7d"),
  iaEstado: document.getElementById("ia-estado"),
  iaLamina: document.getElementById("ia-lamina"),
  iaVolumen: document.getElementById("ia-volumen"),
  iaExplicacion: document.getElementById("ia-explicacion"),
  iaConfianzaMain: document.getElementById("ia-confianza-main"),
  iaConfianzaInline: document.getElementById("ia-confianza-inline"),
  iaConfianzaLevel: document.getElementById("ia-confianza-level"),
  iaConfidenceFill: document.getElementById("ia-confidence-fill"),
  iaMiniHumedad: document.getElementById("ia-mini-humedad"),
  iaMiniEt0: document.getElementById("ia-mini-et0"),
  iaMiniDeficit: document.getElementById("ia-mini-deficit"),
  iaMiniSensores: document.getElementById("ia-mini-sensores"),
  iaMiniTemp: document.getElementById("ia-mini-temp"),
  iaMiniRiesgo: document.getElementById("ia-mini-riesgo"),
  iaRiskLabel: document.getElementById("ia-risk-label"),
  parcelasComparativa: document.getElementById("parcelas-comparativa"),
  parcelasRanking: document.getElementById("parcelas-ranking"),
  parcelasRadar: document.getElementById("parcelas-radar"),
  alertList: document.getElementById("alert-list"),
  alertFilterRow: document.getElementById("alert-filter-row"),
  btnGoAi: document.getElementById("btn-go-ai"),
  heroLamina: document.getElementById("hero-lamina"),
  heroDuracion: document.getElementById("hero-duracion"),
  heroCultivo: document.getElementById("hero-cultivo"),
  kpiHumedad: document.getElementById("kpi-humedad"),
  kpiHumedadSub: document.getElementById("kpi-humedad-sub"),
  kpiTemp: document.getElementById("kpi-temp"),
  kpiTempSub: document.getElementById("kpi-temp-sub"),
  kpiDecision: document.getElementById("kpi-decision"),
  kpiDecisionSub: document.getElementById("kpi-decision-sub"),
  kpiConfianza: document.getElementById("kpi-confianza"),
  kpiConfianzaSub: document.getElementById("kpi-confianza-sub"),
};

function setStatus(message) {
  el.status.textContent = message;
}

function setError(message) {
  el.error.textContent = message || "";
}

async function getJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

function colorByValue(value) {
  if (value >= 60) return "#7b9b35";
  if (value >= 40) return "#e8a838";
  return "#d45b3a";
}

function renderLineChart(target, values) {
  if (!target || !values.length) return;
  const width = 100;
  const height = 100;
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;

  const pointsArr = values
    .map((v, i) => {
      const x = (i / (values.length - 1 || 1)) * width;
      const y = height - ((v - min) / range) * height;
      return { x: x.toFixed(2), y: y.toFixed(2) };
    });

  const points = pointsArr.map((p) => `${p.x},${p.y}`).join(" ");
  const area = `${points} ${width},100 0,100`;
  const last = pointsArr[pointsArr.length - 1];
  const first = pointsArr[0];

  target.innerHTML = `
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" width="100%" height="100%">
      <defs>
        <linearGradient id="drip-area-gradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#9dc5da" stop-opacity="0.52"></stop>
          <stop offset="100%" stop-color="#9dc5da" stop-opacity="0.03"></stop>
        </linearGradient>
      </defs>
      <rect x="0" y="20" width="100" height="20" fill="rgba(123,155,53,0.12)"></rect>
      <line x1="0" y1="20" x2="100" y2="20" stroke="rgba(123,155,53,0.24)" stroke-width="0.8" stroke-dasharray="2 2"></line>
      <line x1="0" y1="40" x2="100" y2="40" stroke="rgba(123,155,53,0.24)" stroke-width="0.8" stroke-dasharray="2 2"></line>
      <line x1="0" y1="80" x2="100" y2="80" stroke="rgba(124,156,168,0.26)" stroke-width="0.8" stroke-dasharray="2 2"></line>
      <line x1="0" y1="60" x2="100" y2="60" stroke="rgba(124,156,168,0.26)" stroke-width="0.8" stroke-dasharray="2 2"></line>
      <line x1="0" y1="40" x2="100" y2="40" stroke="rgba(124,156,168,0.26)" stroke-width="0.8" stroke-dasharray="2 2"></line>
      <polyline points="${area}" fill="url(#drip-area-gradient)" stroke="none"></polyline>
      <polyline points="${points}" fill="none" stroke="#385E5E" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"></polyline>
      <circle cx="${first.x}" cy="${first.y}" r="1.5" fill="#385E5E"></circle>
      <circle cx="${last.x}" cy="${last.y}" r="2.2" fill="#385E5E"></circle>
    </svg>
  `;
}

function showTab(tabName) {
  state.currentTab = tabName;
  el.tabPanels.forEach((panel) => {
    panel.classList.toggle("active", panel.id === `tab-${tabName}`);
  });
  el.navItems.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabName);
  });
}

function normalizeDecision(decision = "") {
  const d = String(decision).toLowerCase();
  if (d.includes("inmediat")) return "Accion inmediata";
  if (d.includes("plan")) return "Planificar riego";
  return "Sin deficit";
}

const IA_SECTION_META = {
  "RED DE SENSORES": {
    title: "Red de sensores",
    badge: "IoT",
    icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="7" width="14" height="10" rx="3"></rect><path d="M9 11h6"></path><path d="M12 17v3"></path><path d="M8 20h8"></path><path d="M8 4l2 2"></path><path d="M16 4l-2 2"></path></svg>`,
  },
  "CLIMA AMBIENTAL": {
    title: "Clima ambiental",
    badge: "Clima",
    icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17.5 18H8a4 4 0 1 1 .7-7.9A5.5 5.5 0 0 1 19 12.5 2.8 2.8 0 0 1 17.5 18z"></path><path d="M5 20h14"></path></svg>`,
  },
  DECISION: {
    title: "Decision",
    badge: "IA",
    icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v3"></path><path d="M12 18v3"></path><path d="M4.9 4.9l2.1 2.1"></path><path d="M17 17l2.1 2.1"></path><circle cx="12" cy="12" r="5"></circle><path d="M10 12l1.4 1.4L15 10"></path></svg>`,
  },
  PROYECCION: {
    title: "Proyeccion",
    badge: "Trend",
    icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 17l5-5 4 4 7-8"></path><path d="M15 8h5v5"></path></svg>`,
  },
  "SENSORES OPERATIVOS": {
    title: "Sensores operativos",
    badge: "Estado",
    icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="5" width="16" height="14" rx="3"></rect><path d="M8 9h8"></path><path d="M8 13h4"></path><path d="M16 13l1.5 1.5L20 12"></path></svg>`,
  },
  SENSORES: {
    title: "Sensores operativos",
    badge: "Estado",
    icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="5" width="16" height="14" rx="3"></rect><path d="M8 9h8"></path><path d="M8 13h4"></path><path d="M16 13l1.5 1.5L20 12"></path></svg>`,
  },
  "PRIORIDAD DE RIEGO": {
    title: "Prioridad de riego",
    badge: "Riesgo",
    icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l8 16H4l8-16z"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path></svg>`,
  },
  "CONFIANZA DEL SISTEMA": {
    title: "Confianza del sistema",
    badge: "Confianza",
    icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l7 4v5c0 4.5-2.9 7.4-7 9-4.1-1.6-7-4.5-7-9V7l7-4z"></path><path d="M9 12l2 2 4-5"></path></svg>`,
  },
};

function normalizeIaExplanationText(value = "") {
  return String(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/DECISI\u00c3.N/g, "DECISION")
    .replace(/PROYECCI\u00c3.N/g, "PROYECCION")
    .replace(/evapotranspiraci\u00c3.n/g, "evapotranspiracion")
    .replace(/D\u00c3.ficit/g, "Deficit")
    .replace(/h\u00c3.drico/g, "hidrico")
    .replace(/cr\u00c3.tico/g, "critico")
    .replace(/Autonom\u00c3.a/g, "Autonomia")
    .replace(/v\u00c3.lidos/g, "validos")
    .replace(/m\u00c3.s/g, "mas")
    .replace(/c\u00c3.lido/g, "calido")
    .replace(/\u00e2\u20ac\u00a2|\u2022/g, "\n")
    .replace(/\u00e2\u0153\u201c|\u2713|\u00e2\u0161\u00a0|\u26a0|\u00f0\u0178\S*|[\u{1F300}-\u{1FAFF}]/gu, "")
    .replace(/[\u00c2]/g, "")
    .replace(/[ \t]+\n/g, "\n")
    .trim();
}

function cleanIaMetric(value = "") {
  return String(value)
    .replace(/^[\s:|.-]+/, "")
    .replace(/[\s|.-]+$/, "")
    .replace(/\s+/g, " ")
    .trim();
}

function parseIaExplanation(rawText) {
  const text = normalizeIaExplanationText(rawText);
  if (!text) return [];

  const pattern = /(RED DE SENSORES|CLIMA AMBIENTAL|DECISION|PROYECCION|SENSORES OPERATIVOS|SENSORES|PRIORIDAD DE RIEGO|CONFIANZA DEL SISTEMA)\s*:/g;
  const matches = [...text.matchAll(pattern)];

  if (!matches.length) {
    return [{
      key: "RESUMEN",
      title: "Resumen IA",
      badge: "IA",
      icon: IA_SECTION_META.DECISION.icon,
      items: [cleanIaMetric(text)],
    }];
  }

  return matches.map((match, index) => {
    const key = match[1];
    const meta = IA_SECTION_META[key] || {
      title: key.toLowerCase(),
      badge: "Insight",
      icon: IA_SECTION_META.DECISION.icon,
    };
    const start = match.index + match[0].length;
    const end = matches[index + 1]?.index ?? text.length;
    const body = text.slice(start, end);
    const items = body
      .split(/\n+/)
      .map(cleanIaMetric)
      .filter(Boolean);

    return {
      key,
      title: meta.title,
      badge: meta.badge,
      icon: meta.icon,
      items,
    };
  }).filter((section) => section.items.length);
}

function renderIaInsights(rawText) {
  if (!el.iaExplicacion) return;

  const sections = parseIaExplanation(rawText);
  el.iaExplicacion.textContent = "";

  if (!sections.length) {
    const empty = document.createElement("p");
    empty.className = "ia-insight-empty";
    empty.textContent = "Sin datos.";
    el.iaExplicacion.appendChild(empty);
    return;
  }

  sections.forEach((section) => {
    const card = document.createElement("article");
    card.className = "ia-insight-item";

    const head = document.createElement("div");
    head.className = "ia-insight-item-head";

    const icon = document.createElement("span");
    icon.className = "ia-insight-icon";
    icon.innerHTML = section.icon;

    const titleWrap = document.createElement("div");
    titleWrap.className = "ia-insight-title-wrap";

    const title = document.createElement("p");
    title.className = "ia-insight-title";
    title.textContent = section.title;

    const badge = document.createElement("span");
    badge.className = "ia-insight-badge";
    badge.textContent = section.badge;

    titleWrap.append(title, badge);
    head.append(icon, titleWrap);

    const list = document.createElement("ul");
    list.className = "ia-insight-metrics";
    section.items.forEach((item) => {
      const row = document.createElement("li");
      row.textContent = item;
      list.appendChild(row);
    });

    card.append(head, list);
    el.iaExplicacion.appendChild(card);
  });
}

function buildSensorSeries(data) {
  const sensores = Object.entries(data.sensores || {});
  const baseTemp = Number(data.temp_suelo_promedio || 28);

  return sensores.map(([id, sensor], idx) => {
    const humedad = sensor.valido ? Number((sensor.theta_sensor * 100).toFixed(1)) : 0;
    const temp = Number((baseTemp + ((idx % 4) - 1.5) * 0.9).toFixed(1));
    return { id, valido: sensor.valido, humedad, temp };
  });
}

function renderHome(data) {
  const decision = normalizeDecision(data.decision);
  el.kpiHumedad.textContent = `${data.theta_pct}%`;
  el.kpiHumedadSub.textContent = `Umbral ${data.umbrales.umbral_pct}%`;
  el.kpiTemp.textContent = `${data.temp_suelo_promedio ?? "--"} C`;
  el.kpiTempSub.textContent = `ET0 ${data.et0} mm`;
  el.kpiDecision.textContent = decision;
  el.kpiDecisionSub.textContent = `Lamina ${data.lamina_mm} mm`;
  el.kpiConfianza.textContent = `${data.confianza}%`;
  el.kpiConfianzaSub.textContent = `${data.n_validos} sensores validos`;
  el.heroLamina.textContent = `Lamina recomendada ${data.lamina_mm} mm`;
  el.heroDuracion.textContent = `Duracion estimada ${Math.max(8, Math.round(Number(data.lamina_mm || 0) * 2.8))} min`;
  el.heroCultivo.textContent = `${data.id} · ${data.nombre || "Lote activo"}`;

  const series24h = [
    data.theta_pct + 5,
    data.theta_pct + 4,
    data.theta_pct + 3,
    data.theta_pct + 2,
    data.theta_pct + 1,
    data.theta_pct,
    data.theta_pct - 2,
    data.theta_pct - 3,
  ].map((v) => Math.max(10, Math.min(95, Math.round(v))));

  renderLineChart(el.chart24h, series24h);
}

function renderSensores(data) {
  const series = buildSensorSeries(data);
  const valueKey = state.sensorMetric === "temperatura" ? "temp" : "humedad";
  const maxValue = state.sensorMetric === "temperatura" ? 45 : 100;

  el.sensorBars.innerHTML = series
    .map((s) => {
      const v = s[valueKey];
      const width = Math.max(2, (v / maxValue) * 100);
      const fill = colorByValue(state.sensorMetric === "temperatura" ? (v / 45) * 100 : v);
      return `
        <div class="bar-row">
          <span>${s.id}</span>
          <div class="bar-track"><div class="bar-fill" style="width:${width}%;background:${fill};"></div></div>
          <span>${v}${state.sensorMetric === "temperatura" ? " C" : "%"}</span>
        </div>
      `;
    })
    .join("");

  const counts = { optimo: 0, atencion: 0, critico: 0 };
  series.forEach((s) => {
    if (!s.valido || s.humedad < 40) counts.critico += 1;
    else if (s.humedad < 60) counts.atencion += 1;
    else counts.optimo += 1;
  });

  const total = Math.max(1, series.length);
  const pOpt = (counts.optimo / total) * 100;
  const pAte = (counts.atencion / total) * 100;
  const pCri = (counts.critico / total) * 100;

  el.sensorDonut.style.background = `conic-gradient(#7b9b35 0 ${pOpt}%, #e8a838 ${pOpt}% ${pOpt + pAte}%, #d45b3a ${pOpt + pAte}% 100%)`;
  el.sensorLegend.innerHTML = `
    <li><span>Optimo</span><strong>${counts.optimo}</strong></li>
    <li><span>Atencion</span><strong>${counts.atencion}</strong></li>
    <li><span>Critico</span><strong>${counts.critico}</strong></li>
  `;
  el.sensorKpiOptimo.textContent = counts.optimo;
  el.sensorKpiAtencion.textContent = counts.atencion;
  el.sensorKpiCritico.textContent = counts.critico;

  const ts = data.timestamp || "--";
  const lote = data.id || "--";
  const zona = data.nombre || "Zona activa";
  el.sensorNodes.innerHTML = series
    .map((s, idx) => {
      const estado = !s.valido || s.humedad < 40 ? "Critico" : s.humedad < 60 ? "Atencion" : "Activo";
      const estadoClass = estado === "Activo" ? "ok" : estado === "Atencion" ? "warn" : "crit";
      const bateria = Math.max(22, Math.min(96, 88 - idx * 4));
      const ce = (1.2 + ((idx % 4) * 0.2)).toFixed(1);
      return `
        <article class="sensor-node-card">
          <div class="sensor-node-left">
            <span class="sensor-node-icon">◌</span>
          </div>
          <div class="sensor-node-main">
            <div class="sensor-node-head">
              <h3>${s.id} · Humedad / Temp / CE</h3>
              <span class="sensor-badge ${estadoClass}">${estado}</span>
            </div>
            <p class="sensor-node-meta">Lote ${lote} · ${zona} · Nodo ${idx + 1}</p>
            <div class="sensor-readings">
              <span>Humedad ${s.humedad}%</span>
              <span>Temp ${s.temp} C</span>
              <span>CE ${ce} dS/m</span>
            </div>
            <div class="sensor-node-foot">
              <div class="battery">
                <span>Bat. ${bateria}%</span>
                <div class="battery-bar"><div class="battery-fill" style="width:${bateria}%;"></div></div>
              </div>
              <span class="sensor-updated">Actualizado: ${ts}</span>
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderIa(data) {
  const decision = normalizeDecision(data.decision);
  el.iaEstado.textContent = decision;
  el.iaLamina.textContent = `Lamina: ${data.lamina_mm} mm`;
  el.iaVolumen.textContent = `Volumen: ${data.volumen_m3} m3`;
  renderIaInsights(data.explicacion || "");
  const confianza = Number(data.confianza || 0);
  const riesgo = data.lamina_mm > 0 ? (data.lamina_mm > 8 ? "Alto" : "Medio") : "Bajo";

  if (el.iaConfianzaMain) el.iaConfianzaMain.textContent = `${confianza}%`;
  if (el.iaConfianzaInline) el.iaConfianzaInline.textContent = `${confianza}%`;
  if (el.iaConfidenceFill) el.iaConfidenceFill.style.width = `${Math.max(0, Math.min(100, confianza))}%`;
  if (el.iaConfianzaLevel) {
    el.iaConfianzaLevel.textContent = confianza >= 85 ? "Muy alta" : confianza >= 70 ? "Alta" : confianza >= 50 ? "Media" : "Baja";
  }

  if (el.iaMiniHumedad) el.iaMiniHumedad.textContent = `${data.theta_pct}%`;
  if (el.iaMiniEt0) el.iaMiniEt0.textContent = `${data.et0} mm`;
  if (el.iaMiniDeficit) el.iaMiniDeficit.textContent = `${data.lamina_mm} mm`;
  if (el.iaMiniSensores) el.iaMiniSensores.textContent = `${data.n_validos} / ${data.n_total}`;
  if (el.iaMiniTemp) el.iaMiniTemp.textContent = `${data.temp_suelo_promedio ?? "--"} C`;
  if (el.iaMiniRiesgo) el.iaMiniRiesgo.textContent = riesgo;
  if (el.iaRiskLabel) el.iaRiskLabel.textContent = riesgo;

  const projection = [data.theta_pct, data.theta_pct - 3, data.theta_pct - 5, data.theta_pct - 7, data.theta_pct - 8, data.theta_pct - 10, data.theta_pct - 12]
    .map((v) => Math.max(8, Math.min(95, Math.round(v))));

  renderLineChart(el.chart7d, projection);
}

function buildParcelaComparative() {
  if (!state.parcelas.length || !state.parcelaData) return [];
  const base = Number(state.parcelaData.theta_pct || 60);

  return state.parcelas.map((p, idx) => {
    const score = Math.max(25, Math.min(90, base + 8 - idx * 6));
    return { nombre: p.nombre || p.id, score };
  });
}

function renderParcelas() {
  const rows = buildParcelaComparative().sort((a, b) => b.score - a.score);

  el.parcelasComparativa.innerHTML = rows
    .map((r) => `
      <div class="rank-row">
        <div>
          <div>${r.nombre}</div>
          <div class="rank-bar"><div class="rank-fill" style="width:${r.score}%;background:${colorByValue(r.score)};"></div></div>
        </div>
        <strong>${r.score}%</strong>
      </div>
    `)
    .join("");

  el.parcelasRanking.innerHTML = rows
    .map((r, i) => `<div class="rank-row"><span>${i + 1}. ${r.nombre}</span><strong>${r.score}%</strong></div>`)
    .join("");

  el.parcelasRadar.innerHTML = `
    <svg viewBox="0 0 220 170" width="100%" height="100%" preserveAspectRatio="xMidYMid meet">
      <polygon points="110,18 168,48 168,122 110,152 52,122 52,48" fill="#e9f0ec" stroke="#b8c7bf"/>
      <polygon points="110,34 155,56 152,113 110,136 70,112 67,60" fill="rgba(30,102,112,0.24)" stroke="#1e6670"/>
      <text x="104" y="12" font-size="10">Humedad</text>
      <text x="170" y="50" font-size="10">Temp</text>
      <text x="170" y="128" font-size="10">Crec</text>
      <text x="101" y="166" font-size="10">Estres</text>
      <text x="23" y="128" font-size="10">Conduct</text>
      <text x="16" y="50" font-size="10">Infil</text>
    </svg>
  `;
}

function buildAlerts(data) {
  const ts = data.timestamp || "";
  return [
    { sev: "critica", title: "Humedad critica detectada", detail: "Nodo con humedad por debajo del minimo.", time: ts },
    { sev: "advertencia", title: "Tendencia a baja humedad", detail: "Planificar riego en 24 a 48 horas.", time: ts },
    { sev: "informacion", title: "Actualizacion de clima", detail: `ET0 reportada: ${data.et0} mm.`, time: ts },
  ];
}

function renderAlertas(data) {
  const items = buildAlerts(data).filter((a) => state.alertFilter === "todas" || a.sev === state.alertFilter);
  const border = { critica: "#d45b3a", advertencia: "#e8a838", informacion: "#1e6670" };

  el.alertList.innerHTML = items
    .map((a) => `
      <article class="alert-item" style="border-left-color:${border[a.sev]};">
        <h4>${a.title}</h4>
        <p>${a.detail}</p>
        <p>${a.time}</p>
      </article>
    `)
    .join("");
}

function renderAll(data) {
  state.parcelaData = data;
  el.contextLine.textContent = `${data.id} · ${data.nombre || "Parcela activa"}`;
  el.weatherText.textContent = `${data.temp_suelo_promedio ?? "--"} C · ET0 ${data.et0} mm`;
  renderHome(data);
  renderSensores(data);
  renderIa(data);
  renderParcelas();
  renderAlertas(data);
}

async function loadParcelas() {
  const parcelas = await getJson("/parcelas");
  state.parcelas = parcelas;

  el.parcelaSelect.innerHTML = parcelas
    .map((parcela) => `<option value="${parcela.id}">${parcela.id} - ${parcela.nombre}</option>`)
    .join("");

  if (!parcelas.length) {
    setStatus("No hay parcelas configuradas.");
    return;
  }

  state.currentParcela = parcelas[0].id;
  el.parcelaSelect.value = state.currentParcela;
  await loadParcelaData(state.currentParcela);
}

async function loadParcelaData(parcelaId) {
  setError("");
  setStatus(`Consultando ${parcelaId}...`);

  const data = await getJson(`/parcela/${encodeURIComponent(parcelaId)}`);
  renderAll(data);

  setStatus(`Datos cargados: ${data.timestamp}`);
}

function bindEvents() {
  el.parcelaSelect.addEventListener("change", async (event) => {
    state.currentParcela = event.target.value;
    if (demoMode) {
      const data = buildDemoData(state.currentParcela);
      renderAll(data);
      setStatus(`Datos demo: ${data.timestamp}`);
      return;
    }
    try {
      await loadParcelaData(state.currentParcela);
    } catch (error) {
      setError(error.message);
      setStatus("No se pudieron cargar datos de la parcela.");
    }
  });

  el.refreshBtn.addEventListener("click", async () => {
    el.refreshBtn.disabled = true;
    try {
      if (demoMode) {
        if (state.currentParcela) {
          const data = buildDemoData(state.currentParcela);
          renderAll(data);
          setStatus(`Datos demo actualizados: ${data.timestamp}`);
        }
      } else {
        await fetch(`${API_BASE}/cache/invalidar`, { method: "POST" });
        if (state.currentParcela) await loadParcelaData(state.currentParcela);
      }
    } catch (error) {
      setError(error.message);
      setStatus("Error al actualizar cache.");
    } finally {
      el.refreshBtn.disabled = false;
    }
  });

  el.navItems.forEach((btn) => {
    btn.addEventListener("click", () => showTab(btn.dataset.tab));
  });

  el.toggleHum.addEventListener("click", () => {
    state.sensorMetric = "humedad";
    el.toggleHum.classList.add("active");
    el.toggleTemp.classList.remove("active");
    if (state.parcelaData) renderSensores(state.parcelaData);
  });

  el.toggleTemp.addEventListener("click", () => {
    state.sensorMetric = "temperatura";
    el.toggleTemp.classList.add("active");
    el.toggleHum.classList.remove("active");
    if (state.parcelaData) renderSensores(state.parcelaData);
  });

  el.alertFilterRow.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      state.alertFilter = chip.dataset.filter;
      el.alertFilterRow.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      if (state.parcelaData) renderAlertas(state.parcelaData);
    });
  });

  el.btnGoAi.addEventListener("click", () => showTab("ia"));
}

function startClock() {
  const tick = () => {
    const now = new Date();
    el.clock.textContent = now.toLocaleString("es-MX", { dateStyle: "medium", timeStyle: "short" });
  };
  tick();
  setInterval(tick, 30000);
}

async function loadDemoMode() {
  demoMode = true;
  state.parcelas = DEMO_PARCELAS;

  el.parcelaSelect.innerHTML = DEMO_PARCELAS
    .map((p) => `<option value="${p.id}">${p.id} - ${p.nombre}</option>`)
    .join("");

  state.currentParcela = DEMO_PARCELAS[0].id;
  el.parcelaSelect.value = state.currentParcela;

  const data = buildDemoData(state.currentParcela);
  renderAll(data);

  setError("Modo demo: el backend no esta disponible. Mostrando datos de ejemplo.");
  setStatus("Datos demo cargados.");
}

async function init() {
  startClock();
  bindEvents();
  try {
    await loadParcelas();
  } catch {
    try {
      await loadDemoMode();
    } catch (e2) {
      setError(`Error critico: ${e2.message}`);
      setStatus("No se pudo cargar.");
    }
  }
}

init();

