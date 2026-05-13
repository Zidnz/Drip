"""
DRIP — Constantes agronómicas y del sistema
Valores basados en agricultura de Sinaloa, México
"""

# ─── Cultivos disponibles ──────────────────────────────────────────────────────
CULTIVOS_SINALOA = ["maíz", "chile", "frijol", "papa", "jitomate", "garbanzo", "trigo"]

# ─── Tipos de suelo ───────────────────────────────────────────────────────────
TIPOS_SUELO = {
    "arcilloso": {"capacidad_campo": 0.40, "punto_marchitez": 0.20, "retencion": "alta"},
    "franco":    {"capacidad_campo": 0.30, "punto_marchitez": 0.12, "retencion": "media"},
    "arenoso":   {"capacidad_campo": 0.18, "punto_marchitez": 0.08, "retencion": "baja"},
    "limoso":    {"capacidad_campo": 0.35, "punto_marchitez": 0.15, "retencion": "media-alta"},
}

# ─── Sistemas de riego ────────────────────────────────────────────────────────
SISTEMAS_RIEGO = {
    "goteo":      {"eficiencia": 0.92, "litros_hora_ha": 2500},
    "aspersión":  {"eficiencia": 0.78, "litros_hora_ha": 4500},
    "gravedad":   {"eficiencia": 0.55, "litros_hora_ha": 8000},
    "microaspersión": {"eficiencia": 0.85, "litros_hora_ha": 3200},
}

# ─── Coeficientes de cultivo (Kc) ─────────────────────────────────────────────
# Basados en FAO-56 adaptados a Sinaloa
KC_CULTIVOS = {
    "maíz":     {"inicial": 0.30, "medio": 1.20, "final": 0.60, "dias": 120},
    "chile":    {"inicial": 0.35, "medio": 1.05, "final": 0.90, "dias": 150},
    "frijol":   {"inicial": 0.40, "medio": 1.15, "final": 0.35, "dias": 90},
    "papa":     {"inicial": 0.45, "medio": 1.15, "final": 0.75, "dias": 110},
    "jitomate": {"inicial": 0.45, "medio": 1.15, "final": 0.80, "dias": 130},
    "garbanzo": {"inicial": 0.30, "medio": 1.00, "final": 0.35, "dias": 100},
    "trigo":    {"inicial": 0.30, "medio": 1.15, "final": 0.30, "dias": 130},
}

# ─── Rangos óptimos por cultivo ───────────────────────────────────────────────
RANGOS_HUMEDAD = {
    "maíz":     {"min": 55, "max": 75, "critico": 40},
    "chile":    {"min": 60, "max": 80, "critico": 45},
    "frijol":   {"min": 50, "max": 70, "critico": 35},
    "papa":     {"min": 65, "max": 85, "critico": 50},
    "jitomate": {"min": 60, "max": 80, "critico": 45},
    "garbanzo": {"min": 45, "max": 65, "critico": 30},
    "trigo":    {"min": 50, "max": 70, "critico": 35},
}

# ─── Clima Sinaloa — promedios mensuales ──────────────────────────────────────
CLIMA_SINALOA = {
    1:  {"temp_max": 26, "temp_min": 12, "lluvia_mm": 18,  "humedad_rel": 62},
    2:  {"temp_max": 28, "temp_min": 13, "lluvia_mm": 12,  "humedad_rel": 60},
    3:  {"temp_max": 31, "temp_min": 16, "lluvia_mm": 8,   "humedad_rel": 55},
    4:  {"temp_max": 34, "temp_min": 19, "lluvia_mm": 5,   "humedad_rel": 52},
    5:  {"temp_max": 37, "temp_min": 22, "lluvia_mm": 10,  "humedad_rel": 58},
    6:  {"temp_max": 35, "temp_min": 26, "lluvia_mm": 120, "humedad_rel": 78},
    7:  {"temp_max": 33, "temp_min": 26, "lluvia_mm": 220, "humedad_rel": 85},
    8:  {"temp_max": 33, "temp_min": 26, "lluvia_mm": 200, "humedad_rel": 84},
    9:  {"temp_max": 33, "temp_min": 24, "lluvia_mm": 130, "humedad_rel": 80},
    10: {"temp_max": 31, "temp_min": 20, "lluvia_mm": 40,  "humedad_rel": 70},
    11: {"temp_max": 28, "temp_min": 15, "lluvia_mm": 20,  "humedad_rel": 64},
    12: {"temp_max": 26, "temp_min": 12, "lluvia_mm": 22,  "humedad_rel": 63},
}

# ─── Prioridades de alertas ───────────────────────────────────────────────────
ALERT_PRIORITY = {"critica": 1, "alta": 2, "media": 3, "baja": 4}

# ─── Estados de parcela ───────────────────────────────────────────────────────
ESTADOS_PARCELA = ["activa", "en_descanso", "en_preparacion", "cosechada"]

# ─── Tipos de sensor ──────────────────────────────────────────────────────────
TIPOS_SENSOR = ["humedad_suelo", "temperatura", "conductividad_electrica", "flujo_agua", "clima"]

# ─── Rendimientos esperados (ton/ha) ─────────────────────────────────────────
RENDIMIENTOS = {
    "maíz":     {"min": 6.0,  "max": 12.0, "promedio": 9.0},
    "chile":    {"min": 15.0, "max": 35.0, "promedio": 25.0},
    "frijol":   {"min": 1.5,  "max": 3.0,  "promedio": 2.0},
    "papa":     {"min": 25.0, "max": 45.0, "promedio": 35.0},
    "jitomate": {"min": 40.0, "max": 80.0, "promedio": 60.0},
    "garbanzo": {"min": 1.0,  "max": 2.5,  "promedio": 1.8},
    "trigo":    {"min": 4.0,  "max": 7.0,  "promedio": 5.5},
}
