# =============================================================================
# actualizar_historial.py — Actualiza el historial del suelo con datos reales
# =============================================================================
# FLUJO:
#   1. Descargar clima de la fecha desde Open-Meteo (o climatologia mensual)
#   2. Leer theta del dia anterior desde SQLite
#   3. Calcular theta con balance hidrico
#   4. Si theta < umbral → aplicar riego automatico (el sistema SI riega)
#   5. Guardar theta post-riego en SQLite
#   6. Repetir → historial continuo y realista
# =============================================================================

import sqlite3
import os, sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import DB_PATH, PARCELAS, SUELO, KC_ETAPAS, CICLO_DIAS
from open_meteo import _penman_monteith


# ET0 mensual promedio para Sinaloa (mm/dia)
# Fuente: CONAGUA + NASA POWER historico 2010-2024
# Norte (Los Mochis/Guasave) / Centro (Culiacan/Navolato) / Sur (Escuinapa)
ET0_MENSUAL_SINALOA = {
    #  mes: [norte,  centro, sur]
    1:      [5.2,    4.8,    4.2],   # Enero   - invierno, fresco
    2:      [6.1,    5.6,    4.9],   # Febrero - calienta gradual
    3:      [7.8,    7.1,    6.2],   # Marzo   - calor creciente
    4:      [9.3,    8.4,    7.2],   # Abril   - calor, temporada seca
    5:      [10.1,   9.2,    7.8],   # Mayo    - pico de calor
    6:      [8.9,    8.1,    7.0],   # Junio   - lluvias empiezan
    7:      [7.8,    7.2,    6.4],   # Julio   - temporada lluvias
    8:      [7.5,    7.0,    6.2],   # Agosto  - lluvias
    9:      [7.2,    6.8,    6.0],   # Septiembre
    10:     [6.5,    6.0,    5.3],   # Octubre - lluvias terminan
    11:     [5.0,    4.6,    4.1],   # Noviembre - fresco
    12:     [4.5,    4.1,    3.7],   # Diciembre - invierno
}

# Precipitacion mensual promedio (mm totales del mes)
# Sinaloa: temporada de lluvias julio-septiembre
LLUVIA_MENSUAL_SINALOA = {
    #  mes: [norte, centro, sur]
    1:      [15,    12,    18],
    2:      [8,     6,     12],
    3:      [5,     4,     8],
    4:      [3,     2,     5],
    5:      [5,     4,     8],
    6:      [40,    35,    60],
    7:      [180,   160,   220],
    8:      [200,   180,   250],
    9:      [120,   100,   150],
    10:     [30,    25,    40],
    11:     [12,    10,    18],
    12:     [15,    12,    20],
}


def _get_zona(lat: float) -> int:
    """0=norte, 1=centro, 2=sur segun latitud de Sinaloa."""
    if lat > 25.5:
        return 0
    elif lat > 24.5:
        return 1
    else:
        return 2


def _clima_para_fecha(lat: float, fecha: str) -> dict:
    """
    Obtiene datos climaticos para una fecha especifica.
    Intenta Open-Meteo primero; si falla usa climatologia mensual
    con valores correctos segun el mes del ano.
    """
    import requests

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":      lat, "longitude": -107.4,
        "daily":         "temperature_2m_max,temperature_2m_min,"
                         "precipitation_sum,windspeed_10m_max,"
                         "shortwave_radiation_sum,"
                         "relativehumidity_2m_max,relativehumidity_2m_min",
        "timezone":      "America/Mazatlan",
        "start_date":    fecha, "end_date": fecha,
        "windspeed_unit":"ms",
    }
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        d = r.json()["daily"]
        t_max  = d["temperature_2m_max"][0]
        t_min  = d["temperature_2m_min"][0]
        hr     = (d["relativehumidity_2m_max"][0] +
                  d["relativehumidity_2m_min"][0]) / 2
        u2     = d["windspeed_10m_max"][0]
        rs     = d["shortwave_radiation_sum"][0]
        lluvia = d["precipitation_sum"][0] or 0.0
        et0    = _penman_monteith(t_max, t_min, hr, u2, rs, lat)
        return {"et0": et0, "lluvia": lluvia,
                "t_max": t_max, "t_min": t_min, "hr": hr,
                "fuente": "open_meteo"}
    except Exception:
        pass

    # Fallback: climatologia mensual correcta segun mes
    mes  = int(fecha[5:7])
    zona = _get_zona(lat)
    et0_mes    = ET0_MENSUAL_SINALOA[mes][zona]
    lluvia_mes = LLUVIA_MENSUAL_SINALOA[mes][zona]
    # Distribuir lluvia del mes uniformemente por dia
    import calendar
    dias_mes = calendar.monthrange(int(fecha[:4]), mes)[1]
    lluvia_dia = round(lluvia_mes / dias_mes, 2)

    # Temperatura tipica por mes y zona
    t_base = {1:26, 2:28, 3:32, 4:38, 5:40, 6:38,
              7:35, 8:34, 9:33, 10:32, 11:28, 12:25}
    t_max = t_base[mes] - zona * 2.5
    t_min = t_max - 16

    return {
        "et0": et0_mes, "lluvia": lluvia_dia,
        "t_max": t_max, "t_min": t_min, "hr": 40 - zona*5,
        "fuente": f"climatologia_mensual_mes{mes}"
    }


