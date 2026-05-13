"""
Configuración agronómica del sistema.
Valores basados en FAO-56 y datos climáticos de Sinaloa, México.
"""

# ---------------------------------------------------------------------------
# CULTIVOS  (Kc según FAO-56, rendimientos en ton/ha, duración etapas en días)
# ---------------------------------------------------------------------------
CULTIVOS = {
    "maiz": {
        "nombre_comun": "Maíz",
        "nombre_cientifico": "Zea mays",
        "kc": {"inicial": 0.30, "desarrollo": 0.75, "media": 1.20, "final": 0.35},
        "etapas_dias": {"inicial": 25, "desarrollo": 35, "media": 45, "final": 30},  # total ~135
        "rendimiento_ton_ha": {"min": 6.0, "max": 12.0, "promedio": 9.0},
        "humedad_optima_pct": 65,        # % humedad volumétrica objetivo
        "humedad_estres_pct": 40,        # umbral estrés hídrico
        "profundidad_raiz_m": 1.0,
        "color_dashboard": "#22c55e",    # green-500
    },
    "frijol": {
        "nombre_comun": "Frijol",
        "nombre_cientifico": "Phaseolus vulgaris",
        "kc": {"inicial": 0.40, "desarrollo": 0.70, "media": 1.15, "final": 0.25},
        "etapas_dias": {"inicial": 20, "desarrollo": 30, "media": 35, "final": 20},  # total ~105
        "rendimiento_ton_ha": {"min": 1.2, "max": 2.5, "promedio": 1.8},
        "humedad_optima_pct": 60,
        "humedad_estres_pct": 38,
        "profundidad_raiz_m": 0.6,
        "color_dashboard": "#a16207",    # yellow-700
    },
    "chile": {
        "nombre_comun": "Chile",
        "nombre_cientifico": "Capsicum annuum",
        "kc": {"inicial": 0.60, "desarrollo": 0.85, "media": 1.05, "final": 0.90},
        "etapas_dias": {"inicial": 30, "desarrollo": 40, "media": 50, "final": 30},  # total ~150
        "rendimiento_ton_ha": {"min": 15.0, "max": 35.0, "promedio": 25.0},
        "humedad_optima_pct": 70,
        "humedad_estres_pct": 45,
        "profundidad_raiz_m": 0.7,
        "color_dashboard": "#ef4444",    # red-500
    },
    "papa": {
        "nombre_comun": "Papa",
        "nombre_cientifico": "Solanum tuberosum",
        "kc": {"inicial": 0.50, "desarrollo": 0.80, "media": 1.15, "final": 0.75},
        "etapas_dias": {"inicial": 25, "desarrollo": 30, "media": 45, "final": 30},  # total ~130
        "rendimiento_ton_ha": {"min": 20.0, "max": 45.0, "promedio": 32.0},
        "humedad_optima_pct": 75,
        "humedad_estres_pct": 50,
        "profundidad_raiz_m": 0.5,
        "color_dashboard": "#f97316",    # orange-500
    },
    "jitomate": {
        "nombre_comun": "Jitomate",
        "nombre_cientifico": "Solanum lycopersicum",
        "kc": {"inicial": 0.60, "desarrollo": 0.80, "media": 1.15, "final": 0.70},
        "etapas_dias": {"inicial": 30, "desarrollo": 40, "media": 45, "final": 25},  # total ~140
        "rendimiento_ton_ha": {"min": 50.0, "max": 120.0, "promedio": 85.0},
        "humedad_optima_pct": 72,
        "humedad_estres_pct": 48,
        "profundidad_raiz_m": 0.8,
        "color_dashboard": "#f43f5e",    # rose-500
    },
}

# ---------------------------------------------------------------------------
# TIPOS DE SUELO (propiedades hídricas)
# ---------------------------------------------------------------------------
TIPOS_SUELO = {
    "franco_arcilloso": {
        "capacidad_campo_pct": 35,       # % humedad vol. a capacidad de campo
        "punto_marchitez_pct": 18,       # % humedad vol. punto marchitez permanente
        "densidad_aparente": 1.35,       # g/cm³
        "conductividad_hidraulica": 1.2, # mm/h
        "descripcion": "Franco arcilloso (predominante en Sinaloa valle)",
    },
    "franco_limoso": {
        "capacidad_campo_pct": 32,
        "punto_marchitez_pct": 15,
        "densidad_aparente": 1.30,
        "conductividad_hidraulica": 2.5,
        "descripcion": "Franco limoso",
    },
    "franco_arenoso": {
        "capacidad_campo_pct": 22,
        "punto_marchitez_pct": 10,
        "densidad_aparente": 1.55,
        "conductividad_hidraulica": 8.0,
        "descripcion": "Franco arenoso (zonas costeras)",
    },
}

