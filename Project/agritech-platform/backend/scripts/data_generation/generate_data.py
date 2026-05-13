"""
generate_data.py
================
Generación de datos sintéticos estadísticamente coherentes para plataforma AgTech.
Región: Sinaloa (Dr-075), México — Ciclo otoño-invierno 2025-2026.
Cultivos: maíz, frijol, chile, papa, jitomate.

Lógica de simulación:
  - Temperatura alta → mayor evapotranspiración → humedad baja más rápido
  - Lluvia → sube humedad del suelo
  - Días sin riego → humedad decae según tipo de suelo
  - Suelo arcilloso retiene más agua que arenoso
  - Goteo < aspersión < gravedad en consumo de agua
  - Riego se activa cuando humedad < (objetivo - umbral_activacion)

Tablas generadas:
  1. cultivos.csv
  2. parcelas.csv
  3. sensores.csv
  4. lecturas_sensor.csv
  5. sensores_climaticos.csv
  6. historial_riego.csv
  7. costos.csv
  8. produccion.csv
  9. alertas.csv
"""

import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# ─── REPRODUCIBILIDAD ────────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ─── RUTAS ───────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── PARÁMETROS GENERALES ────────────────────────────────────────────────────────
START_DATE = datetime(2025, 10, 1)
END_DATE   = datetime(2026, 4, 30)
TOTAL_DAYS = (END_DATE - START_DATE).days + 1
NUM_PARCELAS = 10
READINGS_PER_DAY = 4   # 00:00, 06:00, 12:00, 18:00

print(f"[INFO] Generando {TOTAL_DAYS} días ({START_DATE.date()} → {END_DATE.date()})")
print(f"[INFO] Output: {OUTPUT_DIR}\n")

# ═══════════════════════════════════════════════════════════════════════════════════
# 1. CULTIVOS
# ═══════════════════════════════════════════════════════════════════════════════════

CULTIVOS_DEF = [
    {
        "id_cultivo": 1,
        "nombre_comun": "Maíz",
        "nombre_cientifico": "Zea mays",
        "kc_inicial": 0.30, "kc_medio": 1.20, "kc_final": 0.60,
        "ky_min": 0.20, "ky_max": 1.25, "ky_promedio": 0.72,
        "dias_etapa_inicial": 25, "dias_etapa_desarrollo": 35,
        "dias_etapa_media": 40, "dias_etapa_final": 30,
        "rendimiento_min": 4.0, "rendimiento_max": 12.0, "rendimiento_promedio": 8.0,
        # Parámetros internos para simulación
        "_humedad_minima": 35, "_humedad_optima": 65, "_decaimiento_base": 2.5,
    },
    {
        "id_cultivo": 2,
        "nombre_comun": "Frijol",
        "nombre_cientifico": "Phaseolus vulgaris",
        "kc_inicial": 0.40, "kc_medio": 1.15, "kc_final": 0.35,
        "ky_min": 0.20, "ky_max": 1.15, "ky_promedio": 0.67,
        "dias_etapa_inicial": 20, "dias_etapa_desarrollo": 30,
        "dias_etapa_media": 35, "dias_etapa_final": 20,
        "rendimiento_min": 0.8, "rendimiento_max": 2.5, "rendimiento_promedio": 1.6,
        "_humedad_minima": 40, "_humedad_optima": 60, "_decaimiento_base": 2.8,
    },
    {
        "id_cultivo": 3,
        "nombre_comun": "Chile",
        "nombre_cientifico": "Capsicum annuum",
        "kc_inicial": 0.35, "kc_medio": 1.05, "kc_final": 0.90,
        "ky_min": 0.60, "ky_max": 1.10, "ky_promedio": 0.85,
        "dias_etapa_inicial": 30, "dias_etapa_desarrollo": 40,
        "dias_etapa_media": 110, "dias_etapa_final": 20,
        "rendimiento_min": 8.0, "rendimiento_max": 25.0, "rendimiento_promedio": 16.0,
        "_humedad_minima": 45, "_humedad_optima": 70, "_decaimiento_base": 2.2,
    },
    {
        "id_cultivo": 4,
        "nombre_comun": "Papa",
        "nombre_cientifico": "Solanum tuberosum",
        "kc_inicial": 0.50, "kc_medio": 1.15, "kc_final": 0.75,
        "ky_min": 0.40, "ky_max": 1.10, "ky_promedio": 0.75,
        "dias_etapa_inicial": 25, "dias_etapa_desarrollo": 30,
        "dias_etapa_media": 45, "dias_etapa_final": 30,
        "rendimiento_min": 15.0, "rendimiento_max": 40.0, "rendimiento_promedio": 27.0,
        "_humedad_minima": 50, "_humedad_optima": 75, "_decaimiento_base": 3.0,
    },
    {
        "id_cultivo": 5,
        "nombre_comun": "Jitomate",
        "nombre_cientifico": "Solanum lycopersicum",
        "kc_inicial": 0.60, "kc_medio": 1.15, "kc_final": 0.80,
        "ky_min": 0.40, "ky_max": 1.05, "ky_promedio": 0.72,
        "dias_etapa_inicial": 30, "dias_etapa_desarrollo": 40,
        "dias_etapa_media": 45, "dias_etapa_final": 25,
        "rendimiento_min": 30.0, "rendimiento_max": 90.0, "rendimiento_promedio": 60.0,
        "_humedad_minima": 50, "_humedad_optima": 72, "_decaimiento_base": 2.0,
    },
]

