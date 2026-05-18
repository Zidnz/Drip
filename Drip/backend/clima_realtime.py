import requests
import numpy as np
import sqlite3
import os
import sys
import math
import time

from datetime import datetime

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import (
    PARCELAS,
    SUELO,
    KC_ETAPAS,
    DB_PATH
)

# =============================================================================
# OPEN-METEO REALTIME + DAILY
# =============================================================================

def descargar_clima_hoy(
    lat: float,
    lon: float,
    nombre: str = ""
) -> dict:

    hoy = datetime.now().strftime("%Y-%m-%d")

    url = "https://api.open-meteo.com/v1/forecast"

    params = {

        "latitude": lat,
        "longitude": lon,

        # =====================================================================
        # VARIABLES EN TIEMPO REAL
        # =====================================================================

        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "wind_speed_10m,"
            "precipitation,"
            "shortwave_radiation"
        ),

        # =====================================================================
        # VARIABLES DIARIAS
        # =====================================================================

        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min"
        ),

        "timezone": "America/Mazatlan",

        "forecast_days": 1,

        "windspeed_unit": "ms",
    }

    try:

        resp = requests.get(
            url,
            params=params,
            timeout=10
        )

        resp.raise_for_status()

        data = resp.json()

        # =====================================================================
        # DATOS CURRENT (TIEMPO REAL)
        # =====================================================================

        current = data["current"]

        temperatura = current["temperature_2m"]

        humedad = current["relative_humidity_2m"]

        viento = current["wind_speed_10m"]

        lluvia = current["precipitation"] or 0.0

        radiacion = current["shortwave_radiation"]

        # =====================================================================
        # DATOS DAILY
        # =====================================================================

        daily = data["daily"]

        t_max = daily["temperature_2m_max"][0]

        t_min = daily["temperature_2m_min"][0]

        # =====================================================================
        # ET0 PENMAN-MONTEITH
        # =====================================================================

        et0 = _penman_monteith(
            t_max,
            t_min,
            humedad,
            viento,
            radiacion,
            lat
        )

        # =====================================================================
        # ALERTAS AGROCLIMÁTICAS
        # =====================================================================

        alertas = []

        # Ola de calor
        if temperatura >= 38:
            alertas.append("OLA_DE_CALOR")

        # Estrés hídrico
        if temperatura >= 35 and humedad <= 30:
            alertas.append("ESTRES_HIDRICO")

        # Viento fuerte
        if viento >= 12:
            alertas.append("VIENTO_FUERTE")

        # Alta evapotranspiración
        if et0 >= 8:
            alertas.append("ALTA_EVAPOTRANSPIRACION")

        # =====================================================================
        # PREDICCIÓN FUTURA SIMPLE
        # =====================================================================

        theta_pred_24h = round(
            SUELO["theta_fc"] - (et0 / 1000),
            4
        )

        theta_pred_3d = round(
            SUELO["theta_fc"] - ((et0 * 3) / 1000),
            4
        )

        theta_pred_7d = round(
            SUELO["theta_fc"] - ((et0 * 7) / 1000),
            4
        )

        if theta_pred_3d < SUELO["theta_umbral"]:
            alertas.append("DEFICIT_CRITICO_72H")

        # =====================================================================
        # RETORNO FINAL
        # =====================================================================

        return {

            "fecha": hoy,

            "fuente": "Open-Meteo REALTIME",

            # -----------------------------------------------------------------
            # TIEMPO REAL
            # -----------------------------------------------------------------

            "temperatura": round(float(temperatura), 2),

            "humedad": round(float(humedad), 2),

            "viento": round(float(viento), 2),

            "radiacion": round(float(radiacion), 2),

            "lluvia": round(float(lluvia), 2),

            # -----------------------------------------------------------------
            # VARIABLES DIARIAS
            # -----------------------------------------------------------------

            "t_max": round(float(t_max), 2),

            "t_min": round(float(t_min), 2),

            # -----------------------------------------------------------------
            # ET0
            # -----------------------------------------------------------------

            "et0": round(float(et0), 2),

            # -----------------------------------------------------------------
            # PREDICCIONES
            # -----------------------------------------------------------------

            "theta_pred_24h": theta_pred_24h,

            "theta_pred_3d": theta_pred_3d,

            "theta_pred_7d": theta_pred_7d,

            # -----------------------------------------------------------------
            # ALERTAS
            # -----------------------------------------------------------------

            "alertas": alertas
        }

    except Exception as e:

        print(f"[ERROR API CLIMA] {e}")

        return _climatologia_abril_sinaloa(
            lat,
            nombre
        )

