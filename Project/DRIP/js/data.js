/* ============================================
   DRIP — data.js
   Mock data agrícola — DR-075 Sinaloa
   Ciclo Primavera-Verano 2025
   ============================================ */

const PARCELAS = [
  {
    id: 'P001', nombre: 'Maíz – Lote 1',     cultivo: 'Maíz',     area: 8.5,
    sistema: 'Goteo',          humedad: 72,  objetivo: 65, estres: 30,
    estado: 'optimo',          etapa: 'Desarrollo', dia: 42,
    etc: 5.8,  wue: 1.5,  cwsi: 0.08,
    rend: 52.3, agua_m3: 18420, costo: 12800, ingreso: 287650,
    suelo: 'Franco-arcilloso', color: '#7B9B35', ic_color: '#5F7D2B',
  },
  {
    id: 'P002', nombre: 'Chile – Lote 2',    cultivo: 'Chile',    area: 3.2,
    sistema: 'Microaspersión', humedad: 58,  objetivo: 70, estres: 35,
    estado: 'atencion',        etapa: 'Media',      dia: 68,
    etc: 6.1,  wue: 4.7,  cwsi: 0.28,
    rend: 18.9, agua_m3: 9840,  costo: 7620,  ingreso: 378000,
    suelo: 'Franco-arenoso',   color: '#E8A838', ic_color: '#B07E1A',
  },
  {
    id: 'P003', nombre: 'Papa – Lote 3',     cultivo: 'Papa',     area: 5.0,
    sistema: 'Goteo',          humedad: 68,  objetivo: 65, estres: 30,
    estado: 'optimo',          etapa: 'Media',      dia: 55,
    etc: 4.2,  wue: 4.6,  cwsi: 0.05,
    rend: 31.5, agua_m3: 14200, costo: 9850,  ingreso: 315000,
    suelo: 'Franco',           color: '#7C9CA8', ic_color: '#5A7D8C',
  },
  {
    id: 'P004', nombre: 'Jitomate – Inv. 1', cultivo: 'Jitomate', area: 2.1,
    sistema: 'Goteo',          humedad: 75,  objetivo: 70, estres: 35,
    estado: 'optimo',          etapa: 'Desarrollo', dia: 38,
    etc: 5.5,  wue: 20.4, cwsi: 0.03,
    rend: 29.4, agua_m3: 5620,  costo: 4120,  ingreso: 441000,
    suelo: 'Limoso',           color: '#A8BE6D', ic_color: '#7B9B35',
  },
  {
    id: 'P005', nombre: 'Frijol – Lote 5',   cultivo: 'Frijol',   area: 6.8,
    sistema: 'Aspersión',      humedad: 22,  objetivo: 55, estres: 25,
    estado: 'estres_hidrico',  etapa: 'Inicial',    dia: 18,
    etc: 2.8,  wue: 0.3,  cwsi: 0.61,
    rend: 9.9,  agua_m3: 4180,  costo: 3240,  ingreso: 118800,
    suelo: 'Franco-arcilloso', color: '#D45B3A', ic_color: '#B03A20',
  },
];