# Columnas para el CSV (sin campos internos _)
CULTIVOS_COLS = [k for k in CULTIVOS_DEF[0].keys() if not k.startswith("_")]
df_cultivos = pd.DataFrame(CULTIVOS_DEF)[CULTIVOS_COLS]
df_cultivos.to_csv(os.path.join(OUTPUT_DIR, "cultivos.csv"), index=False)
print(f"[OK] cultivos.csv — {len(df_cultivos)} registros")

# Índice rápido cultivo_id → definición
cultivo_map = {c["id_cultivo"]: c for c in CULTIVOS_DEF}

# ═══════════════════════════════════════════════════════════════════════════════════
# 2. PARCELAS
# ═══════════════════════════════════════════════════════════════════════════════════

TIPOS_SUELO = {
    "arcilloso":  {"retencion": 0.90, "decaimiento_factor": 0.70},  # retiene mucho
    "franco":     {"retencion": 0.75, "decaimiento_factor": 0.90},
    "limoso":     {"retencion": 0.80, "decaimiento_factor": 0.80},
    "arenoso":    {"retencion": 0.50, "decaimiento_factor": 1.30},  # retiene poco
    "franco-arcilloso": {"retencion": 0.82, "decaimiento_factor": 0.75},
}

SISTEMAS_RIEGO = {
    "goteo":       {"eficiencia": 0.92, "litros_por_ha_por_evento": 600,  "costo_agua_m3": 4.5},
    "aspersion":   {"eficiencia": 0.78, "litros_por_ha_por_evento": 1100, "costo_agua_m3": 3.8},
    "gravedad":    {"eficiencia": 0.55, "litros_por_ha_por_evento": 2200, "costo_agua_m3": 2.5},
    "microaspersion": {"eficiencia": 0.85, "litros_por_ha_por_evento": 800, "costo_agua_m3": 4.0},
}

NOMBRES_PARCELAS = [
    "La Esperanza", "El Mezquite", "San Isidro", "Los Nogales",
    "El Vergel", "La Primavera", "Los Almendros", "Santa Rosa",
    "El Palomar", "La Huerta Norte",
]

# Asignación determinista con distribución realista de cultivos
CULTIVO_ASIGNACION = [1, 3, 5, 2, 4, 5, 3, 1, 2, 4]  # 2 maíz, 2 frijol, 2 chile, 2 papa, 2 jitomate

parcelas_data = []
for i in range(NUM_PARCELAS):
    cultivo_id = CULTIVO_ASIGNACION[i]
    cultivo = cultivo_map[cultivo_id]
    suelo = random.choice(list(TIPOS_SUELO.keys()))
    sistema = random.choice(list(SISTEMAS_RIEGO.keys()))
    area = round(random.uniform(2.0, 25.0), 2)
    humedad_obj = cultivo["_humedad_optima"]

    # Fecha siembra: escalonada en octubre-noviembre 2025
    dias_offset = random.randint(0, 45)
    fecha_siembra = START_DATE + timedelta(days=dias_offset)

    parcelas_data.append({
        "id_parcela": i + 1,
        "nombre_parcela": NOMBRES_PARCELAS[i],
        "area_ha": area,
        "cultivo_actual": cultivo_id,
        "tipo_suelo": suelo,
        "sistema_riego": sistema,
        "humedad_objetivo": humedad_obj,
        "estado_parcela": "activa",
        "color_estado": "#22c55e",
        "fecha_siembra": fecha_siembra.date(),
        # Internos para simulación
        "_suelo_retencion": TIPOS_SUELO[suelo]["retencion"],
        "_suelo_decaimiento": TIPOS_SUELO[suelo]["decaimiento_factor"],
        "_sistema_litros_ha": SISTEMAS_RIEGO[sistema]["litros_por_ha_por_evento"],
        "_sistema_eficiencia": SISTEMAS_RIEGO[sistema]["eficiencia"],
        "_costo_agua_m3": SISTEMAS_RIEGO[sistema]["costo_agua_m3"],
        "_humedad_minima": cultivo["_humedad_minima"],
        "_decaimiento_base": cultivo["_decaimiento_base"],
        "_humedad_actual": float(humedad_obj),  # estado inicial
        "_dias_sin_riego": 0,
    })

