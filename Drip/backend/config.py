import os

# =============================================================================
# CONFIGURACIÓN GLOBAL DEL SISTEMA IA AGRÍCOLA
# =============================================================================

# =============================================================================
# 1. DEFINICIÓN DE PARCELAS (SINALOA)
# =============================================================================

PARCELAS = {

    "P01": {
        "nombre": "Valle del Fuerte Norte",
        "municipio": "Los Mochis",
        "lat": 25.78,
        "lon": -109.07,
        "area_ha": 15.0,
        "cultivo": "Maíz",
        "variedad": "H-438",
        "fecha_siembra": "04-15",
    },

    "P02": {
        "nombre": "Valle de Guasave",
        "municipio": "Guasave",
        "lat": 25.57,
        "lon": -108.47,
        "area_ha": 10.5,
        "cultivo": "Maíz",
        "variedad": "DK-2038",
        "fecha_siembra": "04-20",
    },

    "P03": {
        "nombre": "Valle de Culiacán",
        "municipio": "Culiacán",
        "lat": 24.80,
        "lon": -107.39,
        "area_ha": 12.0,
        "cultivo": "Maíz",
        "variedad": "H-317",
        "fecha_siembra": "04-25",
    },

    "P04": {
        "nombre": "Valle de Navolato",
        "municipio": "Navolato",
        "lat": 24.77,
        "lon": -107.70,
        "area_ha": 8.0,
        "cultivo": "Maíz",
        "variedad": "H-317",
        "fecha_siembra": "04-22",
    },

    "P05": {
        "nombre": "Valle de Escuinapa",
        "municipio": "Escuinapa",
        "lat": 22.85,
        "lon": -105.80,
        "area_ha": 9.5,
        "cultivo": "Maíz",
        "variedad": "VS-536",
        "fecha_siembra": "04-10",
    },
}

# =============================================================================
# 2. PROPIEDADES DEL SUELO
# =============================================================================

SUELO = {

    "tipo": "Franco-arcilloso",

    # Capacidad de campo
    "theta_fc": 0.32,

    # Punto de marchitez
    "theta_pwp": 0.17,

    # Saturación
    "theta_sat": 0.46,

    # Agua disponible
    "theta_aw": 0.15,

    # Agotamiento permisible
    "p_maiz": 0.50,

    # Umbral para iniciar riego
    "theta_umbral": 0.245,

    # Estrés hídrico severo
    "theta_critico": 0.192
}

# =============================================================================
# 3. CICLO FENOLÓGICO DEL MAÍZ
# =============================================================================

CICLO_DIAS = 130

KC_ETAPAS = [

    {
        "nombre": "Inicial",
        "dia_inicio": 0,
        "dia_fin": 20,
        "kc_inicio": 0.30,
        "kc_fin": 0.30,
        "zr_inicio": 0.30,
        "zr_fin": 0.30,
    },

    {
        "nombre": "Desarrollo",
        "dia_inicio": 21,
        "dia_fin": 55,
        "kc_inicio": 0.30,
        "kc_fin": 1.20,
        "zr_inicio": 0.30,
        "zr_fin": 0.90,
    },

    {
        "nombre": "Media",
        "dia_inicio": 56,
        "dia_fin": 105,
        "kc_inicio": 1.20,
        "kc_fin": 1.20,
        "zr_inicio": 0.90,
        "zr_fin": 1.00,
    },

    {
        "nombre": "Final",
        "dia_inicio": 106,
        "dia_fin": 130,
        "kc_inicio": 1.20,
        "kc_fin": 0.35,
        "zr_inicio": 1.00,
        "zr_fin": 1.00,
    },
]

# =============================================================================
# 4. VARIABLES NASA POWER
# =============================================================================

NASA_VARIABLES = [

    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "WS2M",
    "ALLSKY_SFC_SW_DWN",
    "PRECTOTCORR",
]

ANIO_INICIO = 2021
ANIO_FIN = 2025

# =============================================================================
# 5. CONFIGURACIÓN DE SENSORES (VERSIÓN ESTABLE)
# =============================================================================

SENSOR_ERRORES = {

    # =========================================================
    # RUIDO NORMAL DEL SENSOR
    # =========================================================

    # Variación pequeña y realista
    "ruido_std": 0.002,

    # =========================================================
    # DERIVA DEL SENSOR
    # =========================================================

    # Descalibración muy lenta
    "deriva_diaria": 0.00005,

    # =========================================================
    # SPIKES / PICOS ANÓMALOS
    # =========================================================

    # Muy raros
    "prob_spike": 0.003,

    # Magnitud moderada
    "spike_magnitud": [0.03, -0.03],

    # =========================================================
    # DATOS FALTANTES
    # =========================================================

    # Muy pocos fallos
    "prob_faltante": 0.01,

    # =========================================================
    # RECALIBRACIÓN
    # =========================================================

    # Recalibración semanal
    "reset_calibracion": 7,
}

SEED_BASE = 42

# =============================================================================
# 6. ESTADOS DE RIEGO
# =============================================================================

CLASES_RIEGO = {

    0: {
        "nombre": "No regar",
        "color": "#2E7D32",
        "emoji": "✓"
    },

    1: {
        "nombre": "Regar pronto",
        "color": "#E65100",
        "emoji": "⚠"
    },

    2: {
        "nombre": "Regar urgente",
        "color": "#C62828",
        "emoji": "✗"
    },
}

# =============================================================================
# 7. ESCENARIOS DE SIMULACIÓN
# =============================================================================

ESCENARIOS = {

    # =========================================================
    # OPERACIÓN NORMAL
    # =========================================================

    "normal": {

        "et0_factor": 1.0,

        "lluvia_factor": 1.0,

        # Red estable
        "prob_faltante": 0.01
    },

    # =========================================================
    # ESCENARIO DE SEQUÍA
    # =========================================================

    "sequia": {

        "et0_factor": 1.30,

        "lluvia_factor": 0.50,

        # Ligero aumento de fallos
        "prob_faltante": 0.02
    },

    # =========================================================
    # FALLA PARCIAL DE SENSORES
    # =========================================================

    "falla_sensores": {

        "et0_factor": 1.0,

        "lluvia_factor": 1.0,

        # Fallo parcial realista
        "prob_faltante": 0.25
    },
}

# =============================================================================
# 8. GESTIÓN DE DIRECTORIOS
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DB_DIR = os.path.join(PROJECT_ROOT, "db")
DATA_DIR = os.path.join(DB_DIR, "data")

RAW_DIR = os.path.join(DATA_DIR, "raw")

PROC_DIR = os.path.join(DATA_DIR, "processed")

DB_PATH = os.path.join(DATA_DIR, "riego.db")

# =============================================================================
# CREACIÓN AUTOMÁTICA DE DIRECTORIOS
# =============================================================================

for directory in [DATA_DIR, RAW_DIR, PROC_DIR]:

    if not os.path.exists(directory):

        os.makedirs(directory, exist_ok=True)
