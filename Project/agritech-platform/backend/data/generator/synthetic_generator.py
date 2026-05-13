"""
Generador de datos sintéticos para AgriTech Platform.
Produce datos agronómicamente coherentes para Sinaloa, México.

Salida:
    data/output/
        clima.json            → lecturas climáticas diarias por parcela
        parcelas.json         → metadata de parcelas
        sensores.json         → metadata de sensores IoT
        lecturas_sensor.json  → lecturas de humedad/temp/CE cada 6h
        riegos.json           → historial de riegos automáticos
        alertas.json          → alertas generadas
        resumen_parcelas.json → KPIs agregados para dashboard
        agritech.db           → SQLite con todas las tablas

Uso:
    python synthetic_generator.py
"""

import json
import math
import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from config import (
    CLIMA_SINALOA_MENSUAL,
    CULTIVOS,
    PARCELAS_CONFIG,
    SIM_CONFIG,
    SISTEMAS_RIEGO,
    TIPOS_SUELO,
)
from penman_monteith import calcular_et0, calcular_etc, calcular_kc_etapa

# ─── Reproducibilidad ───────────────────────────────────────────────────────
random.seed(SIM_CONFIG["seed_random"])

# ─── Rutas de salida ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
DB_PATH = BASE_DIR / "db" / "agritech.db"
DB_PATH.parent.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════
# 1. GENERADOR CLIMÁTICO
# ═══════════════════════════════════════════════════════════════════════════

def generar_clima_diario(año: int, dias: int) -> list[dict]:
    """
    Genera serie climática diaria con variabilidad realista sobre
    promedios mensuales de Sinaloa (Culiacán).
    """
    clima = CLIMA_SINALOA_MENSUAL
    fecha_inicio = date(año, 1, 1)
    registros = []

    for d in range(dias):
        fecha = fecha_inicio + timedelta(days=d)
        mes_idx = fecha.month - 1  # 0-indexed

        # Temperatura con ruido gaussiano
        t_max_base = clima["temp_max_c"][mes_idx]
        t_min_base = clima["temp_min_c"][mes_idx]
        t_max = round(t_max_base + random.gauss(0, SIM_CONFIG["ruido_temp_std"]), 1)
        t_min = round(t_min_base + random.gauss(0, SIM_CONFIG["ruido_temp_std"] * 0.6), 1)
        # Garantizar t_max > t_min
        if t_max <= t_min:
            t_max = t_min + 4.0

        # Humedad relativa
        hr_base = clima["humedad_rel_pct"][mes_idx]
        hr = round(max(20, min(98, hr_base + random.gauss(0, SIM_CONFIG["ruido_hr_std"]))), 1)

        # Precipitación (modelo probabilístico por mes)
        precip_mensual = clima["precip_mm"][mes_idx]
        # Probabilidad diaria de lluvia proporcional a precipitación mensual
        prob_lluvia = min(0.8, precip_mensual / 180.0)
        if random.random() < prob_lluvia:
            # Distribución exponencial con media = precip_mensual / días_lluvia_esperados
            dias_lluvia_esperados = max(1, int(prob_lluvia * 30))
            precip = round(
                random.expovariate(1 / (precip_mensual / dias_lluvia_esperados)), 1
            )
            precip = min(precip, 80.0)   # tope realista Sinaloa
        else:
            precip = 0.0

        # Radiación solar (con nubosidad afectando)
        rs_base = clima["radiacion_mj_m2"][mes_idx]
        factor_nubosidad = 1.0 - (0.4 * (precip / 30.0) if precip > 0 else 0)
        rs = round(
            max(5.0, rs_base * factor_nubosidad + random.gauss(0, 1.5)), 2
        )

        # Viento
        viento_base = clima["viento_m_s"][mes_idx]
        viento = round(max(0.5, viento_base + random.gauss(0, SIM_CONFIG["ruido_viento_std"])), 2)

        # ET₀ usando Penman-Monteith
        dia_del_año = fecha.timetuple().tm_yday
        et0_result = calcular_et0(
            temp_max_c=t_max,
            temp_min_c=t_min,
            humedad_rel_pct=hr,
            radiacion_mj_m2=rs,
            viento_m_s=viento,
            elevacion_msnm=clima["elevacion_msnm"],
            dia_del_año=dia_del_año,
        )

        registros.append({
            "fecha": fecha.isoformat(),
            "dia_del_año": dia_del_año,
            "mes": fecha.month,
            "temp_max_c": t_max,
            "temp_min_c": t_min,
            "temp_media_c": et0_result["temp_media_c"],
            "humedad_relativa_pct": hr,
            "precipitacion_mm": precip,
            "radiacion_solar_mj_m2": rs,
            "velocidad_viento_m_s": viento,
            "et0_mm_dia": et0_result["et0_mm_dia"],
            "vpd_kpa": et0_result["vpd_kpa"],
            "Rn_mj_m2": et0_result["Rn_mj_m2"],
        })

    return registros