PARCELAS_COLS = [k for k in parcelas_data[0].keys() if not k.startswith("_")]
df_parcelas = pd.DataFrame(parcelas_data)[PARCELAS_COLS]
df_parcelas.to_csv(os.path.join(OUTPUT_DIR, "parcelas.csv"), index=False)
print(f"[OK] parcelas.csv — {len(df_parcelas)} registros")

# ═══════════════════════════════════════════════════════════════════════════════════
# 3. SENSORES
# ═══════════════════════════════════════════════════════════════════════════════════

MODELOS_SENSOR = {
    "humedad":          ["Sentek EnviroSCAN", "Decagon 5TM", "Campbell CS655"],
    "temperatura":      ["DS18B20 Pro", "Onset HOBO U23", "Vaisala HMT310"],
    "conductividad":    ["Meter Group TEROS 12", "Stevens HydraProbe", "Delta-T SM150"],
}

sensores_data = []
sensor_id = 1
for p in parcelas_data:
    pid = p["id_parcela"]
    n_sensores = random.randint(2, 4)
    tipos_asignados = random.sample(["humedad", "humedad", "temperatura", "conductividad"], n_sensores)

    for tipo in tipos_asignados:
        modelos = MODELOS_SENSOR[tipo]
        bateria = round(random.uniform(55, 100), 1)
        estado = "activo" if bateria > 20 else "bajo_bateria"
        fecha_inst = START_DATE - timedelta(days=random.randint(30, 180))

        sensores_data.append({
            "id_sensor": sensor_id,
            "parcela_id": pid,
            "tipo_sensor": tipo,
            "modelo_sensor": random.choice(modelos),
            "estado_sensor": estado,
            "bateria": bateria,
            "fecha_instalacion": fecha_inst.date(),
        })
        sensor_id += 1

df_sensores = pd.DataFrame(sensores_data)
df_sensores.to_csv(os.path.join(OUTPUT_DIR, "sensores.csv"), index=False)
print(f"[OK] sensores.csv — {len(df_sensores)} registros")

# ═══════════════════════════════════════════════════════════════════════════════════
# 4. SIMULACIÓN TEMPORAL (día a día)
# Genera: sensores_climaticos, lecturas_sensor, historial_riego, alertas
# ═══════════════════════════════════════════════════════════════════════════════════

print("\n[INFO] Simulando ciclo agrícola día a día...")

# Listas acumuladoras
rows_clima       = []
rows_lecturas    = []
rows_riego       = []
rows_alertas     = []

lectura_id  = 1
clima_id    = 1
riego_id    = 1
alerta_id   = 1

HORAS_LECTURA = [0, 6, 12, 18]  # UTC-7 implícito

