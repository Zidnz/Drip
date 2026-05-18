import sqlite3
import os
from datetime import datetime
from config import DB_PATH

# =============================================================================
# GESTIÓN DE PERSISTENCIA (SQLITE)
# =============================================================================

def crear_base_de_datos():
    """
    Inicializa el esquema de la base de datos y define las tablas del sistema.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Habilitar integridad referencial
    cursor.execute("PRAGMA foreign_keys = ON")

    # ==================== TABLA PARCELAS ====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parcelas (
            parcela_id    TEXT PRIMARY KEY,
            nombre        TEXT NOT NULL,
            municipio     TEXT NOT NULL,
            zona          TEXT NOT NULL,
            lat           REAL NOT NULL,
            lon           REAL NOT NULL,
            area_ha       REAL NOT NULL,
            cultivo       TEXT NOT NULL,
            variedad      TEXT NOT NULL,
            fecha_siembra TEXT NOT NULL,
            theta_fc      REAL NOT NULL,
            theta_pwp     REAL NOT NULL,
            theta_umbral  REAL NOT NULL
        )
    """)

    # ==================== TABLA CLIMA DIARIO ====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clima_diario (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            parcela_id    TEXT NOT NULL,
            fecha         TEXT NOT NULL,
            t_max         REAL,
            t_min         REAL,
            humedad_rel   REAL,
            viento        REAL,
            radiacion     REAL,
            lluvia        REAL,
            et0           REAL,
            FOREIGN KEY (parcela_id) REFERENCES parcelas(parcela_id),
            UNIQUE(parcela_id, fecha)
        )
    """)

    # ==================== TABLA LECTURAS SENSOR ====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lecturas_sensor (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            parcela_id      TEXT NOT NULL,
            fecha           TEXT NOT NULL,
            dia_ciclo       INTEGER,
            etapa           TEXT,
            kc              REAL,
            theta_real      REAL,
            theta_sensor    REAL,
            tipo_error      TEXT DEFAULT 'ninguno',
            deficit_hidrico REAL,
            clase_hoy       INTEGER,
            clase_t3        INTEGER,
            FOREIGN KEY (parcela_id) REFERENCES parcelas(parcela_id),
            UNIQUE(parcela_id, fecha)
        )
    """)

    # ==================== TABLA EVENTOS DE RIEGO ====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos_riego (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            parcela_id      TEXT NOT NULL,
            fecha           TEXT NOT NULL,
            lamina_mm       REAL NOT NULL,
            lamina_m3       REAL NOT NULL,
            tipo_riego      TEXT,
            trigger_clase   INTEGER,
            theta_antes     REAL,
            theta_esperada  REAL,
            FOREIGN KEY (parcela_id) REFERENCES parcelas(parcela_id)
        )
    """)

    # ==================== TABLA LOG DE DECISIONES ====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_decisiones (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp         TEXT NOT NULL,
            parcela_id        TEXT NOT NULL,
            fecha             TEXT NOT NULL,
            sensor_valido     INTEGER,
            tipo_anomalia     TEXT,
            clase_bh          INTEGER,
            clase_rf          INTEGER,
            clase_final       INTEGER NOT NULL,
            confianza         TEXT NOT NULL,
            modo_operacion    TEXT NOT NULL,
            theta_usado       REAL,
            et0_dia           REAL,
            kc_dia            REAL,
            etc_dia           REAL,
            explicacion       TEXT,
            FOREIGN KEY (parcela_id) REFERENCES parcelas(parcela_id)
        )
    """)

    # ==================== TABLA COSTOS ERP ====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS erp_costos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha           TEXT NOT NULL,
            parcela_id      TEXT NOT NULL,
            m3_agua         REAL,
            horas_bomba     REAL,
            kwh_energia     REAL,
            costo_energia   REAL,
            costo_agua      REAL,
            costo_mano_obra REAL,
            costo_total     REAL,
            FOREIGN KEY (parcela_id) REFERENCES parcelas(parcela_id)
        )
    """)

    conn.commit()
    conn.close()
    print(f"✅ Base de datos inicializada correctamente ({DB_PATH})")


def insertar_parcelas():
    """
    Inserta o actualiza las parcelas desde la configuración en config.py
    """
    from config import PARCELAS, SUELO

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for pid, p in PARCELAS.items():
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO parcelas 
                (parcela_id, nombre, municipio, zona, lat, lon, area_ha, 
                 cultivo, variedad, fecha_siembra, theta_fc, theta_pwp, theta_umbral)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pid,
                p.get("nombre"),
                p.get("municipio"),
                p.get("zona", "Sin definir"),           # Valor por defecto
                p.get("lat"),
                p.get("lon"),
                p.get("area_ha"),
                p.get("cultivo"),
                p.get("variedad"),
                p.get("fecha_siembra"),
                SUELO.get("theta_fc"),
                SUELO.get("theta_pwp"),
                SUELO.get("theta_umbral")
            ))
            print(f"   → Parcela {pid} ({p.get('nombre')}) actualizada")
        except Exception as e:
            print(f"❌ Error al insertar parcela {pid}: {e}")

    conn.commit()
    conn.close()
    print(f"✅ {len(PARCELAS)} parcelas insertadas/actualizadas correctamente.")


def get_connection():
    """Retorna una conexión con foreign keys activadas."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ejecutar_query(query, params=None):
    """Ejecuta consultas SELECT y devuelve resultados como lista de diccionarios."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = [dict(row) for row in cursor.fetchall()]
        return results
    finally:
        conn.close()


# =============================================================================
if __name__ == "__main__":
    print(f"Iniciando configuración de base de datos - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    crear_base_de_datos()
    insertar_parcelas()
    print("🎉 Configuración completada.")