# =============================================================================
# PENMAN-MONTEITH FAO-56
# =============================================================================

def _penman_monteith(
    t_max,
    t_min,
    hr,
    u2,
    rs,
    lat
):

    t_med = (t_max + t_min) / 2

    J = datetime.now().timetuple().tm_yday

    # =====================================================================
    # PRESIÓN DE VAPOR
    # =====================================================================

    es_max = 0.6108 * math.exp(
        17.27 * t_max / (t_max + 237.3)
    )

    es_min = 0.6108 * math.exp(
        17.27 * t_min / (t_min + 237.3)
    )

    es = (es_max + es_min) / 2

    ea = hr / 100 * es

    # =====================================================================
    # DELTA
    # =====================================================================

    delta = (
        4098 *
        (
            0.6108 *
            math.exp(
                17.27 * t_med / (t_med + 237.3)
            )
        )
        /
        (t_med + 237.3) ** 2
    )

    gamma = 0.000665 * 101.3

    # =====================================================================
    # RADIACIÓN EXTRATERRESTRE
    # =====================================================================

    lat_r = lat * math.pi / 180

    dr = (
        1 +
        0.033 *
        math.cos(2 * math.pi * J / 365)
    )

    d_sol = (
        0.409 *
        math.sin(2 * math.pi * J / 365 - 1.39)
    )

    ws = math.acos(
        -math.tan(lat_r) *
        math.tan(d_sol)
    )

    Ra = (
        (24 * 60 / math.pi) *
        0.082 *
        dr *
        (
            ws *
            math.sin(lat_r) *
            math.sin(d_sol)
            +
            math.cos(lat_r) *
            math.cos(d_sol) *
            math.sin(ws)
        )
    )

    # =====================================================================
    # BALANCE DE RADIACIÓN
    # =====================================================================

    Rns = (1 - 0.23) * rs

    sigma = 4.903e-9

    Rnl = (
        sigma *
        (
            (
                (t_max + 273.16) ** 4 +
                (t_min + 273.16) ** 4
            ) / 2
        ) *
        (
            0.34 - 0.14 * math.sqrt(max(ea, 0.01))
        ) *
        (
            1.35 * rs / (0.75 * Ra + 0.001)
            - 0.35
        )
    )

    Rn = Rns - Rnl

    # =====================================================================
    # ECUACIÓN FAO-56
    # =====================================================================

    num = (
        0.408 * delta * Rn
        +
        gamma *
        (
            900 / (t_med + 273)
        ) *
        u2 *
        (es - ea)
    )

    den = (
        delta +
        gamma *
        (1 + 0.34 * u2)
    )

    et0 = max(num / den, 0)

    return round(et0, 2)

# =============================================================================
# FALLBACK CLIMATOLÓGICO
# =============================================================================

def _climatologia_abril_sinaloa(
    lat: float,
    nombre: str
):

    hoy = datetime.now().strftime("%Y-%m-%d")

    if lat > 25.5:

        t_max = 41.5
        t_min = 24.0
        hr = 30.0
        viento = 3.1
        radiacion = 25.2

    elif lat > 24.5:

        t_max = 38.5
        t_min = 22.5
        hr = 35.0
        viento = 2.8
        radiacion = 24.1

    else:

        t_max = 35.0
        t_min = 22.0
        hr = 48.0
        viento = 2.5
        radiacion = 22.0

    lluvia = 0.2 if lat <= 24.5 else 0.0

    et0 = _penman_monteith(
        t_max,
        t_min,
        hr,
        viento,
        radiacion,
        lat
    )

    return {

        "fecha": hoy,

        "fuente": "CLIMATOLOGIA_CONAGUA",

        "temperatura": (t_max + t_min) / 2,

        "humedad": hr,

        "viento": viento,

        "radiacion": radiacion,

        "lluvia": lluvia,

        "t_max": t_max,

        "t_min": t_min,

        "et0": et0,

        "theta_pred_24h": 0.0,

        "theta_pred_3d": 0.0,

        "theta_pred_7d": 0.0,

        "alertas": ["FALLBACK_CLIMATOLOGICO"]
    }