for dia_idx in range(TOTAL_DAYS):
    fecha_actual = START_DATE + timedelta(days=dia_idx)
    mes = fecha_actual.month

    # ── Clima regional (base Sinaloa) ────────────────────────────────────────────
    # Ciclo otoño-invierno: oct-feb frío/templado, mar-abr se calienta
    temp_base_mes = {10: 26, 11: 22, 12: 19, 1: 18, 2: 20, 3: 25, 4: 30}
    temp_base = temp_base_mes.get(mes, 24)
    temp_std  = 4.0

    # Precipitación: oct-nov algo, resto casi nada (ciclo seco)
    prob_lluvia = {10: 0.15, 11: 0.08, 12: 0.04, 1: 0.03, 2: 0.03, 3: 0.02, 4: 0.02}
    llueve_hoy = random.random() < prob_lluvia.get(mes, 0.03)
    precip_mm  = round(np.random.exponential(8.0), 1) if llueve_hoy else 0.0

    humedad_rel_base = 55 + (precip_mm * 1.5)  # lluvia sube humedad relativa
    humedad_rel_base = min(humedad_rel_base, 95)

    radiacion_base = {10: 18, 11: 16, 12: 14, 1: 15, 2: 17, 3: 20, 4: 22}
    radiacion = round(np.random.normal(radiacion_base.get(mes, 17), 2.5), 1)
    radiacion = max(8.0, radiacion)

    viento = round(np.random.gamma(shape=2.0, scale=2.5), 1)  # km/h

    # Temperatura ambiente (varía por parcela levemente)
    temp_ambiente_base = round(np.random.normal(temp_base, temp_std), 1)

    # ── Por parcela ──────────────────────────────────────────────────────────────
    for p in parcelas_data:
        pid = p["id_parcela"]

        # Temperatura con micro-variación geográfica por parcela
        temp_parcela = round(temp_ambiente_base + np.random.normal(0, 0.8), 1)
        hum_rel_parc = round(humedad_rel_base + np.random.normal(0, 3), 1)
        hum_rel_parc = min(max(hum_rel_parc, 20), 98)

        # ── Clima por parcela ────────────────────────────────────────────────────
        rows_clima.append({
            "id_clima": clima_id,
            "parcela_id": pid,
            "temperatura_ambiente": temp_parcela,
            "humedad_relativa": hum_rel_parc,
            "precipitacion_mm": precip_mm,
            "radiacion_solar": radiacion,
            "velocidad_viento": viento,
            "timestamp": fecha_actual.strftime("%Y-%m-%d 08:00:00"),
        })
        clima_id += 1

        # ── Actualizar humedad del suelo ─────────────────────────────────────────
        h = p["_humedad_actual"]
        decaimiento_base = p["_decaimiento_base"]
        factor_suelo = p["_suelo_decaimiento"]

        # Evapotranspiración: mayor temperatura → mayor pérdida
        et_factor = 1.0 + max(0, (temp_parcela - 25) * 0.04)
        decaimiento_diario = decaimiento_base * factor_suelo * et_factor
        decaimiento_diario += np.random.normal(0, 0.3)  # ruido

        # Lluvia: sube humedad según retención del suelo
        ganancia_lluvia = precip_mm * 0.4 * p["_suelo_retencion"]

        h_nueva = h - decaimiento_diario + ganancia_lluvia
        h_nueva = min(max(h_nueva, 10.0), 95.0)

        # ── Decisión de riego ────────────────────────────────────────────────────
        umbral_riego = p["_humedad_minima"] + 5  # activa riego antes del mínimo
        riego_hoy = False

        if h_nueva < umbral_riego and not llueve_hoy:
            riego_hoy = True
            litros_total = p["_sistema_litros_ha"] * p["area_ha"]
            litros_total *= (1 + np.random.normal(0, 0.05))  # ±5% variación
            litros_total = max(litros_total, 100)

            duracion = round(litros_total / (p["_sistema_litros_ha"] / 60), 0)  # min
            duracion = max(20, duracion)

            costo_agua = round((litros_total / 1000) * p["_costo_agua_m3"], 2)
            costo_energia = round(costo_agua * 0.35, 2)  # ~35% del costo agua

            # Ganancia de humedad por riego
            ganancia_riego = (litros_total / 1000) * (p["_sistema_eficiencia"] * 3.5) / p["area_ha"]
            h_nueva = min(h_nueva + ganancia_riego, 92.0)

            rows_riego.append({
                "id_riego": riego_id,
                "parcela_id": pid,
                "fecha_riego": fecha_actual.date(),
                "cantidad_agua_litros": round(litros_total, 0),
                "duracion_min": int(duracion),
                "metodo_riego": p["sistema_riego"],
                "costo_agua": costo_agua,
                "costo_energia": costo_energia,
            })
            riego_id += 1
            p["_dias_sin_riego"] = 0
        else:
            p["_dias_sin_riego"] += 1

        p["_humedad_actual"] = round(h_nueva, 2)

        # ── Lecturas del sensor (4 por día por parcela) ──────────────────────────
        sensores_parcela = [s for s in sensores_data if s["parcela_id"] == pid]
        if not sensores_parcela:
            continue

        sensores_humedad = [s for s in sensores_parcela if s["tipo_sensor"] == "humedad"]
        sensores_temp    = [s for s in sensores_parcela if s["tipo_sensor"] == "temperatura"]
        sensores_cond    = [s for s in sensores_parcela if s["tipo_sensor"] == "conductividad"]

        for hora in HORAS_LECTURA:
            ts = fecha_actual.strftime(f"%Y-%m-%d {hora:02d}:00:00")

            # Variación intradiaria de humedad: baja al mediodía por calor
            variacion_hora = {0: 0, 6: -1.5, 12: -3.5, 18: -1.0}
            h_hora = h_nueva + variacion_hora.get(hora, 0) + np.random.normal(0, 0.8)
            h_hora = round(min(max(h_hora, 10), 95), 2)

            # Temperatura del suelo (más estable que ambiente)
            t_suelo_base = temp_parcela * 0.85 + 3
            t_hora_factor = {0: -2.0, 6: -1.0, 12: 2.5, 18: 1.0}
            t_suelo = round(t_suelo_base + t_hora_factor.get(hora, 0) + np.random.normal(0, 0.5), 1)

            # Conductividad eléctrica (correlación positiva con humedad y fertilidad)
            ce_base = 0.8 + (h_hora / 100) * 0.6
            ce = round(ce_base + np.random.normal(0, 0.05), 3)
            ce = max(0.1, ce)

            # Usar primer sensor de cada tipo
            sid_hum  = sensores_humedad[0]["id_sensor"]  if sensores_humedad else None
            sid_temp = sensores_temp[0]["id_sensor"]     if sensores_temp    else None
            sid_cond = sensores_cond[0]["id_sensor"]     if sensores_cond    else None

            # Un solo registro por timestamp agrupa las 3 mediciones del sensor principal
            sensor_principal = sensores_parcela[0]["id_sensor"]
            rows_lecturas.append({
                "id_lectura": lectura_id,
                "sensor_id": sensor_principal,
                "humedad_suelo": h_hora,
                "temperatura_suelo": t_suelo,
                "conductividad_electrica": ce,
                "timestamp": ts,
            })
            lectura_id += 1

        # ── Alertas ──────────────────────────────────────────────────────────────
        cultivo_info = cultivo_map[p["cultivo_actual"]]
        hum_critica  = cultivo_info["_humedad_minima"]

        if h_nueva < hum_critica:
            rows_alertas.append({
                "id_alerta": alerta_id,
                "parcela_id": pid,
                "tipo_alerta": "estres_hidrico",
                "mensaje": f"Humedad crítica {h_nueva:.1f}% — mínima tolerada {hum_critica}%",
                "prioridad": "alta",
                "fecha_alerta": fecha_actual.strftime("%Y-%m-%d %H:%M:%S"),
                "atendida": False,
            })
            alerta_id += 1

        elif h_nueva > 88:
            rows_alertas.append({
                "id_alerta": alerta_id,
                "parcela_id": pid,
                "tipo_alerta": "exceso_humedad",
                "mensaje": f"Humedad excesiva {h_nueva:.1f}% — riesgo de anegamiento",
                "prioridad": "media",
                "fecha_alerta": fecha_actual.strftime("%Y-%m-%d %H:%M:%S"),
                "atendida": False,
            })
            alerta_id += 1

        elif p["_dias_sin_riego"] > 7 and h_nueva < (p["humedad_objetivo"] - 15):
            rows_alertas.append({
                "id_alerta": alerta_id,
                "parcela_id": pid,
                "tipo_alerta": "deficit_riego",
                "mensaje": f"{p['_dias_sin_riego']} días sin riego — déficit hídrico acumulado",
                "prioridad": "media",
                "fecha_alerta": fecha_actual.strftime("%Y-%m-%d %H:%M:%S"),
                "atendida": random.choice([True, False]),
            })
            alerta_id += 1

    # Progreso cada 30 días
    if (dia_idx + 1) % 30 == 0:
        print(f"  → {fecha_actual.date()} ({dia_idx + 1}/{TOTAL_DAYS} días)")

