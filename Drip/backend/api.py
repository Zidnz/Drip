# =============================================================================
# API.PY — FastAPI REST bridge para el Sistema IA de Riego
# =============================================================================
# Corre con:  uvicorn api:app --reload --port 8000
# Docs auto:  http://localhost:8000/docs
# =============================================================================

import os
import sys
import time
import math
import numpy as np
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── paths ────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS_PATH = os.path.join(ROOT, "models")
for p in [ROOT, MODELS_PATH]:
    if p not in sys.path:
        sys.path.insert(0, p)

from models.recomendador import Recomendador
from config import PARCELAS, SUELO, CLASES_RIEGO
from clima_realtime import descargar_clima_hoy

# =============================================================================
# APP
# =============================================================================

app = FastAPI(
    title="DRIP — Sistema IA de Riego · Sinaloa",
    description="API REST que expone el motor de recomendación agrícola.",
    version="1.0.0",
)

# ── CORS: permite que cualquier frontend local consuma la API ─────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # en producción, limita a tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# SERIALIZACIÓN SEGURA (numpy → tipos Python nativos)
# =============================================================================

def _limpia(obj: Any) -> Any:
    """Convierte recursivamente tipos numpy/float especiales a tipos JSON-safe."""
    if isinstance(obj, dict):
        return {k: _limpia(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_limpia(i) for i in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return round(float(obj), 6)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return _limpia(obj.tolist())
    return obj

# =============================================================================
# SINGLETON DEL RECOMENDADOR + CACHÉ SIMPLE
# =============================================================================

_recomendador: Recomendador | None = None
_cache: dict[str, dict] = {}          # {key: {"ts": float, "data": dict}}
CACHE_TTL = 300                        # 5 minutos (igual que Streamlit)


def get_recomendador() -> Recomendador:
    global _recomendador
    if _recomendador is None:
        _recomendador = Recomendador()
    return _recomendador


def _cache_get(key: str) -> dict | None:
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["data"]
    return None


def _cache_set(key: str, data: dict) -> None:
    _cache[key] = {"ts": time.time(), "data": data}

# =============================================================================
# ENDPOINTS
# =============================================================================

# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["estado"])
def raiz():
    return {
        "status": "ok",
        "sistema": "DRIP — IA de Riego · Sinaloa",
        "version": "1.0.0",
        "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ── Configuración del suelo (estática, sin caché necesaria) ──────────────────
@app.get("/suelo", tags=["config"])
def get_suelo():
    return _limpia(SUELO)


# ── Lista de parcelas ─────────────────────────────────────────────────────────
@app.get("/parcelas", tags=["parcelas"])
def get_parcelas():
    """
    Devuelve la lista de parcelas definidas en config.py.
    No llama al Recomendador ni a la BD — es sólo config estática.
    """
    resultado = []
    for pid, info in PARCELAS.items():
        resultado.append({
            "id": pid,
            "nombre": info["nombre"],
            "municipio": info["municipio"],
            "cultivo": info["cultivo"],
            "variedad": info["variedad"],
            "area_ha": info["area_ha"],
            "lat": info["lat"],
            "lon": info["lon"],
        })
    return resultado


# ── Recomendación completa de una parcela ────────────────────────────────────
@app.get("/parcela/{pid}", tags=["parcelas"])
def get_parcela(pid: str):
    """
    Retorna la recomendación completa del sistema IA para la parcela indicada.
    Incluye: humedad, decisión, lámina, sensores, clima, explicación.
    Caché: 5 minutos.
    """
    pid = pid.upper()
    if pid not in PARCELAS:
        raise HTTPException(
            status_code=404,
            detail=f"Parcela '{pid}' no existe. Válidas: {list(PARCELAS.keys())}",
        )

    cached = _cache_get(f"parcela_{pid}")
    if cached:
        return JSONResponse(content=cached)

    try:
        rec = get_recomendador()
        raw = rec.recomendar(pid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error del motor IA: {e}")

    # Enriquecer con ET₀ del clima (útil para el frontend)
    try:
        info = PARCELAS[pid]
        clima = descargar_clima_hoy(info["lat"], info["lon"], info["nombre"])
        et0 = clima.get("et0", 5.2)
    except Exception:
        et0 = 5.2

    resultado = _limpia({
        "id":                 raw["parcela"],
        "nombre":             raw["nombre"],
        "municipio":          raw["municipio"],
        "cultivo":            PARCELAS[pid]["cultivo"],
        "area_ha":            PARCELAS[pid]["area_ha"],
        "theta":              raw["theta"],
        "theta_pct":          round(raw["theta"] * 100, 1),
        "decision":           raw["decision"],
        "lamina_mm":          raw["lamina_mm"],
        "volumen_m3":         raw["volumen_m3"],
        "n_validos":          raw["n_validos"],
        "confianza":          round(raw["confianza"], 1),
        "temp_suelo_promedio":raw["temp_suelo_promedio"],
        "et0":                et0,
        "sensores":           raw["sensores"],
        "explicacion":        raw["explicacion"],
        "umbrales": {
            "umbral_pct":     round(SUELO["theta_umbral"] * 100, 1),
            "critico_pct":    round(SUELO["theta_critico"] * 100, 1),
            "fc_pct":         round(SUELO["theta_fc"] * 100, 1),
        },
        "timestamp":          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    _cache_set(f"parcela_{pid}", resultado)
    return JSONResponse(content=resultado)


# ── Sólo los sensores de una parcela (más liviano) ────────────────────────────
@app.get("/parcela/{pid}/sensores", tags=["sensores"])
def get_sensores(pid: str):
    """
    Devuelve únicamente el grid de sensores de la parcela.
    Útil para actualizar el panel de nodos sin recargar todo.
    """
    pid = pid.upper()
    if pid not in PARCELAS:
        raise HTTPException(status_code=404, detail=f"Parcela '{pid}' no existe.")

    # Reutiliza el caché completo si existe
    cached = _cache_get(f"parcela_{pid}")
    if cached:
        return JSONResponse(content={
            "id":       pid,
            "sensores": cached["sensores"],
            "n_validos":cached["n_validos"],
            "timestamp":cached["timestamp"],
        })

    try:
        rec = get_recomendador()
        raw = rec.recomendar(pid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content=_limpia({
        "id":       pid,
        "sensores": raw["sensores"],
        "n_validos":raw["n_validos"],
        "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }))


# ── Clima actual de una parcela ───────────────────────────────────────────────
@app.get("/clima/{pid}", tags=["clima"])
def get_clima(pid: str):
    """
    Devuelve temperatura, humedad, viento, ET₀ y alertas
    agroclimáticas en tiempo real (Open-Meteo).
    Caché: 5 minutos.
    """
    pid = pid.upper()
    if pid not in PARCELAS:
        raise HTTPException(status_code=404, detail=f"Parcela '{pid}' no existe.")

    cached = _cache_get(f"clima_{pid}")
    if cached:
        return JSONResponse(content=cached)

    info = PARCELAS[pid]
    try:
        clima = descargar_clima_hoy(info["lat"], info["lon"], info["nombre"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error API clima: {e}")

    resultado = _limpia({
        "id":          pid,
        "nombre":      info["nombre"],
        "municipio":   info["municipio"],
        **clima,
        "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    _cache_set(f"clima_{pid}", resultado)
    return JSONResponse(content=resultado)


# ── Vista global: todas las parcelas (para ranking y comparativa) ─────────────
@app.get("/global", tags=["parcelas"])
def get_global():
    """
    Devuelve un resumen de todas las parcelas ordenadas por humedad ascendente.
    Ideal para el widget de ranking y la gráfica comparativa del dashboard.
    Caché: 5 minutos.
    """
    cached = _cache_get("global")
    if cached:
        return JSONResponse(content=cached)

    rec = get_recomendador()
    resumen = []

    for pid in PARCELAS:
        try:
            raw = rec.recomendar(pid)
            resumen.append(_limpia({
                "id":        pid,
                "nombre":    raw["nombre"],
                "municipio": raw["municipio"],
                "cultivo":   PARCELAS[pid]["cultivo"],
                "theta":     raw["theta"],
                "theta_pct": round(raw["theta"] * 100, 1),
                "decision":  raw["decision"],
                "lamina_mm": raw["lamina_mm"],
                "n_validos": raw["n_validos"],
                "confianza": round(raw["confianza"], 1),
            }))
        except Exception as e:
            resumen.append({
                "id":    pid,
                "error": str(e),
            })

    # Ordenar por humedad ascendente (más seco primero)
    resumen.sort(key=lambda x: x.get("theta", 9))

    resultado = {
        "parcelas":  resumen,
        "total":     len(resumen),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    _cache_set("global", resultado)
    return JSONResponse(content=resultado)


# ── Invalidar caché manualmente (equivale al botón "Actualizar" de Streamlit) ─
@app.post("/cache/invalidar", tags=["admin"])
def invalidar_cache():
    """Limpia todo el caché en memoria. Útil para forzar datos frescos."""
    _cache.clear()
    return {"status": "ok", "mensaje": "Caché invalidado correctamente."}


# ── Clases de riego (útil para el frontend) ───────────────────────────────────
@app.get("/clases-riego", tags=["config"])
def get_clases_riego():
    return _limpia(CLASES_RIEGO)


# =============================================================================
# ARRANQUE DIRECTO
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