# ---------------------------------------------------------------------------
# SISTEMAS DE RIEGO
# ---------------------------------------------------------------------------
SISTEMAS_RIEGO = {
    "goteo": {
        "eficiencia": 0.92,
        "costo_m3": 0.85,          # MXN por m³
        "caudal_lh_ha": 2500,      # litros/hora por hectárea típico
    },
    "aspersion": {
        "eficiencia": 0.78,
        "costo_m3": 1.10,
        "caudal_lh_ha": 5000,
    },
    "gravedad": {
        "eficiencia": 0.55,
        "costo_m3": 0.45,
        "caudal_lh_ha": 12000,
    },
    "microaspersion": {
        "eficiencia": 0.85,
        "costo_m3": 0.95,
        "caudal_lh_ha": 3500,
    },
}

# ---------------------------------------------------------------------------
# CLIMA DE SINALOA (parámetros mensuales promedio, estación Culiacán)
# FAO datos climáticos + CONAGUA SMN
# ---------------------------------------------------------------------------
# Índice 0=Enero, 11=Diciembre
CLIMA_SINALOA_MENSUAL = {
    "temp_max_c":     [27, 29, 32, 36, 38, 38, 36, 36, 35, 33, 30, 27],
    "temp_min_c":     [11, 12, 14, 18, 21, 24, 24, 24, 23, 19, 14, 11],
    "humedad_rel_pct":[55, 52, 50, 48, 52, 68, 78, 80, 78, 68, 60, 57],
    "precip_mm":      [18, 10, 5,  3,  5,  40, 90, 110, 75, 30, 15, 20],
    "radiacion_mj_m2":[14, 17, 20, 23, 25, 24, 22, 21, 20, 18, 15, 13],  # MJ/m²/día
    "viento_m_s":     [2.1,2.3,2.5,2.8,2.6,2.4,2.2,2.0,2.0,2.1,2.0,2.0],
    # Elevación Culiacán: 60 msnm → presión atmosférica ≈ 100.8 kPa
    "elevacion_msnm": 60,
}

# ---------------------------------------------------------------------------
# PARCELAS DEL SISTEMA (5 parcelas demo)
# ---------------------------------------------------------------------------
PARCELAS_CONFIG = [
    {
        "id": "P001",
        "nombre": "Parcela Norte A",
        "cultivo": "maiz",
        "area_ha": 8.5,
        "tipo_suelo": "franco_arcilloso",
        "sistema_riego": "goteo",
        "fecha_siembra_mes": 11,   # Noviembre (ciclo O-I Sinaloa)
        "sensores_count": 3,
    },
    {
        "id": "P002",
        "nombre": "Parcela Sur B",
        "cultivo": "jitomate",
        "area_ha": 4.2,
        "tipo_suelo": "franco_limoso",
        "sistema_riego": "goteo",
        "fecha_siembra_mes": 10,   # Octubre
        "sensores_count": 4,
    },
    {
        "id": "P003",
        "nombre": "Parcela Central C",
        "cultivo": "chile",
        "area_ha": 6.0,
        "tipo_suelo": "franco_arcilloso",
        "sistema_riego": "microaspersion",
        "fecha_siembra_mes": 10,
        "sensores_count": 3,
    },
    {
        "id": "P004",
        "nombre": "Bloque Este D",
        "cultivo": "papa",
        "area_ha": 5.5,
        "tipo_suelo": "franco_limoso",
        "sistema_riego": "aspersion",
        "fecha_siembra_mes": 11,
        "sensores_count": 2,
    },
    {
        "id": "P005",
        "nombre": "Bloque Oeste E",
        "cultivo": "frijol",
        "area_ha": 7.0,
        "tipo_suelo": "franco_arenoso",
        "sistema_riego": "gravedad",
        "fecha_siembra_mes": 11,
        "sensores_count": 2,
    },
]

# ---------------------------------------------------------------------------
# PARÁMETROS DE SIMULACIÓN
# ---------------------------------------------------------------------------
SIM_CONFIG = {
    "año_inicio": 2025,
    "dias_simulacion": 365,
    "seed_random": 42,              # reproducibilidad
    "ruido_temp_std": 2.0,          # °C desviación estándar sobre media mensual
    "ruido_hr_std": 5.0,            # % HR
    "ruido_viento_std": 0.4,        # m/s
    "prob_lluvia_multiplicador": 1.0,
    # Riego automático: se activa cuando humedad < umbral_riego_pct
    "umbral_riego_deficit_pct": 0.55,  # regar cuando humedad < 55% de capacidad campo
    "lecturas_por_dia": 4,          # frecuencia sensor (cada 6h)
}