print(f"  → {END_DATE.date()} ({TOTAL_DAYS}/{TOTAL_DAYS} días) ✓\n")

# ── Guardar tablas de la simulación ─────────────────────────────────────────────
df_clima = pd.DataFrame(rows_clima)
df_clima.to_csv(os.path.join(OUTPUT_DIR, "sensores_climaticos.csv"), index=False)
print(f"[OK] sensores_climaticos.csv — {len(df_clima):,} registros")

df_lecturas = pd.DataFrame(rows_lecturas)
df_lecturas.to_csv(os.path.join(OUTPUT_DIR, "lecturas_sensor.csv"), index=False)
print(f"[OK] lecturas_sensor.csv — {len(df_lecturas):,} registros")

df_riego = pd.DataFrame(rows_riego)
df_riego.to_csv(os.path.join(OUTPUT_DIR, "historial_riego.csv"), index=False)
print(f"[OK] historial_riego.csv — {len(df_riego):,} registros")

df_alertas = pd.DataFrame(rows_alertas)
df_alertas.to_csv(os.path.join(OUTPUT_DIR, "alertas.csv"), index=False)
print(f"[OK] alertas.csv — {len(df_alertas):,} registros")

# ═══════════════════════════════════════════════════════════════════════════════════
# 5. COSTOS
# ═══════════════════════════════════════════════════════════════════════════════════

