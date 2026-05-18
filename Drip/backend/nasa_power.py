import requests
import json
import time
import sqlite3
import pandas as pd
import numpy as np
import os
from datetime import datetime
from config import PARCELAS, NASA_VARIABLES, ANIO_INICIO, ANIO_FIN, RAW_DIR, DB_PATH

# Configuración de API externa
NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

def construir_url(lat: float, lon: float) -> str:
    """
    Genera el endpoint para la consulta de datos diarios (Comunidad AG).
    """
    params = {
        "parameters": ",".join(NASA_VARIABLES),
        "community":  "AG",
        "longitude":  lon,
        "latitude":   lat,
        "start":      f"{ANIO_INICIO}0101",
        "end":        f"{ANIO_FIN}1231",
        "format":     "JSON",
    }
    query = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{NASA_POWER_URL}?{query}"

def descargar_datos_parcela(parcela_id: str, parcela_info: dict) -> pd.DataFrame:
    """
    Gestiona la obtención de datos mediante caché local o API requests.
    """
    archivo_raw = f"{RAW_DIR}/clima_{parcela_id}.json"
    
    if os.path.exists(archivo_raw):
        with open(archivo_raw, "r") as f:
            datos_json = json.load(f)
    else:
        url = construir_url(parcela_info["lat"], parcela_info["lon"])
        try:
            respuesta = requests.get(url, timeout=60)
            respuesta.raise_for_status()
            datos_json = respuesta.json()
            
            with open(archivo_raw, "w") as f:
                json.dump(datos_json, f)
            time.sleep(1) 
            
        except requests.exceptions.RequestException as e:
            return None

    # Mapeo de parámetros JSON a estructura tabular
    parametros = datos_json["properties"]["parameter"]
    t_max      = parametros["T2M_MAX"]
    t_min      = parametros["T2M_MIN"]
    hum_rel    = parametros["RH2M"]
    viento     = parametros["WS2M"]
    radiacion  = parametros["ALLSKY_SFC_SW_DWN"]
    lluvia     = parametros["PRECTOTCORR"]
    
    fechas = sorted(t_max.keys())
    filas = []
    
    for fecha_str in fechas:
        fecha = datetime.strptime(fecha_str, "%Y%m%d").strftime("%Y-%m-%d")
        limpiar = lambda v: None if v == -999 else v
        
        filas.append({
            "fecha":       fecha,
            "t_max":       limpiar(t_max.get(fecha_str)),
            "t_min":       limpiar(t_min.get(fecha_str)),
            "humedad_rel": limpiar(hum_rel.get(fecha_str)),
            "viento":      limpiar(viento.get(fecha_str)),
            "radiacion":   limpiar(radiacion.get(fecha_str)),
            "lluvia":      limpiar(lluvia.get(fecha_str)),
        })
    
    df = pd.DataFrame(filas)
    
    # Casting numérico e interpolación de gaps (umbral de 3 días)
    for col in ["t_max", "t_min", "humedad_rel", "viento", "radiacion", "lluvia"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].interpolate(method="linear", limit=3)
    
    return df

def calcular_et0_penman_monteith(df: pd.DataFrame, lat: float) -> pd.Series:
    """
    Implementación del modelo Penman-Monteith (FAO-56) para ET0.
    """
    T_max = df["t_max"].values
    T_min = df["t_min"].values
    T_med = (T_max + T_min) / 2
    HR    = df["humedad_rel"].values
    u2    = df["viento"].values
    Rs    = df["radiacion"].values
    
    fechas = pd.to_datetime(df["fecha"])
    J = fechas.dt.dayofyear.values 
    
    # Psicrometría y Presiones de Vapor
    es_max = 0.6108 * np.exp(17.27 * T_max / (T_max + 237.3))
    es_min = 0.6108 * np.exp(17.27 * T_min / (T_min + 237.3))
    es     = (es_max + es_min) / 2
    ea     = HR / 100 * es
    
    delta = 4098 * (0.6108 * np.exp(17.27 * T_med / (T_med + 237.3))) / (T_med + 237.3) ** 2
    gamma = 0.000665 * 101.3 # Presión estándar nivel del mar (Sinaloa)
    
    # Cálculo de Balance Energético (Radiación Neta)
    Rns = (1 - 0.23) * Rs 
    lat_rad = lat * np.pi / 180
    dr = 1 + 0.033 * np.cos(2 * np.pi * J / 365)
    delta_sol = 0.409 * np.sin(2 * np.pi * J / 365 - 1.39)
    ws = np.arccos(-np.tan(lat_rad) * np.tan(delta_sol))
    Ra = (24 * 60 / np.pi) * 0.082 * dr * (
        ws * np.sin(lat_rad) * np.sin(delta_sol) +
        np.cos(lat_rad) * np.cos(delta_sol) * np.sin(ws)
    )
    
    sigma = 4.903e-9
    Rnl = sigma * ((T_max + 273.16)**4 + (T_min + 273.16)**4) / 2 * \
          (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * Rs / (0.75 * Ra) - 0.35)
    
    Rn = Rns - Rnl
    
    # Ecuación final ET0
    numerador = 0.408 * delta * Rn + gamma * (900 / (T_med + 273)) * u2 * (es - ea)
    denominador = delta + gamma * (1 + 0.34 * u2)
    
    return pd.Series(np.maximum(numerador / denominador, 0), index=df.index, name="et0")

def guardar_clima_en_bd(parcela_id: str, df: pd.DataFrame):
    """
    Persistencia de registros climáticos y ET0 en SQLite.
    """
    conn = sqlite3.connect(DB_PATH)
    registros = []
    for _, row in df.iterrows():
        registros.append((
            parcela_id, row["fecha"], row.get("t_max"), row.get("t_min"),
            row.get("humedad_rel"), row.get("viento"), row.get("radiacion"),
            row.get("lluvia"), row.get("et0")
        ))
    
    conn.executemany("""
        INSERT OR IGNORE INTO clima_diario 
        (parcela_id, fecha, t_max, t_min, humedad_rel, viento, radiacion, lluvia, et0)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, registros)
    
    conn.commit()
    conn.close()

def descargar_todo():
    """
    Orquestador de descarga, cálculo de ET0 y persistencia por parcela.
    """
    for parcela_id, parcela_info in PARCELAS.items():
        df = descargar_datos_parcela(parcela_id, parcela_info)
        if df is not None:
            df["et0"] = calcular_et0_penman_monteith(df, parcela_info["lat"])
            guardar_clima_en_bd(parcela_id, df)

if __name__ == "__main__":
    descargar_todo()