def _kc_para_fecha(info: dict, fecha: str) -> tuple:
    """Retorna (kc, zr, etapa, dia_ciclo) para la fecha dada."""
    anio = int(fecha[:4])
    mes_dia = info["fecha_siembra"]
    try:
        fecha_s = datetime.strptime(f"{anio}-{mes_dia}", "%Y-%m-%d")
    except Exception:
        return 0.80, 0.70, "Media", 65

    fecha_a   = datetime.strptime(fecha, "%Y-%m-%d")
    dia_ciclo = (fecha_a - fecha_s).days

    if dia_ciclo < 0 or dia_ciclo > CICLO_DIAS:
        return 0.30, 0.30, "Fuera de ciclo", dia_ciclo

    for e in KC_ETAPAS:
        if e["dia_inicio"] <= dia_ciclo <= e["dia_fin"]:
            dur = e["dia_fin"] - e["dia_inicio"]
            f   = (dia_ciclo - e["dia_inicio"]) / dur if dur > 0 else 0
            kc  = e["kc_inicio"] + f * (e["kc_fin"] - e["kc_inicio"])
            zr  = e["zr_inicio"] + f * (e["zr_fin"] - e["zr_inicio"])
            return round(kc,4), round(zr,4), e["nombre"], dia_ciclo

    return 0.30, 0.30, "Inicial", dia_ciclo