# =============================================================================
# BALANCE HÍDRICO
# =============================================================================

def calcular_theta_hoy(
    parcela_id: str,
    clima_hoy: dict
) -> float:

    conn = sqlite3.connect(DB_PATH)

    row = conn.execute("""

        SELECT
            theta_real,
            kc

        FROM lecturas_sensor

        WHERE parcela_id = ?

        ORDER BY fecha DESC

        LIMIT 1

    """, (parcela_id,)).fetchone()

    conn.close()

    # =====================================================================
    # ESTADO PREVIO
    # =====================================================================

    theta_prev = (
        row[0]
        if row
        else SUELO["theta_fc"] * 0.85
    )

    kc = (
        row[1]
        if row and row[1]
        else 0.80
    )

    # =====================================================================
    # ET0 / ETC
    # =====================================================================

    et0_hoy = clima_hoy.get("et0", 8.0)

    etc_hoy = et0_hoy * kc

    lluvia_efectiva = (
        clima_hoy.get("lluvia", 0.0) * 0.80
    )

    zr = 0.90

    # =====================================================================
    # BALANCE HÍDRICO
    # =====================================================================

    delta = (
        (lluvia_efectiva - etc_hoy)
        /
        (zr * 1000)
    )

    theta_hoy = np.clip(

        theta_prev + delta,

        SUELO["theta_pwp"] * 0.85,

        SUELO["theta_fc"]
    )

    return round(float(theta_hoy), 4)

# =============================================================================
# TODAS LAS PARCELAS
# =============================================================================

def obtener_clima_todas_parcelas():

    resultados = {}

    for parcela_id, info in PARCELAS.items():

        clima = descargar_clima_hoy(
            info["lat"],
            info["lon"],
            info["nombre"]
        )

        theta = calcular_theta_hoy(
            parcela_id,
            clima
        )

        resultados[parcela_id] = {

            "parcela_id": parcela_id,

            "nombre": info["nombre"],

            "fecha": clima["fecha"],

            "theta_real": theta,

            "clima": clima
        }

    return resultados

# =============================================================================
# MAIN LOOP TIEMPO REAL
# =============================================================================

if __name__ == "__main__":

    while True:

        try:

            datos = obtener_clima_todas_parcelas()

            # Limpia consola
            os.system("cls" if os.name == "nt" else "clear")

            print("=" * 70)
            print("CLIMA AGRÍCOLA EN TIEMPO REAL")
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print("=" * 70)

            for parcela_id, data in datos.items():

                clima = data["clima"]

                print("\n--------------------------------------------------")

                print(f"PARCELA     : {data['nombre']}")

                print(f"TEMP        : {clima['temperatura']} °C")

                print(f"HUMEDAD     : {clima['humedad']} %")

                print(f"VIENTO      : {clima['viento']} m/s")

                print(f"RADIACIÓN   : {clima['radiacion']} W/m2")

                print(f"LLUVIA      : {clima['lluvia']} mm")

                print(f"ET0         : {clima['et0']} mm/día")

                print(f"THETA REAL  : {data['theta_real']}")

                print(
                    f"THETA 24H   : "
                    f"{clima['theta_pred_24h']}"
                )

                print(
                    f"THETA 3D    : "
                    f"{clima['theta_pred_3d']}"
                )

                print(
                    f"THETA 7D    : "
                    f"{clima['theta_pred_7d']}"
                )

                print(f"ALERTAS     : {clima['alertas']}")

                print("--------------------------------------------------")

            print("\nActualizando automáticamente en 5 minutos...\n")

            # ================================================================
            # ACTUALIZACIÓN AUTOMÁTICA
            # ================================================================

            time.sleep(300)

        except KeyboardInterrupt:

            print("\nSistema detenido manualmente")
            break

        except Exception as e:

            print(f"\nERROR GENERAL: {e}")

            print("\nReintentando en 60 segundos...\n")

            time.sleep(60)