const SENSORES = [
  { id: 'S001', parc: 'P001', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',        estado: 'activo',      bat: 87, prof: 60, zona: 'Zona A',   hum: 72, temp: 24, ce: 1.4 },
  { id: 'S002', parc: 'P001', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',        estado: 'activo',      bat: 81, prof: 30, zona: 'Zona B',   hum: 74, temp: 25, ce: 1.3 },
  { id: 'S003', parc: 'P001', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',        estado: 'activo',      bat: 79, prof: 90, zona: 'Zona C',   hum: 69, temp: 23, ce: 1.5 },
  { id: 'S004', parc: 'P002', tipo: 'Humedad / Temp / CE', modelo: 'Sentek EnviroSCAN',  estado: 'activo',      bat: 92, prof: 45, zona: 'Zona A',   hum: 58, temp: 26, ce: 2.1 },
  { id: 'S005', parc: 'P002', tipo: 'Humedad / Temp / CE', modelo: 'Sentek EnviroSCAN',  estado: 'bateria_baja',bat: 18, prof: 30, zona: 'Zona B',   hum: 55, temp: 27, ce: 1.9 },
  { id: 'S006', parc: 'P003', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',        estado: 'activo',      bat: 95, prof: 60, zona: 'Zona A',   hum: 68, temp: 23, ce: 1.2 },
  { id: 'S007', parc: 'P003', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',        estado: 'activo',      bat: 88, prof: 30, zona: 'Zona B',   hum: 71, temp: 24, ce: 1.1 },
  { id: 'S008', parc: 'P004', tipo: 'Humedad / Temp / CE', modelo: 'Sentek EnviroSCAN',  estado: 'activo',      bat: 76, prof: 45, zona: 'Zona A',   hum: 75, temp: 25, ce: 1.8 },
  { id: 'S009', parc: 'P004', tipo: 'Humedad / Temp / CE', modelo: 'Sentek EnviroSCAN',  estado: 'activo',      bat: 83, prof: 30, zona: 'Zona B',   hum: 74, temp: 26, ce: 1.7 },
  { id: 'S010', parc: 'P005', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',        estado: 'offline',     bat: 5,  prof: 60, zona: 'Zona A',   hum: 22, temp: 28, ce: 0.8 },
  { id: 'S011', parc: 'P005', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',        estado: 'bateria_baja',bat: 22, prof: 30, zona: 'Zona B',   hum: 24, temp: 29, ce: 0.7 },
  { id: 'S012', parc: 'P005', tipo: 'Humedad / Temp / CE', modelo: 'Decagon 5TM',        estado: 'activo',      bat: 71, prof: 90, zona: 'Zona C',   hum: 20, temp: 28, ce: 0.9 },
  { id: 'S013', parc: 'P003', tipo: 'Estación climática',  modelo: 'Davis Vantage Pro',  estado: 'activo',      bat: 96, prof: 0,  zona: 'Estacion', hum: 52, temp: 34, ce: 0   },
  { id: 'S014', parc: 'P001', tipo: 'Caudalímetro',        modelo: 'Seametrics AG3000',  estado: 'activo',      bat: 90, prof: 0,  zona: 'Cabezal',  hum: 0,  temp: 0,  ce: 0   },
  { id: 'S015', parc: 'P002', tipo: 'Caudalímetro',        modelo: 'Seametrics AG3000',  estado: 'activo',      bat: 88, prof: 0,  zona: 'Cabezal',  hum: 0,  temp: 0,  ce: 0   },
];

const RIEGOS = [
  { fecha: '2025-06-15', pid: 'P005', metodo: 'Aspersión',   litros: 15300000, dur: 145, ca: 918,  ce: 2142, motivo: 'Estrés hídrico crítico' },
  { fecha: '2025-06-12', pid: 'P002', metodo: 'Microasp.',   litros: 4896000,  dur: 82,  ca: 294,  ce: 587,  motivo: 'Programado'             },
  { fecha: '2025-06-10', pid: 'P001', metodo: 'Goteo',       litros: 8160000,  dur: 134, ca: 490,  ce: 734,  motivo: 'Programado'             },
  { fecha: '2025-06-08', pid: 'P003', metodo: 'Goteo',       litros: 6800000,  dur: 112, ca: 408,  ce: 612,  motivo: 'Déficit hídrico'        },
  { fecha: '2025-06-06', pid: 'P004', metodo: 'Goteo',       litros: 1470000,  dur: 48,  ca: 88,   ce: 132,  motivo: 'Programado'             },
  { fecha: '2025-06-03', pid: 'P005', metodo: 'Aspersión',   litros: 12240000, dur: 116, ca: 734,  ce: 1714, motivo: 'Programado'             },
  { fecha: '2025-06-01', pid: 'P001', metodo: 'Goteo',       litros: 9350000,  dur: 153, ca: 561,  ce: 842,  motivo: 'Programado'             },
];

const ALERTAS = [
  { p: 'alta',  tipo: 'Estrés hídrico',  pid: 'P005', msg: 'Se detecta déficit de agua en Frijol – Lote 5. Riego urgente en próximas 24h.',       hora: 'Hace 1 hora',  atendida: false },
  { p: 'alta',  tipo: 'Sensor offline',  pid: 'P005', msg: 'Sensor S010 sin comunicación desde hace 6 horas. Verificar batería y conexión.',       hora: 'Hace 6 horas', atendida: false },
  { p: 'media', tipo: 'Humedad elevada', pid: 'P004', msg: 'Humedad en Jitomate – Inv. 1 supera el 75%. Riesgo de enfermedades radiculares.',      hora: 'Hace 3 horas', atendida: false },
  { p: 'baja',  tipo: 'Batería baja',    pid: 'P002', msg: 'Sensor S005 en Chile – Lote 2 con batería al 18%. Reemplazar pronto.',                 hora: 'Hace 1 día',   atendida: true  },
  { p: 'baja',  tipo: 'ETc elevada',     pid: 'P001', msg: 'ETc promedio últimos 7 días supera 6 mm/día. Considerar ajuste en frecuencia.',        hora: 'Hace 2 días',  atendida: true  },
];

const CLIMA = {
  temp: 34, hum: 52, viento: 2.4, et0: 6.1, presion: 1012,
  ubicacion: 'Culiacán, Sin.',
  pronostico: [
    { dia: 'Hoy',     icon: 'sun',        max: 34, min: 22, lluvia: 0  },
    { dia: 'Mañana',  icon: 'cloud',      max: 31, min: 20, lluvia: 10 },
    { dia: 'Jue',     icon: 'cloud-rain', max: 28, min: 19, lluvia: 40 },
    { dia: 'Vie',     icon: 'sun',        max: 33, min: 21, lluvia: 5  },
  ],
};

const KPI_REPORTES = {
  ahorroAgua:    23,    // % vs gravedad
  rendimientoT:  142,   // toneladas
  ingresoMXN:    2400000,
  wuePromedio:   6.2,   // kg/m³
};

// ── Helpers ───────────────────────────────────────────────────────────────────
const humColor = h => h >= 60 ? 'var(--green-primary)' : h >= 35 ? 'var(--color-warning)' : 'var(--color-danger)';
const humColorHex = h => h >= 60 ? '#7B9B35' : h >= 35 ? '#E8A838' : '#D45B3A';
const fmtL   = l => l >= 1e6 ? (l / 1e6).toFixed(2) + ' ML' : l >= 1000 ? (l / 1000).toFixed(0) + ' m³' : l + ' L';
const fmtMXN = v => '$' + v.toLocaleString('es-MX');

function genHum(base, obj, n = 30) {
  let vals = [], h = base;
  for (let i = 0; i < n; i++) {
    h += (Math.random() - 0.48) * 3;
    if (h < obj - 18) h += 8;
    if (h > 96) h = 96;
    if (h < 4)  h = 4;
    vals.push(Math.round(h * 10) / 10);
  }
  return vals;
}

const LABELS_30 = Array.from({ length: 30 }, (_, i) => {
  const d = new Date(2025, 4, 16 + i);
  return `${d.getDate()}/${d.getMonth() + 1}`;
});
