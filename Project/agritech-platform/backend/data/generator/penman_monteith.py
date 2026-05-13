"""
Implementación de Penman-Monteith (FAO-56) para cálculo de ET₀.
Referencia: Allen et al. (1998). FAO Irrigation and Drainage Paper No. 56.

ET₀ = [0.408 · Δ · (Rn - G) + γ · (900/(T+273)) · u₂ · (es - ea)]
      / [Δ + γ · (1 + 0.34 · u₂)]

donde:
    ET₀ = evapotranspiración de referencia [mm/día]
    Δ   = pendiente de la curva de presión de vapor saturante [kPa/°C]
    Rn  = radiación neta en superficie del cultivo [MJ/m²/día]
    G   = flujo de calor en el suelo [MJ/m²/día] ≈ 0 para cálculo diario
    γ   = constante psicrométrica [kPa/°C]
    T   = temperatura media diaria del aire [°C]
    u₂  = velocidad del viento a 2 m altura [m/s]
    es  = presión de vapor de saturación [kPa]
    ea  = presión de vapor real [kPa]
"""

import math


def calcular_et0(
    temp_max_c: float,
    temp_min_c: float,
    humedad_rel_pct: float,
    radiacion_mj_m2: float,
    viento_m_s: float,
    elevacion_msnm: float = 60.0,
    dia_del_año: int = 180,
    latitud_rad: float = math.radians(24.8),   # Culiacán, Sinaloa ≈ 24.8°N
) -> dict:
    """
    Calcula ET₀ diaria usando Penman-Monteith FAO-56.

    Returns dict con ET₀ y variables intermedias para trazabilidad.
    """

    # --- Temperatura media ---
    T = (temp_max_c + temp_min_c) / 2.0

    # --- Presión atmosférica (kPa) a partir de elevación ---
    P = 101.3 * ((293 - 0.0065 * elevacion_msnm) / 293) ** 5.26

    # --- Constante psicrométrica γ [kPa/°C] ---
    gamma = 0.000665 * P

    # --- Pendiente de la curva de presión de vapor saturante Δ [kPa/°C] ---
    delta = (4098 * (0.6108 * math.exp(17.27 * T / (T + 237.3)))) / (T + 237.3) ** 2

    # --- Presión de vapor de saturación es [kPa] ---
    e_s_tmax = 0.6108 * math.exp(17.27 * temp_max_c / (temp_max_c + 237.3))
    e_s_tmin = 0.6108 * math.exp(17.27 * temp_min_c / (temp_min_c + 237.3))
    es = (e_s_tmax + e_s_tmin) / 2.0

    # --- Presión de vapor real ea [kPa] ---
    ea = (humedad_rel_pct / 100.0) * es

    # --- Déficit de presión de vapor (VPD) [kPa] ---
    vpd = es - ea

    # --- Radiación extraterrestre Ra [MJ/m²/día] (FAO-56 Eq. 21) ---
    dr = 1 + 0.033 * math.cos(2 * math.pi / 365 * dia_del_año)
    declinacion = 0.409 * math.sin(2 * math.pi / 365 * dia_del_año - 1.39)
    ws = math.acos(-math.tan(latitud_rad) * math.tan(declinacion))
    Ra = (24 * 60 / math.pi) * 0.0820 * dr * (
        ws * math.sin(latitud_rad) * math.sin(declinacion)
        + math.cos(latitud_rad) * math.cos(declinacion) * math.sin(ws)
    )

    # --- Radiación solar Rs (usamos el valor medido/simulado directamente) ---
    Rs = radiacion_mj_m2

    # --- Radiación solar en cielo despejado Rso [MJ/m²/día] ---
    Rso = (0.75 + 2e-5 * elevacion_msnm) * Ra

    # --- Radiación neta de onda corta Rns ---
    alfa = 0.23   # albedo superficie de referencia (pasto corto)
    Rns = (1 - alfa) * Rs

    # --- Radiación neta de onda larga Rnl (FAO-56 Eq. 39) ---
    sigma = 4.903e-9   # Stefan-Boltzmann [MJ/K⁴/m²/día]
    T_max_K = temp_max_c + 273.16
    T_min_K = temp_min_c + 273.16
    Rs_Rso_ratio = min(Rs / Rso, 1.0) if Rso > 0 else 0.5
    Rnl = sigma * ((T_max_K**4 + T_min_K**4) / 2) * (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * Rs_Rso_ratio - 0.35)

    # --- Radiación neta Rn [MJ/m²/día] ---
    Rn = Rns - Rnl

    # --- Flujo de calor en suelo G ≈ 0 (cálculo diario) ---
    G = 0.0

    # --- ET₀ Penman-Monteith [mm/día] ---
    numerador = 0.408 * delta * (Rn - G) + gamma * (900 / (T + 273)) * viento_m_s * vpd
    denominador = delta + gamma * (1 + 0.34 * viento_m_s)
    et0 = max(numerador / denominador, 0.0)

    return {
        "et0_mm_dia": round(et0, 3),
        "temp_media_c": round(T, 2),
        "presion_atm_kpa": round(P, 2),
        "delta_kpa_c": round(delta, 4),
        "gamma_kpa_c": round(gamma, 4),
        "es_kpa": round(es, 4),
        "ea_kpa": round(ea, 4),
        "vpd_kpa": round(vpd, 4),
        "Ra_mj_m2": round(Ra, 3),
        "Rn_mj_m2": round(Rn, 3),
    }


def calcular_etc(et0: float, kc: float) -> float:
    """
    ETc = ET₀ × Kc
    Evapotranspiración del cultivo [mm/día].
    """
    return round(et0 * kc, 3)


def calcular_kc_etapa(dia_ciclo: int, etapas_dias: dict, kc_valores: dict) -> tuple:
    """
    Devuelve (Kc, nombre_etapa) interpolando linealmente entre etapas.
    dia_ciclo: días desde siembra (0-indexed).
    """
    ini = etapas_dias["inicial"]
    des = etapas_dias["desarrollo"]
    med = etapas_dias["media"]
    fin = etapas_dias["final"]

    kc_ini = kc_valores["inicial"]
    kc_med = kc_valores["media"]
    kc_fin = kc_valores["final"]

    if dia_ciclo < ini:
        return kc_ini, "inicial"
    elif dia_ciclo < ini + des:
        # Interpolación lineal ini → media
        t = (dia_ciclo - ini) / des
        kc = kc_ini + t * (kc_med - kc_ini)
        return round(kc, 3), "desarrollo"
    elif dia_ciclo < ini + des + med:
        return kc_med, "media"
    elif dia_ciclo < ini + des + med + fin:
        # Interpolación lineal media → final
        t = (dia_ciclo - ini - des - med) / fin
        kc = kc_med + t * (kc_fin - kc_med)
        return round(kc, 3), "final"
    else:
        return kc_fin, "cosecha"