TIPO_COSTOS = [
    ("fertilizante",  lambda area: round(np.random.normal(2800, 400) * area, 2)),
    ("mantenimiento", lambda area: round(np.random.normal(600,  150) * area, 2)),
    ("mano_de_obra",  lambda area: round(np.random.normal(1500, 300) * area, 2)),
    ("pesticida",     lambda area: round(np.random.normal(900,  200) * area, 2)),
    ("semilla",       lambda area: round(np.random.normal(500,  100) * area, 2)),
    ("energia",       lambda area: round(np.random.normal(800,  150) * area, 2)),
]

rows_costos = []
costo_id = 1

for p in parcelas_data:
    pid = p["id_parcela"]
    area = p["area_ha"]

    # Costos de riego (mensual agregado desde historial)
    riegos_parcela = [r for r in rows_riego if r["parcela_id"] == pid]
    costos_agua_por_mes = {}
    for r in riegos_parcela:
        mes_key = str(r["fecha_riego"])[:7]  # YYYY-MM
        costos_agua_por_mes[mes_key] = costos_agua_por_mes.get(mes_key, 0) + r["costo_agua"]

    for mes_key, monto in costos_agua_por_mes.items():
        fecha_c = datetime.strptime(mes_key + "-15", "%Y-%m-%d")
        rows_costos.append({
            "id_costo": costo_id,
            "parcela_id": pid,
            "tipo_costo": "agua_riego",
            "descripcion": f"Costo agua riego {mes_key}",
            "monto": round(monto, 2),
            "fecha": fecha_c.date(),
        })
        costo_id += 1

    # Otros costos: 1-2 eventos por tipo durante el ciclo
    for tipo, fn_monto in TIPO_COSTOS:
        n_eventos = random.randint(1, 2)
        for _ in range(n_eventos):
            dias_rand = random.randint(0, TOTAL_DAYS - 1)
            fecha_c = START_DATE + timedelta(days=dias_rand)
            rows_costos.append({
                "id_costo": costo_id,
                "parcela_id": pid,
                "tipo_costo": tipo,
                "descripcion": f"{tipo.capitalize()} — ciclo 2025-26",
                "monto": fn_monto(area),
                "fecha": fecha_c.date(),
            })
            costo_id += 1

df_costos = pd.DataFrame(rows_costos).sort_values("fecha").reset_index(drop=True)
df_costos.to_csv(os.path.join(OUTPUT_DIR, "costos.csv"), index=False)
print(f"[OK] costos.csv — {len(df_costos):,} registros")

# ═══════════════════════════════════════════════════════════════════════════════════
# 6. PRODUCCIÓN
# ═══════════════════════════════════════════════════════════════════════════════════

CALIDADES = ["premium", "primera", "segunda", "tercera"]

rows_produccion = []
prod_id = 1

