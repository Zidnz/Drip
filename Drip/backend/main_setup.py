import sqlite3
import pandas as pd
from datetime import datetime

# =============================================================================
# ORQUESTADOR DE CONFIGURACIÓN INICIAL
# =============================================================================

def main():
    """
    Ejecuta el flujo completo de inicialización del sistema:
    BD -> Carga de Activos -> Ingesta de Clima -> Verificación.
    """
    print(f"Iniciando configuración del sistema: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Inicialización de persistencia y catálogo de parcelas
    from database import crear_base_de_datos, insertar_parcelas
    crear_base_de_datos()
    insertar_parcelas()

    # 2. Ingesta de series temporales climáticas (NASA POWER)
    from nasa_power import descargar_todo
    descargar_todo()

    # 3. Validación de integridad de datos
    generar_reporte_verificacion()

    print(f"Configuración finalizada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def generar_reporte_verificacion():
    """
    Realiza auditoría de datos en la BD para asegurar consistencia agronómica.
    """
    from config import DB_PATH, PARCELAS, SUELO
    conn = sqlite3.connect(DB_PATH)

    # Auditoría de activos (Parcelas)
    df_parcelas = pd.read_sql_query("SELECT * FROM parcelas", conn)
    for _, row in df_parcelas.iterrows():
        print(f"Parcela: {row['parcela_id']} | Area: {row['area_ha']} ha | Suelo: {row['theta_umbral']} (umbral)")

    # Auditoría de series climáticas y ET0
    df_clima = pd.read_sql_query("""
        SELECT 
            c.parcela_id,
            p.nombre,
            COUNT(*) as n_dias,
            ROUND(AVG(c.et0), 2) as et0_media,
            SUM(CASE WHEN c.et0 IS NULL THEN 1 ELSE 0 END) as nulos
        FROM clima_diario c
        JOIN parcelas p ON c.parcela_id = p.parcela_id
        GROUP BY c.parcela_id
    """, conn)

    for _, row in df_clima.iterrows():
        # Verificación de rango técnico ET0 para la región (Sinaloa)
        status = "OK"
        if row["et0_media"] is not None:
            if not (2 <= row["et0_media"] <= 14):
                status = "FUERA_DE_RANGO"
        
        print(f"ID: {row['parcela_id']} | Días: {row['n_dias']} | ET0 Media: {row['et0_media']} | Status: {status}")

    # Resumen de cobertura temporal
    total_registros = conn.execute("SELECT COUNT(*) FROM clima_diario").fetchone()[0]
    periodo = conn.execute(
        "SELECT MIN(substr(fecha,1,4)), MAX(substr(fecha,1,4)) FROM clima_diario"
    ).fetchone()
    
    print("-" * 30)
    print(f"Total registros: {total_registros}")
    print(f"Periodo: {periodo[0]} - {periodo[1]}")
    print(f"Propiedades Suelo: θ_fc={SUELO['theta_fc']}, θ_pwp={SUELO['theta_pwp']}")
    print("-" * 30)

    conn.close()

if __name__ == "__main__":
    main()