def calcular_y_guardar_dia(parcela_id: str, info: dict,
                            fecha: str, conn: sqlite3.Connection) -> dict:
    """
    Calcula y guarda theta para UN dia.

    DIFERENCIA CLAVE vs la version anterior:
    Si theta cae bajo el umbral, el sistema APLICA RIEGO
    (igual que lo haria en la realidad si se sigue la recomendacion).
    Esto mantiene el historial fisicamente realista.
    """
    # No sobreescribir si ya existe
    existe = conn.execute(
        "SELECT theta_real FROM lecturas_sensor WHERE parcela_id=? AND fecha=?",
        (parcela_id, fecha)
    ).fetchone()
    if existe:
        return {"theta_real": existe[0], "ya_existia": True}

    # Theta del dia anterior
    row_ant = conn.execute("""
        SELECT theta_real FROM lecturas_sensor
        WHERE parcela_id=? AND fecha < ?
        ORDER BY fecha DESC LIMIT 1
    """, (parcela_id, fecha)).fetchone()
    theta_prev = row_ant[0] if row_ant else SUELO["theta_fc"] * 0.85

    # Clima de la fecha
    clima  = _clima_para_fecha(info["lat"], fecha)
    et0    = clima["et0"]
    lluvia = clima["lluvia"]

    # Kc y Zr
    kc, zr, etapa, dia_ciclo = _kc_para_fecha(info, fecha)

    etc             = et0 * kc
    lluvia_efectiva = lluvia * 0.80

    # Balance hidrico
    delta     = (lluvia_efectiva - etc) / (zr * 1000)
    theta_raw = theta_prev + delta
    theta_raw = min(theta_raw, SUELO["theta_fc"])
    theta_raw = max(theta_raw, SUELO["theta_pwp"] * 0.85)

    # RIEGO AUTOMATICO: si bajo el umbral, el agricultor riega
    # Esto es lo que hace que el historial sea realista —
    # no simulamos un campo abandonado, sino uno operado
    riego_mm = 0.0
    if theta_raw < SUELO["theta_umbral"]:
        # Regar hasta capacidad de campo
        riego_mm = round(
            (SUELO["theta_fc"] - theta_raw) * zr * 1000, 1
        )
        riego_mm  = min(riego_mm, 80.0)  # limite operativo
        theta_raw = theta_raw + riego_mm / (zr * 1000)
        theta_raw = min(theta_raw, SUELO["theta_fc"])

    theta_final = round(theta_raw, 4)
    deficit     = round(max(0, SUELO["theta_fc"] - theta_final), 4)

    # Clase post-riego
    if theta_final >= SUELO["theta_umbral"]:
        clase = 0
    elif theta_final >= SUELO["theta_critico"]:
        clase = 1
    else:
        clase = 2

    # Guardar en lecturas_sensor
    conn.execute("""
        INSERT OR IGNORE INTO lecturas_sensor
        (parcela_id, fecha, dia_ciclo, etapa, kc,
         theta_real, theta_sensor, tipo_error,
         deficit_hidrico, clase_hoy, clase_t3)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (parcela_id, fecha, dia_ciclo, etapa, kc,
          theta_final, None, "pendiente",
          deficit, clase, clase))

    # Guardar clima en clima_diario
    conn.execute("""
        INSERT OR IGNORE INTO clima_diario
        (parcela_id, fecha, t_max, t_min, humedad_rel,
         viento, radiacion, lluvia, et0)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (parcela_id, fecha,
          clima.get("t_max", 35), clima.get("t_min", 20),
          clima.get("hr", 35), 3.0, 20.0,
          lluvia, et0))

    # Registrar evento de riego si se aplico
    if riego_mm > 0:
        lamina_m3 = round(riego_mm * info["area_ha"] * 10, 1)
        conn.execute("""
            INSERT OR IGNORE INTO eventos_riego
            (parcela_id, fecha, lamina_mm, lamina_m3,
             tipo_riego, trigger_clase, theta_antes, theta_esperada)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (parcela_id, fecha, riego_mm, lamina_m3,
              "automatico_historial", 1,
              round(theta_raw - riego_mm/(zr*1000), 4),
              theta_final))

    conn.commit()

    return {
        "theta_real":  theta_final,
        "theta_prev":  theta_prev,
        "et0":         et0,
        "etc":         round(etc, 2),
        "lluvia":      lluvia,
        "riego_mm":    riego_mm,
        "kc":          kc,
        "etapa":       etapa,
        "dia_ciclo":   dia_ciclo,
        "clase":       clase,
        "ya_existia":  False,
        "fuente":      clima.get("fuente", "?"),
    }


def cerrar_gap_y_actualizar(dias_atras: int = 120) -> dict:
    """Calcula todos los dias faltantes desde el ultimo registro hasta hoy."""
    conn    = sqlite3.connect(DB_PATH)
    hoy     = datetime.now().strftime("%Y-%m-%d")
    hoy_dt  = datetime.strptime(hoy, "%Y-%m-%d")
    resumen = {}

    for parcela_id, info in PARCELAS.items():
        row = conn.execute(
            "SELECT MAX(fecha) FROM lecturas_sensor WHERE parcela_id=?",
            (parcela_id,)
        ).fetchone()

        ultimo   = row[0] if row[0] else "2021-01-01"
        inicio_dt = datetime.strptime(ultimo, "%Y-%m-%d") + timedelta(days=1)
        n_dias    = min((hoy_dt - inicio_dt).days + 1, dias_atras)

        if n_dias <= 0:
            print(f"  [{parcela_id}] {info['nombre']} — al dia")
            resumen[parcela_id] = {"dias_nuevos": 0, "theta_hoy": None}
            continue

        print(f"\n  [{parcela_id}] {info['nombre']}")
        print(f"    Desde: {ultimo} | Dias a calcular: {n_dias}")

        dias_calc   = 0
        theta_final = None

        for i in range(n_dias):
            fecha  = (inicio_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            r      = calcular_y_guardar_dia(parcela_id, info, fecha, conn)
            if not r.get("ya_existia"):
                dias_calc   += 1
                theta_final  = r["theta_real"]
                # Mostrar cada 15 dias y el ultimo
                if dias_calc % 15 == 1 or fecha == hoy:
                    riego_txt = f" [riego {r['riego_mm']}mm]" if r.get("riego_mm",0) > 0 else ""
                    print(f"    {fecha}: theta={r['theta_real']} "
                          f"ET0={r['et0']:.1f}mm"
                          f"{riego_txt}")

        # Estado de hoy
        row_hoy = conn.execute(
            "SELECT theta_real, clase_hoy FROM lecturas_sensor "
            "WHERE parcela_id=? AND fecha=?",
            (parcela_id, hoy)
        ).fetchone()

        if row_hoy:
            estados = ["No regar", "Regar pronto", "RIEGO URGENTE"]
            print(f"\n    HOY {hoy}: theta={row_hoy[0]} "
                  f"→ {estados[row_hoy[1]]}")

        resumen[parcela_id] = {
            "dias_nuevos": dias_calc,
            "theta_hoy":   row_hoy[0] if row_hoy else theta_final,
        }

    conn.close()
    return resumen


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  ACTUALIZADOR DE HISTORIAL DEL SUELO v2")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Limpiar registros con fuente "pendiente" del intento anterior
    conn = sqlite3.connect(DB_PATH)
    n_borrados = conn.execute("""
        DELETE FROM lecturas_sensor
        WHERE tipo_error = 'pendiente'
        AND fecha > '2025-08-01'
    """).rowcount
    conn.commit()
    conn.close()
    if n_borrados > 0:
        print(f"\n  Limpiando {n_borrados} registros del intento anterior...")

    print("\n  Calculando dias faltantes con ET0 mensual correcta")
    print("  y riego automatico cuando el suelo baja del umbral...\n")

    resumen = cerrar_gap_y_actualizar(dias_atras=120)

    print("\n" + "="*60)
    print("  RESUMEN FINAL")
    total = sum(v["dias_nuevos"] for v in resumen.values())
    print(f"  Dias nuevos calculados: {total}")
    for pid, v in resumen.items():
        if v["theta_hoy"]:
            umbral = SUELO["theta_umbral"]
            estado = "OK" if v["theta_hoy"] >= umbral else "necesita riego"
            print(f"  {pid}: theta hoy = {v['theta_hoy']} ({estado})")
    print("\n  Historial listo. Listo para recomendar con datos reales.")
    print("="*60)