# ═══════════════════════════════════════════════════════════════════════════
# 2. GENERADOR DE PARCELAS, SENSORES Y BALANCE HÍDRICO
# ═══════════════════════════════════════════════════════════════════════════

def calcular_dia_ciclo(fecha: date, fecha_siembra: date) -> int:
    """Días transcurridos desde la siembra (0-indexed)."""
    delta = (fecha - fecha_siembra).days
    return max(0, delta)


def simular_parcela(
    parcela_cfg: dict,
    clima_diario: list[dict],
    año: int,
) -> dict:
    """
    Simula el balance hídrico completo de una parcela durante un año.

    Balance: θ(t+1) = θ(t) - ETc/profundidad_raiz + precipitacion_efectiva + riego
    θ expresado como % de saturación (0-100) para el dashboard.
    """
    cultivo_key = parcela_cfg["cultivo"]
    cultivo = CULTIVOS[cultivo_key]
    suelo = TIPOS_SUELO[parcela_cfg["tipo_suelo"]]
    sistema = SISTEMAS_RIEGO[parcela_cfg["sistema_riego"]]

    # Fecha de siembra (año anterior para cultivo O-I que cruza año nuevo)
    mes_siembra = parcela_cfg["fecha_siembra_mes"]
    if mes_siembra >= 10:
        fecha_siembra = date(año - 1, mes_siembra, 1)
    else:
        fecha_siembra = date(año, mes_siembra, 1)

    # Humedad inicial = capacidad de campo
    CC = suelo["capacidad_campo_pct"]          # Capacidad de Campo [%]
    PMP = suelo["punto_marchitez_pct"]          # Punto Marchitez Permanente [%]
    rango_util = CC - PMP                       # Agua útil total [%]
    prof_raiz = cultivo["profundidad_raiz_m"]

    humedad_actual = CC * 0.85   # inicia al 85% de capacidad de campo
    umbral_riego = CC * SIM_CONFIG["umbral_riego_deficit_pct"]

    lecturas_diarias = []
    riegos = []
    alertas_raw = []
    balance_acum_7d = []

    for registro_clima in clima_diario:
        fecha = date.fromisoformat(registro_clima["fecha"])
        dia_ciclo = calcular_dia_ciclo(fecha, fecha_siembra)

        # Kc según etapa fenológica
        kc, etapa = calcular_kc_etapa(
            dia_ciclo,
            cultivo["etapas_dias"],
            cultivo["kc"],
        )

        # ETc [mm/día]
        et0 = registro_clima["et0_mm_dia"]
        etc_mm = calcular_etc(et0, kc)

        # Precipitación efectiva (70-85% de la total, pérdidas escorrentía/evaporación)
        precip_efectiva = registro_clima["precipitacion_mm"] * random.uniform(0.70, 0.85)

        # Convertir ETc de mm a cambio en humedad volumétrica [%]
        # Δθ(%) = ETc_mm / (prof_raiz_m × 10)
        # Derivación: Δθ(m³/m³) = ETc_mm/1000 / prof_raiz_m  → ×100 para %
        #             = ETc_mm / (prof_raiz_m × 10)
        etc_pct = etc_mm / (prof_raiz * 10)
        precip_pct = precip_efectiva / (prof_raiz * 10)

        # Reducción por ETc
        humedad_actual -= etc_pct

        # Aumento por precipitación (no supera capacidad de campo)
        humedad_actual = min(CC, humedad_actual + precip_pct)

        # ─── Riego automático ────────────────────────────────────────────
        agua_litros = 0.0
        riego_evento = None

        if humedad_actual < umbral_riego and etapa != "cosecha":
            # Regar hasta reponer al 90% de capacidad de campo
            deficit_pct = (CC * 0.90) - humedad_actual
            # agua_reponer_mm: lámina de agua a reponer [mm]
            # deficit_pct [%] × prof_raiz [m] × 10 = mm (conversión: Δθ% × Z_m × 10)
            agua_reponer_mm = deficit_pct * prof_raiz * 10 / sistema["eficiencia"]
            # litros = mm × m²  (1mm en 1m² = 1 litro)
            area_m2 = parcela_cfg["area_ha"] * 10000
            agua_litros = agua_reponer_mm * area_m2
            duracion_min = int(agua_litros / (sistema["caudal_lh_ha"] * parcela_cfg["area_ha"]))
            costo_agua = (agua_litros / 1000) * sistema["costo_m3"]  # m³ × MXN/m³
            costo_energia = costo_agua * 0.35   # ~35% del costo de agua en energía

            riego_evento = {
                "parcela_id": parcela_cfg["id"],
                "fecha_riego": fecha.isoformat(),
                "cantidad_agua_litros": round(agua_litros, 1),
                "duracion_min": max(30, duracion_min),
                "metodo_riego": parcela_cfg["sistema_riego"],
                "costo_agua_mxn": round(costo_agua, 2),
                "costo_energia_mxn": round(costo_energia, 2),
                "motivo": "deficit_hidrico_automatico",
                "humedad_antes": round(humedad_actual, 2),
                "etc_dia_mm": etc_mm,
            }
            riegos.append(riego_evento)

            # Aplicar riego
            humedad_actual = min(CC, humedad_actual + deficit_pct * sistema["eficiencia"])

        # ─── Límites físicos ─────────────────────────────────────────────
        humedad_actual = max(PMP - 2, min(CC + 3, humedad_actual))  # permite leve sobre-riego/estrés

        # ─── Índice de estrés hídrico (CWSI simplificado) ────────────────
        # 0 = sin estrés, 1 = estrés máximo
        cwsi = max(0.0, min(1.0, (umbral_riego - humedad_actual) / rango_util))

        # ─── WUE (Water Use Efficiency) kg/m³  ──────────────────────────
        # Aproximación diaria; el real se calcula a cosecha
        rendimiento_diario_kg = (
            cultivo["rendimiento_ton_ha"]["promedio"] * 1000 * parcela_cfg["area_ha"]
            / cultivo["etapas_dias"]["media"]  # distribuido sobre etapa media
        ) if etapa == "media" else 0
        wue = round(rendimiento_diario_kg / max(1, agua_litros / 1000), 2) if agua_litros > 0 else 0

        # ─── Registro diario ─────────────────────────────────────────────
        deficit_hidrico = max(0, cultivo["humedad_optima_pct"] - humedad_actual)
        humedad_pct_dashboard = round(
            (humedad_actual - PMP) / rango_util * 100, 1
        )   # normalizado 0-100% para UI

        dias_ultimo_riego = 0
        if riegos:
            ult = date.fromisoformat(riegos[-1]["fecha_riego"])
            dias_ultimo_riego = (fecha - ult).days

        balance_acum_7d.append(precip_efectiva - etc_mm)
        if len(balance_acum_7d) > 7:
            balance_acum_7d.pop(0)

        lectura = {
            "parcela_id": parcela_cfg["id"],
            "fecha": fecha.isoformat(),
            "dia_ciclo": dia_ciclo,
            "etapa_fenologica": etapa,
            "kc": kc,
            "humedad_suelo_pct": round(humedad_actual, 2),         # % volumétrico real
            "humedad_dashboard_pct": max(0, min(100, humedad_pct_dashboard)),
            "temp_max_c": registro_clima["temp_max_c"],
            "temp_min_c": registro_clima["temp_min_c"],
            "temp_media_c": registro_clima["temp_media_c"],
            "et0_mm_dia": et0,
            "etc_mm_dia": etc_mm,
            "kc_etapa": kc,
            "precipitacion_mm": registro_clima["precipitacion_mm"],
            "precipitacion_efectiva_mm": round(precip_efectiva, 2),
            "riego_litros": round(agua_litros, 1),
            "cwsi": round(cwsi, 3),
            "deficit_hidrico_mm": round(deficit_hidrico, 2),
            "dias_desde_riego": dias_ultimo_riego,
            "balance_hidrico_7d_mm": round(sum(balance_acum_7d), 2),
            "vpd_kpa": registro_clima["vpd_kpa"],
            "humedad_relativa_pct": registro_clima["humedad_relativa_pct"],
            "radiacion_solar_mj_m2": registro_clima["radiacion_solar_mj_m2"],
        }
        lecturas_diarias.append(lectura)

        # ─── Alertas automáticas ─────────────────────────────────────────
        if cwsi > 0.6:
            alertas_raw.append({
                "parcela_id": parcela_cfg["id"],
                "tipo_alerta": "estres_hidrico_critico",
                "mensaje": f"CWSI={cwsi:.2f} — Estrés hídrico crítico en {parcela_cfg['nombre']}. Humedad: {humedad_actual:.1f}%",
                "prioridad": "alta",
                "fecha_alerta": fecha.isoformat(),
                "atendida": False,
            })
        elif cwsi > 0.35:
            alertas_raw.append({
                "parcela_id": parcela_cfg["id"],
                "tipo_alerta": "humedad_baja",
                "mensaje": f"Humedad por debajo del umbral en {parcela_cfg['nombre']}. Monitorear.",
                "prioridad": "media",
                "fecha_alerta": fecha.isoformat(),
                "atendida": random.random() > 0.3,
            })

        if registro_clima["precipitacion_mm"] > 40:
            alertas_raw.append({
                "parcela_id": parcela_cfg["id"],
                "tipo_alerta": "lluvia_intensa",
                "mensaje": f"Precipitación intensa: {registro_clima['precipitacion_mm']} mm. Revisar drenaje.",
                "prioridad": "media",
                "fecha_alerta": fecha.isoformat(),
                "atendida": random.random() > 0.5,
            })

    return {
        "lecturas_diarias": lecturas_diarias,
        "riegos": riegos,
        "alertas": alertas_raw,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 3. GENERADOR DE LECTURAS DE SENSOR (cada 6h)
# ═══════════════════════════════════════════════════════════════════════════

def generar_lecturas_sensor(
    parcela_id: str,
    sensores: list[dict],
    lecturas_diarias: list[dict],
) -> list[dict]:
    """
    Genera lecturas de sensores IoT (4 por día) interpolando
    sobre las lecturas diarias del balance hídrico.
    """
    lecturas_sensor = []
    horas = [0, 6, 12, 18]

    for lectura in lecturas_diarias:
        fecha = lectura["fecha"]
        for hora in horas:
            ts = f"{fecha}T{hora:02d}:00:00"

            # Variación intradía de humedad (suelo más seco a mediodía)
            factor_hora = {0: 1.02, 6: 1.01, 12: 0.97, 18: 0.99}[hora]
            # Temperatura del suelo sigue a la del aire con lag
            temp_suelo_offset = {0: -2, 6: -3, 12: 2, 18: 1}[hora]

            for sensor in sensores:
                if sensor["parcela_id"] != parcela_id:
                    continue

                # Ruido realista entre sensores (variabilidad espacial)
                ruido_humedad = random.gauss(0, 1.2)
                ruido_temp = random.gauss(0, 0.5)
                ruido_ce = random.gauss(0, 0.05)

                humedad = round(
                    lectura["humedad_suelo_pct"] * factor_hora + ruido_humedad, 2
                )
                temp_suelo = round(
                    lectura["temp_media_c"] + temp_suelo_offset + ruido_temp, 2
                )
                # CE: aumenta con menor humedad (mayor concentración de sales)
                ce_base = 0.8 + (40 - min(40, humedad)) * 0.02
                ce = round(max(0.2, ce_base + ruido_ce), 3)

                lecturas_sensor.append({
                    "sensor_id": sensor["id"],
                    "parcela_id": parcela_id,
                    "timestamp": ts,
                    "humedad_suelo_pct": max(5, humedad),
                    "temperatura_suelo_c": temp_suelo,
                    "conductividad_electrica_ds_m": ce,
                    "bateria_pct": sensor["bateria_inicial"] - random.uniform(0, 0.02),
                })

    return lecturas_sensor


# ═══════════════════════════════════════════════════════════════════════════
# 4. GENERADOR DE METADATA DE PARCELAS Y SENSORES
# ═══════════════════════════════════════════════════════════════════════════

def generar_metadata_parcelas(año: int) -> list[dict]:
    parcelas_out = []
    for cfg in PARCELAS_CONFIG:
        cultivo = CULTIVOS[cfg["cultivo"]]
        suelo = TIPOS_SUELO[cfg["tipo_suelo"]]
        mes_siembra = cfg["fecha_siembra_mes"]
        fecha_siembra = date(año - 1 if mes_siembra >= 10 else año, mes_siembra, 1)
        total_dias = sum(cultivo["etapas_dias"].values())
        fecha_cosecha_estimada = fecha_siembra + timedelta(days=total_dias)

        parcelas_out.append({
            "id_parcela": cfg["id"],
            "nombre_parcela": cfg["nombre"],
            "area_ha": cfg["area_ha"],
            "cultivo_actual": cfg["cultivo"],
            "nombre_cultivo": cultivo["nombre_comun"],
            "tipo_suelo": cfg["tipo_suelo"],
            "descripcion_suelo": suelo["descripcion"],
            "sistema_riego": cfg["sistema_riego"],
            "humedad_objetivo_pct": cultivo["humedad_optima_pct"],
            "humedad_estres_pct": cultivo["humedad_estres_pct"],
            "estado_parcela": "activa",
            "color_cultivo": cultivo["color_dashboard"],
            "fecha_siembra": fecha_siembra.isoformat(),
            "fecha_cosecha_estimada": fecha_cosecha_estimada.isoformat(),
            "capacidad_campo_pct": suelo["capacidad_campo_pct"],
            "punto_marchitez_pct": suelo["punto_marchitez_pct"],
            "rendimiento_esperado_ton": round(
                cultivo["rendimiento_ton_ha"]["promedio"] * cfg["area_ha"], 1
            ),
        })
    return parcelas_out


def generar_metadata_sensores(año: int) -> list[dict]:
    sensores = []
    modelos = ["Sentek Drill & Drop", "Decagon 5TM", "Stevens HydraProbe", "Delta-T PR2"]
    sensor_id_counter = 1

    for cfg in PARCELAS_CONFIG:
        for i in range(cfg["sensores_count"]):
            bateria = round(random.uniform(72, 98), 1)
            sensores.append({
                "id": f"S{sensor_id_counter:03d}",
                "parcela_id": cfg["id"],
                "tipo_sensor": "humedad_temperatura_CE",
                "modelo_sensor": random.choice(modelos),
                "estado_sensor": "activo" if bateria > 20 else "bateria_baja",
                "bateria_pct": bateria,
                "bateria_inicial": bateria,
                "profundidad_cm": random.choice([20, 30, 40, 60]),
                "fecha_instalacion": date(año - 1, random.randint(8, 11), 1).isoformat(),
                "zona_parcela": f"Zona {chr(65 + i)}",
            })
            sensor_id_counter += 1

    return sensores


# ═══════════════════════════════════════════════════════════════════════════
# 5. KPIs AGREGADOS PARA DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

def calcular_kpis_parcela(
    parcela_cfg: dict,
    lecturas: list[dict],
    riegos: list[dict],
) -> dict:
    cultivo = CULTIVOS[parcela_cfg["cultivo"]]
    sistema = SISTEMAS_RIEGO[parcela_cfg["sistema_riego"]]

    # Últimos 30 días
    ult_30 = lecturas[-30:]
    humedad_prom = round(sum(l["humedad_suelo_pct"] for l in ult_30) / len(ult_30), 2)
    et0_prom = round(sum(l["et0_mm_dia"] for l in ult_30) / len(ult_30), 2)
    etc_prom = round(sum(l["etc_mm_dia"] for l in ult_30) / len(ult_30), 2)
    cwsi_prom = round(sum(l["cwsi"] for l in ult_30) / len(ult_30), 3)
    dias_estres = sum(1 for l in lecturas if l["cwsi"] > 0.35)

    # Consumo total de agua de riego
    agua_total_litros = sum(r["cantidad_agua_litros"] for r in riegos)
    agua_total_m3 = agua_total_litros / 1000
    costo_agua_total = sum(r["costo_agua_mxn"] for r in riegos)
    costo_energia_total = sum(r["costo_energia_mxn"] for r in riegos)

    # Agua total consumida (riego + lluvia efectiva) para WUE real
    area_m2 = parcela_cfg["area_ha"] * 10000
    lluvia_efectiva_m3 = sum(l["precipitacion_efectiva_mm"] * area_m2 / 1000
                              for l in lecturas if "precipitacion_efectiva_mm" in l)
    agua_total_consumida_m3 = agua_total_m3 + lluvia_efectiva_m3

    # Eficiencia vs gravedad (benchmark)
    eficiencia_relativa = round(
        (SISTEMAS_RIEGO["gravedad"]["eficiencia"] / sistema["eficiencia"]) * 100 - 100, 1
    )

    # Rendimiento estimado basado en CWSI acumulado (Doorenbos & Kassam Ky)
    ky_tabla = {"maiz": 1.25, "jitomate": 1.05, "chile": 1.10, "papa": 1.10, "frijol": 1.15}
    ky = ky_tabla.get(parcela_cfg["cultivo"], 1.0)
    # Usar CWSI solo de los dias activos del cultivo (no cosecha)
    lecturas_activas = [l for l in lecturas if l["etapa_fenologica"] != "cosecha"]
    cwsi_activo = round(sum(l["cwsi"] for l in lecturas_activas) / max(1, len(lecturas_activas)), 3)
    fraccion_estres = min(0.9, cwsi_activo)
    rendimiento_max = cultivo["rendimiento_ton_ha"]["promedio"]
    rendimiento_estimado = round(rendimiento_max * (1 - ky * fraccion_estres) * parcela_cfg["area_ha"], 1)
    precio_ton = random.uniform(3500, 6000)
    ingreso_estimado = round(rendimiento_estimado * precio_ton, 0)

    # WUE [kg producido / m³ agua total consumida] — rango real: 0.5–10 kg/m³
    wue = round((rendimiento_estimado * 1000) / max(1, agua_total_consumida_m3), 2)

    # Última lectura
    ultima = lecturas[-1]

    # Estado de la parcela para dashboard (basado en lecturas activas)
    hum_activa_prom = round(
        sum(l["humedad_suelo_pct"] for l in lecturas_activas) / max(1, len(lecturas_activas)), 2
    )
    if cwsi_activo > 0.45 or hum_activa_prom < cultivo["humedad_estres_pct"]:
        estado = "estres_hidrico"
        color_estado = "#ef4444"
    elif cwsi_activo > 0.20:
        estado = "atencion"
        color_estado = "#f97316"
    else:
        estado = "optimo"
        color_estado = "#22c55e"

    return {
        "parcela_id": parcela_cfg["id"],
        "nombre_parcela": parcela_cfg["nombre"],
        "cultivo": cultivo["nombre_comun"],
        "area_ha": parcela_cfg["area_ha"],
        "sistema_riego": parcela_cfg["sistema_riego"],
        "estado": estado,
        "color_estado": color_estado,
        "humedad_actual_pct": ultima["humedad_suelo_pct"],
        "humedad_dashboard_pct": ultima["humedad_dashboard_pct"],
        "humedad_objetivo_pct": cultivo["humedad_optima_pct"],
        "humedad_promedio_30d": humedad_prom,
        "et0_promedio_30d_mm": et0_prom,
        "etc_promedio_30d_mm": etc_prom,
        "cwsi_promedio_30d": cwsi_prom,
        "dias_estres_hidrico": dias_estres,
        "etapa_actual": ultima["etapa_fenologica"],
        "dia_ciclo_actual": ultima["dia_ciclo"],
        "kc_actual": ultima["kc_etapa"],
        "agua_total_litros": round(agua_total_litros, 0),
        "agua_total_m3": round(agua_total_m3, 1),
        "costo_agua_mxn": round(costo_agua_total, 2),
        "costo_energia_mxn": round(costo_energia_total, 2),
        "costo_total_mxn": round(costo_agua_total + costo_energia_total, 2),
        "eficiencia_riego_vs_gravedad_pct": eficiencia_relativa,
        "numero_riegos": len(riegos),
        "rendimiento_estimado_ton": rendimiento_estimado,
        "ingreso_estimado_mxn": ingreso_estimado,
        "wue_kg_m3": wue,
        "ultima_lectura_fecha": ultima["fecha"],
        "ultima_humedad": ultima["humedad_suelo_pct"],
        "ultima_etc_mm": ultima["etc_mm_dia"],
    }


# ═══════════════════════════════════════════════════════════════════════════
# 6. ESCRITURA A SQLITE
# ═══════════════════════════════════════════════════════════════════════════

def crear_base_datos(
    parcelas_meta: list,
    sensores_meta: list,
    clima: list,
    todas_lecturas_diarias: list,
    todos_riegos: list,
    todas_alertas: list,
    kpis: list,
):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS parcelas (
            id_parcela TEXT PRIMARY KEY,
            nombre_parcela TEXT, area_ha REAL, cultivo_actual TEXT,
            nombre_cultivo TEXT, tipo_suelo TEXT, sistema_riego TEXT,
            humedad_objetivo_pct REAL, estado_parcela TEXT,
            color_cultivo TEXT, fecha_siembra TEXT, rendimiento_esperado_ton REAL
        );
        CREATE TABLE IF NOT EXISTS sensores (
            id TEXT PRIMARY KEY, parcela_id TEXT, tipo_sensor TEXT,
            modelo_sensor TEXT, estado_sensor TEXT, bateria_pct REAL,
            profundidad_cm INTEGER, fecha_instalacion TEXT, zona_parcela TEXT
        );
        CREATE TABLE IF NOT EXISTS clima_diario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT, dia_del_año INTEGER, mes INTEGER,
            temp_max_c REAL, temp_min_c REAL, temp_media_c REAL,
            humedad_relativa_pct REAL, precipitacion_mm REAL,
            radiacion_solar_mj_m2 REAL, velocidad_viento_m_s REAL,
            et0_mm_dia REAL, vpd_kpa REAL
        );
        CREATE TABLE IF NOT EXISTS lecturas_balance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parcela_id TEXT, fecha TEXT, dia_ciclo INTEGER,
            etapa_fenologica TEXT, kc REAL,
            humedad_suelo_pct REAL, humedad_dashboard_pct REAL,
            et0_mm_dia REAL, etc_mm_dia REAL,
            precipitacion_mm REAL, riego_litros REAL,
            cwsi REAL, deficit_hidrico_mm REAL,
            dias_desde_riego INTEGER, balance_hidrico_7d_mm REAL,
            vpd_kpa REAL
        );
        CREATE TABLE IF NOT EXISTS historial_riego (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parcela_id TEXT, fecha_riego TEXT,
            cantidad_agua_litros REAL, duracion_min INTEGER,
            metodo_riego TEXT, costo_agua_mxn REAL, costo_energia_mxn REAL,
            motivo TEXT
        );
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parcela_id TEXT, tipo_alerta TEXT, mensaje TEXT,
            prioridad TEXT, fecha_alerta TEXT, atendida INTEGER
        );
        CREATE TABLE IF NOT EXISTS kpis_parcela (
            parcela_id TEXT PRIMARY KEY,
            estado TEXT, color_estado TEXT,
            humedad_actual_pct REAL, cwsi_promedio_30d REAL,
            agua_total_m3 REAL, costo_total_mxn REAL,
            rendimiento_estimado_ton REAL, wue_kg_m3 REAL,
            etapa_actual TEXT, numero_riegos INTEGER
        );
    """)

    for p in parcelas_meta:
        cur.execute(
            "INSERT OR REPLACE INTO parcelas VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (p["id_parcela"], p["nombre_parcela"], p["area_ha"], p["cultivo_actual"],
             p["nombre_cultivo"], p["tipo_suelo"], p["sistema_riego"],
             p["humedad_objetivo_pct"], p["estado_parcela"], p["color_cultivo"],
             p["fecha_siembra"], p["rendimiento_esperado_ton"]),
        )

    for s in sensores_meta:
        cur.execute(
            "INSERT OR REPLACE INTO sensores VALUES (?,?,?,?,?,?,?,?,?)",
            (s["id"], s["parcela_id"], s["tipo_sensor"], s["modelo_sensor"],
             s["estado_sensor"], s["bateria_pct"], s["profundidad_cm"],
             s["fecha_instalacion"], s["zona_parcela"]),
        )

    for c in clima:
        cur.execute(
            "INSERT INTO clima_diario VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (c["fecha"], c["dia_del_año"], c["mes"], c["temp_max_c"], c["temp_min_c"],
             c["temp_media_c"], c["humedad_relativa_pct"], c["precipitacion_mm"],
             c["radiacion_solar_mj_m2"], c["velocidad_viento_m_s"],
             c["et0_mm_dia"], c["vpd_kpa"], c.get("Rn_mj_m2", 0)),
        )

    for l in todas_lecturas_diarias:
        cur.execute(
            "INSERT INTO lecturas_balance VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (l["parcela_id"], l["fecha"], l["dia_ciclo"], l["etapa_fenologica"],
             l["kc"], l["humedad_suelo_pct"], l["humedad_dashboard_pct"],
             l["et0_mm_dia"], l["etc_mm_dia"], l["precipitacion_mm"],
             l["riego_litros"], l["cwsi"], l["deficit_hidrico_mm"],
             l["dias_desde_riego"], l["balance_hidrico_7d_mm"], l["vpd_kpa"]),
        )

    for r in todos_riegos:
        cur.execute(
            "INSERT INTO historial_riego VALUES (NULL,?,?,?,?,?,?,?,?)",
            (r["parcela_id"], r["fecha_riego"], r["cantidad_agua_litros"],
             r["duracion_min"], r["metodo_riego"], r["costo_agua_mxn"],
             r["costo_energia_mxn"], r["motivo"]),
        )

    for a in todas_alertas:
        cur.execute(
            "INSERT INTO alertas VALUES (NULL,?,?,?,?,?,?)",
            (a["parcela_id"], a["tipo_alerta"], a["mensaje"],
             a["prioridad"], a["fecha_alerta"], int(a["atendida"])),
        )

    for k in kpis:
        cur.execute(
            "INSERT OR REPLACE INTO kpis_parcela VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (k["parcela_id"], k["estado"], k["color_estado"],
             k["humedad_actual_pct"], k["cwsi_promedio_30d"],
             k["agua_total_m3"], k["costo_total_mxn"],
             k["rendimiento_estimado_ton"], k["wue_kg_m3"],
             k["etapa_actual"], k["numero_riegos"]),
        )

    conn.commit()
    conn.close()
    print(f"  [OK] SQLite: {DB_PATH}")


# ═══════════════════════════════════════════════════════════════════════════
# 7. MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    año = SIM_CONFIG["año_inicio"]
    dias = SIM_CONFIG["dias_simulacion"]

    sep = "-" * 55
    print(f"\n{sep}")
    print(f"  AgriTech Platform - Generador de Datos Sinteticos")
    print(f"  Anno: {año}  |  Dias: {dias}  |  Seed: {SIM_CONFIG['seed_random']}")
    print(f"{sep}\n")

    # 1. Clima diario
    print("[>>] Generando clima diario (Penman-Monteith FAO-56)...")
    clima = generar_clima_diario(año, dias)
    print(f"  [OK] {len(clima)} registros climaticos | ET0 media: {sum(c['et0_mm_dia'] for c in clima)/len(clima):.2f} mm/dia")

    # 2. Metadata
    print("[>>] Generando metadata de parcelas y sensores...")
    parcelas_meta = generar_metadata_parcelas(año)
    sensores_meta = generar_metadata_sensores(año)
    print(f"  [OK] {len(parcelas_meta)} parcelas | {len(sensores_meta)} sensores")

    # 3. Balance hídrico por parcela
    print("[>>] Simulando balance hidrico por parcela...")
    todas_lecturas = []
    todos_riegos = []
    todas_alertas = []
    kpis_lista = []

    for cfg in PARCELAS_CONFIG:
        resultado = simular_parcela(cfg, clima, año)
        lecturas = resultado["lecturas_diarias"]
        riegos = resultado["riegos"]
        alertas = resultado["alertas"]

        # Añadir parcela_id a lecturas para agregación
        todas_lecturas.extend(lecturas)
        todos_riegos.extend(riegos)
        todas_alertas.extend(alertas)

        kpis = calcular_kpis_parcela(cfg, lecturas, riegos)
        kpis_lista.append(kpis)

        cultivo_nombre = CULTIVOS[cfg["cultivo"]]["nombre_comun"]
        print(
            f"  ✓ {cfg['nombre']} ({cultivo_nombre}) | "
            f"Riegos: {len(riegos)} | CWSI: {kpis['cwsi_promedio_30d']:.3f} | "
            f"WUE: {kpis['wue_kg_m3']:.1f} kg/m³ | "
            f"Rend.est.: {kpis['rendimiento_estimado_ton']} ton"
        )

    # 4. Lecturas de sensor IoT (cada 6h, muestra últimos 60 días para no saturar)
    print("[>>] Generando lecturas de sensores IoT (ultimos 60 dias)...")
    lecturas_60d_por_parcela = {
        cfg["id"]: [l for l in todas_lecturas if l["parcela_id"] == cfg["id"]][-60:]
        for cfg in PARCELAS_CONFIG
    }
    todas_lecturas_sensor = []
    for cfg in PARCELAS_CONFIG:
        sensores_parcela = [s for s in sensores_meta if s["parcela_id"] == cfg["id"]]
        lecturas_sensor = generar_lecturas_sensor(
            cfg["id"], sensores_parcela, lecturas_60d_por_parcela[cfg["id"]]
        )
        todas_lecturas_sensor.extend(lecturas_sensor)
    print(f"  [OK] {len(todas_lecturas_sensor)} lecturas de sensor generadas")

    # 5. Alertas — mantener solo las relevantes (max 200 últimas)
    todas_alertas = sorted(todas_alertas, key=lambda x: x["fecha_alerta"], reverse=True)[:200]

    # 6. Guardar JSON
    print("[>>] Guardando archivos JSON...")

    archivos = {
        "clima.json": clima,
        "parcelas.json": parcelas_meta,
        "sensores.json": sensores_meta,
        "lecturas_balance.json": todas_lecturas,
        "lecturas_sensor.json": todas_lecturas_sensor,
        "riegos.json": todos_riegos,
        "alertas.json": todas_alertas,
        "kpis_parcelas.json": kpis_lista,
    }

    for nombre, datos in archivos.items():
        path = OUTPUT_DIR / nombre
        with open(path, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        print(f"  [OK] {nombre}: {len(datos)} registros")

    # 7. SQLite
    print("[>>] Escribiendo base de datos SQLite...")
    crear_base_datos(
        parcelas_meta, sensores_meta, clima,
        todas_lecturas, todos_riegos, todas_alertas, kpis_lista,
    )

    # 8. Resumen final
    sep = "-" * 55
    print(f"\n{sep}")
    print("  RESUMEN DE DATOS GENERADOS")
    print(sep)
    et0_media = sum(c["et0_mm_dia"] for c in clima) / len(clima)
    et0_max = max(c["et0_mm_dia"] for c in clima)
    precip_total = sum(c["precipitacion_mm"] for c in clima)
    agua_total = sum(r["cantidad_agua_litros"] for r in todos_riegos) / 1_000_000
    costo_total = sum(k["costo_total_mxn"] for k in kpis_lista)
    alertas_criticas = sum(1 for a in todas_alertas if a["prioridad"] == "alta")
    rend_total = sum(k["rendimiento_estimado_ton"] for k in kpis_lista)

    print(f"  ET0 media anual:      {et0_media:.2f} mm/dia")
    print(f"  ET0 máxima:           {et0_max:.2f} mm/dia")
    print(f"  Precipitacion total:  {precip_total:.0f} mm")
    print(f"  Agua de riego total:  {agua_total:.2f} Mm³ ({agua_total*1000:.0f} m³)")
    print(f"  Costo operativo total: ${costo_total:,.0f} MXN")
    print(f"  Rendimiento estimado: {rend_total:.1f} ton")
    print(f"  Alertas críticas:     {alertas_criticas}")
    print(f"  Registros totales:    {len(todas_lecturas) + len(todos_riegos) + len(clima):,}")
    print(f"\n  Archivos en: {OUTPUT_DIR}")
    print(f"  DB en:       {DB_PATH}")