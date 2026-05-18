import requests
import numpy as np
import sqlite3
import os, sys
import math
from datetime import datetime, timedelta

# Configuración de rutas para módulos internos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import PARCELAS, SUELO, KC_ETAPAS, DB_PATH

# =============================================================================
# GESTIÓN DE CLIMA EN TIEMPO REAL (OPEN-METEO)
# =============================================================================

def descargar_clima_hoy(lat: float, lon: float, nombre: str = "") -> dict:
    """
    Obtiene variables meteorológicas actuales vía API con fallback climatológico.
    """
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = "https://api.open-meteo.com/v1/forecast"
    
    params = {
        "latitude":     lat,
        "longitude":    lon,
        "daily":        "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,shortwave_radiation_sum,relativehumidity_2m_max,relativehumidity_2m_min",
        "timezone":       "America/Mazatlan",
        "forecast_days":  1,
        "windspeed_unit": "ms",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        d = resp.json()["daily"]

        # Extracción y promedios de variables
        t_max = d["temperature_2m_max"][0]
        t_min = d["temperature_2m_min"][0]
        hr    = (d["relativehumidity_2m_max"][0] + d["relativehumidity_2m_min"][0]) / 2
        u2    = d["windspeed_10m_max"][0]
        rs    = d["shortwave_radiation_sum"][0]
        lluvia = d["precipitation_sum"][0] or 0.0

        # Cálculo de ET0 mediante Penman-Monteith
        et0 = _penman_monteith(t_max, t_min, hr, u2, rs, lat)

        return {
            "fecha": hoy, "fuente": "Open-Meteo",
            "t_max": t_max, "t_min": t_min, "hr_media": hr,
            "viento": u2, "radiacion": rs, "lluvia": lluvia, "et0": et0,
        }

    except Exception:
        # Fallback basado en registros históricos CONAGUA (Abril - Sinaloa)
        return _climatologia_abril_sinaloa(lat, nombre)


def _penman_monteith(t_max, t_min, hr, u2, rs, lat):
    """
    Algoritmo Penman-Monteith FAO-56 para resolución diaria.
    """
    t_med  = (t_max + t_min) / 2
    J      = datetime.now().timetuple().tm_yday

    # Presión de vapor y psicrometría
    es_max = 0.6108 * math.exp(17.27 * t_max / (t_max + 237.3))
    es_min = 0.6108 * math.exp(17.27 * t_min / (t_min + 237.3))
    es     = (es_max + es_min) / 2
    ea     = hr / 100 * es

    delta = 4098 * (0.6108 * math.exp(17.27 * t_med / (t_med + 237.3))) / (t_med + 237.3)**2
    gamma = 0.000665 * 101.3

    # Balance de radiación neta
    lat_r = lat * math.pi / 180
    dr    = 1 + 0.033 * math.cos(2 * math.pi * J / 365)
    d_sol = 0.409 * math.sin(2 * math.pi * J / 365 - 1.39)
    ws    = math.acos(-math.tan(lat_r) * math.tan(d_sol))
    Ra    = (24*60/math.pi) * 0.082 * dr * (
        ws * math.sin(lat_r) * math.sin(d_sol) +
        math.cos(lat_r) * math.cos(d_sol) * math.sin(ws)
    )
    
    Rns   = (1 - 0.23) * rs
    sigma = 4.903e-9
    Rnl   = sigma * ((t_max+273.16)**4 + (t_min+273.16)**4) / 2 * \
            (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * rs / (0.75 * Ra + 0.001) - 0.35)
    
    Rn = Rns - Rnl

    # Ecuación final ET0 [mm/día]
    num = 0.408 * delta * Rn + gamma * (900 / (t_med + 273)) * u2 * (es - ea)
    den = delta + gamma * (1 + 0.34 * u2)
    
    return round(max(num / den, 0), 2)


def _climatologia_abril_sinaloa(lat: float, nombre: str) -> dict:
    """
    Datos de contingencia basados en el gradiente térmico de Sinaloa.
    """
    hoy = datetime.now().strftime("%Y-%m-%d")

    if lat > 25.5:       # Zona Norte
        t_max, t_min, hr, u2, rs = 41.5, 24.0, 30.0, 3.1, 25.2
    elif lat > 24.5:     # Zona Centro
        t_max, t_min, hr, u2, rs = 38.5, 22.5, 35.0, 2.8, 24.1
    else:                # Zona Sur
        t_max, t_min, hr, u2, rs = 35.0, 22.0, 48.0, 2.5, 22.0

    lluvia = 0.2 if lat <= 24.5 else 0.0
    et0 = _penman_monteith(t_max, t_min, hr, u2, rs, lat)

    return {
        "fecha": hoy, "fuente": "climatologia_CONAGUA",
        "t_max": t_max, "t_min": t_min, "hr_media": hr,
        "viento": u2, "radiacion": rs, "lluvia": lluvia, "et0": et0,
    }


def calcular_theta_hoy(parcela_id: str, clima_hoy: dict) -> float:
    """
    Cálculo de humedad actual integrando el último registro histórico (Modelo Híbrido).
    """
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("""
        SELECT theta_real, kc FROM lecturas_sensor
        WHERE parcela_id = ? ORDER BY fecha DESC LIMIT 1
    """, (parcela_id,)).fetchone()
    conn.close()

    # Estado inicial en caso de ausencia de registros
    theta_prev = row[0] if row else SUELO["theta_fc"] * 0.85
    kc = row[1] if row and row[1] else 0.80

    et0_hoy = clima_hoy.get("et0", 8.0)
    etc_hoy = et0_hoy * kc
    lluvia_efectiva = clima_hoy.get("lluvia", 0.0) * 0.80
    zr = 0.90 # Profundidad radicular estándar

    # Balance de masa hídrica (un solo paso de tiempo)
    delta = (lluvia_efectiva - etc_hoy) / (zr * 1000)
    theta_hoy = np.clip(theta_prev + delta, SUELO["theta_pwp"] * 0.85, SUELO["theta_fc"])

    return round(float(theta_hoy), 4)


def obtener_clima_todas_parcelas() -> dict:
    """
    Procesa el estado hídrico actual para la totalidad de la red de parcelas.
    """
    resultados = {}
    for parcela_id, info in PARCELAS.items():
        clima = descargar_clima_hoy(info["lat"], info["lon"], info["nombre"])
        theta = calcular_theta_hoy(parcela_id, clima)
        
        resultados[parcela_id] = {
            "parcela_id": parcela_id,
            "nombre":     info["nombre"],
            "clima":      clima,
            "theta_real": theta,
            "fecha":      clima["fecha"],
        }
    return resultados


if __name__ == "__main__":
    datos = obtener_clima_todas_parcelas()