for p in parcelas_data:
    pid = p["id_parcela"]
    cultivo_id = p["cultivo_actual"]
    cultivo_info = cultivo_map[cultivo_id]
    area = p["area_ha"]

    # Humedad promedio del ciclo influye en rendimiento
    lecturas_p = df_lecturas[df_lecturas["sensor_id"].isin(
        [s["id_sensor"] for s in sensores_data if s["parcela_id"] == pid]
    )]["humedad_suelo"]
    hum_promedio = lecturas_p.mean() if len(lecturas_p) > 0 else cultivo_info["_humedad_optima"]

    # Factor de rendimiento: cuánto se acercó la humedad al óptimo
    diferencia = abs(hum_promedio - cultivo_info["_humedad_optima"])
    factor_hum = max(0.6, 1.0 - (diferencia / cultivo_info["_humedad_optima"]) * 0.8)
    factor_ruido = np.random.normal(1.0, 0.08)

    rendimiento_est = round(cultivo_info["rendimiento_promedio"] * factor_hum * area, 2)
    rendimiento_real = round(rendimiento_est * factor_ruido, 2)
    rendimiento_real = max(rendimiento_real, cultivo_info["rendimiento_min"] * area * 0.5)

    # Precio de venta estimado por cultivo (MXN/ton)
    precio_ton = {1: 4500, 2: 12000, 3: 8000, 4: 5500, 5: 6000}
    precio = precio_ton.get(cultivo_id, 5000)
    ingreso_est  = round(rendimiento_est  * precio, 2)
    ingreso_real = round(rendimiento_real * precio * np.random.normal(1.0, 0.05), 2)

    # Calidad correlacionada con rendimiento vs promedio
    if rendimiento_real >= cultivo_info["rendimiento_promedio"] * area * 0.9:
        calidad = random.choices(CALIDADES, weights=[40, 40, 15, 5])[0]
    elif rendimiento_real >= cultivo_info["rendimiento_promedio"] * area * 0.7:
        calidad = random.choices(CALIDADES, weights=[10, 40, 35, 15])[0]
    else:
        calidad = random.choices(CALIDADES, weights=[5, 20, 40, 35])[0]

    # Fecha cosecha: fin del ciclo de la etapa final del cultivo
    dias_ciclo = (cultivo_info["dias_etapa_inicial"] + cultivo_info["dias_etapa_desarrollo"]
                  + cultivo_info["dias_etapa_media"] + cultivo_info["dias_etapa_final"])
    fecha_siembra_dt = datetime.strptime(str(p["fecha_siembra"]), "%Y-%m-%d")
    fecha_cosecha = fecha_siembra_dt + timedelta(days=dias_ciclo)

    rows_produccion.append({
        "id_produccion": prod_id,
        "parcela_id": pid,
        "cultivo_id": cultivo_id,
        "fecha_cosecha": fecha_cosecha.date(),
        "rendimiento_real_ton": rendimiento_real,
        "ingreso_estimado": ingreso_est,
        "ingreso_real": ingreso_real,
        "calidad_cosecha": calidad,
    })
    prod_id += 1

df_produccion = pd.DataFrame(rows_produccion)
df_produccion.to_csv(os.path.join(OUTPUT_DIR, "produccion.csv"), index=False)
print(f"[OK] produccion.csv — {len(df_produccion):,} registros")

# ═══════════════════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ═══════════════════════════════════════════════════════════════════════════════════

tablas = {
    "cultivos": df_cultivos,
    "parcelas": df_parcelas,
    "sensores": df_sensores,
    "sensores_climaticos": df_clima,
    "lecturas_sensor": df_lecturas,
    "historial_riego": df_riego,
    "costos": df_costos,
    "produccion": df_produccion,
    "alertas": df_alertas,
}

print("\n" + "═" * 55)
print("  RESUMEN DE DATOS GENERADOS")
print("═" * 55)
total = 0
for nombre, df in tablas.items():
    print(f"  {nombre:<25} {len(df):>8,} registros")
    total += len(df)
print("─" * 55)
print(f"  {'TOTAL':<25} {total:>8,} registros")
print("═" * 55)

# Stats humedad
print("\n  ESTADÍSTICAS DE HUMEDAD DEL SUELO:")
print(f"  Media:  {df_lecturas['humedad_suelo'].mean():.1f}%")
print(f"  Std:    {df_lecturas['humedad_suelo'].std():.1f}%")
print(f"  Min:    {df_lecturas['humedad_suelo'].min():.1f}%")
print(f"  Max:    {df_lecturas['humedad_suelo'].max():.1f}%")

print("\n  RIEGOS POR SISTEMA:")
print(df_riego.groupby("metodo_riego").agg(
    eventos=("id_riego", "count"),
    agua_total_m3=("cantidad_agua_litros", lambda x: round(x.sum() / 1000, 0))
).to_string())

print(f"\n[✓] Todos los CSVs guardados en: {OUTPUT_DIR}\n")
