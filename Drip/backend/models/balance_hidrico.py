import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys, os

# Configuración de rutas para módulos internos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DB_PATH, PARCELAS, SUELO, KC_ETAPAS, CICLO_DIAS, CLASES_RIEGO
)

# =============================================================================
# LÓGICA AGRONÓMICA (FAO-56)
# =============================================================================

def obtener_kc_y_etapa(dia_ciclo: int) -> tuple:
    """
    Calcula el coeficiente de cultivo (Kc) y profundidad radicular (Zr) interpolados.
    Basado en etapas fenológicas de la Tabla 12, FAO-56.
    """
    dia_ciclo = np.clip(dia_ciclo, 0, CICLO_DIAS)

    for etapa in KC_ETAPAS:
        if etapa["dia_inicio"] <= dia_ciclo <= etapa["dia_fin"]:
            duracion = etapa["dia_fin"] - etapa["dia_inicio"]
            fraccion = (dia_ciclo - etapa["dia_inicio"]) / duracion if duracion > 0 else 0

            # Interpolación lineal entre límites de etapa
            kc = etapa["kc_inicio"] + fraccion * (etapa["kc_fin"] - etapa["kc_inicio"])
            zr = etapa["zr_inicio"] + fraccion * (etapa["zr_fin"] - etapa["zr_inicio"])

            return round(kc, 4), round(zr, 4), etapa["nombre"]

    return KC_ETAPAS[-1]["kc_fin"], KC_ETAPAS[-1]["zr_fin"], KC_ETAPAS[-1]["nombre"]

def clasificar_estado_hidrico(theta: float) -> int:
    """
    Categorización del estado de humedad según umbrales de config.py.
    0: Confort | 1: Riego Preventivo | 2: Estrés Crítico.
    """
    if theta is None or np.isnan(theta):
        return 1

    if theta >= SUELO["theta_umbral"]:
        return 0
    elif theta >= SUELO["theta_critico"]:
        return 1
    else:
        return 2

def calcular_lamina_riego(theta_actual: float, zr: float) -> float:
    """
    Calcula el volumen de reposición (mm) para alcanzar Capacidad de Campo.
    Limitado por capacidad operativa (0-80mm).
    """
    lamina = (SUELO["theta_fc"] - theta_actual) * zr * 1000
    return round(max(0, min(lamina, 80)), 1)

# =============================================================================
# MOTOR DE SIMULACIÓN DE BALANCE HÍDRICO
# =============================================================================

class BalanceHidrico:
    """
    Implementación del modelo de balance de masa hídrica en suelo para Maíz.
    """
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def _obtener_clima_parcela(self, parcela_id: str, anio: int) -> pd.DataFrame:
        """Extrae series temporales climáticas de SQLite para el ciclo de cultivo."""
        info_parcela = PARCELAS[parcela_id]
        mes, dia = info_parcela["fecha_siembra"].split("-")
        fecha_inicio = f"{anio}-{mes}-{dia}"
        
        fecha_fin_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d") + timedelta(days=CICLO_DIAS - 1)
        fecha_fin = fecha_fin_dt.strftime("%Y-%m-%d")

        return pd.read_sql_query("""
            SELECT fecha, et0, lluvia FROM clima_diario
            WHERE parcela_id = ? AND fecha >= ? AND fecha <= ? ORDER BY fecha
        """, self.conn, params=(parcela_id, fecha_inicio, fecha_fin))

    def simular_temporada(self, parcela_id: str, anio: int, 
                          theta_inicial: float = None, 
                          et0_factor: float = 1.0, 
                          lluvia_factor: float = 1.0) -> pd.DataFrame:
        """
        Simulación diaria del balance hídrico bajo escenarios climáticos.
        Fórmula: θ(t+1) = θ(t) + (Lluvia_ef + Riego - ETc) / (Zr * 1000)
        """
        df_clima = self._obtener_clima_parcela(parcela_id, anio)
        if df_clima.empty: return pd.DataFrame()

        theta = theta_inicial if theta_inicial is not None else SUELO["theta_fc"] * 0.85
        filas = []

        for i, row in df_clima.iterrows():
            dia_ciclo = i + 1
            kc, zr, etapa = obtener_kc_y_etapa(dia_ciclo)
            
            # Cálculo de demanda y oferta hídrica
            et0_dia = (row["et0"] or 5.0) * et0_factor
            etc_dia = et0_dia * kc
            lluvia_ef = (row["lluvia"] or 0.0) * lluvia_factor * 0.80

            # Trigger de riego por déficit
            riego_mm = calcular_lamina_riego(theta, zr) if theta < SUELO["theta_umbral"] else 0.0

            # Actualización de estado (Balance de masa)
            delta_theta = (lluvia_ef + riego_mm - etc_dia) / (zr * 1000)
            theta_nuevo = np.clip(theta + delta_theta, SUELO["theta_pwp"] * 0.90, SUELO["theta_fc"])

            filas.append({
                "fecha": row["fecha"], "dia_ciclo": dia_ciclo, "etapa": etapa,
                "kc": kc, "zr": zr, "et0": round(et0_dia, 3), "etc": round(etc_dia, 3),
                "lluvia": round(row["lluvia"] or 0.0, 2), "riego_mm": riego_mm,
                "theta_real": round(theta_nuevo, 4), "deficit": round(SUELO["theta_fc"] - theta_nuevo, 4),
                "clase_hoy": clasificar_estado_hidrico(theta_nuevo)
            })
            theta = theta_nuevo

        df_res = pd.DataFrame(filas)
        # Cálculo de Target (t+3) para modelos predictivos
        df_res["clase_t3"] = df_res["clase_hoy"].shift(-3).fillna(df_res["clase_hoy"]).astype(int)
        
        return df_res

    def guardar_resultados(self, parcela_id: str, anio: int, df: pd.DataFrame):
        """Persistencia de resultados de simulación y eventos de riego en SQLite."""
        if df.empty: return 0

        registros = []
        for _, row in df.iterrows():
            registros.append((
                parcela_id, row["fecha"], int(row["dia_ciclo"]), row["etapa"],
                row["kc"], row["theta_real"], None, "ninguno", row["deficit"],
                int(row["clase_hoy"]), int(row["clase_t3"])
            ))

        self.conn.executemany("""
            INSERT OR REPLACE INTO lecturas_sensor 
            (parcela_id, fecha, dia_ciclo, etapa, kc, theta_real, 
             theta_sensor, tipo_error, deficit_hidrico, clase_hoy, clase_t3)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, registros)

        # Registro de láminas aplicadas
        riegos = df[df["riego_mm"] > 0]
        eventos = []
        for _, row in riegos.iterrows():
            eventos.append((
                parcela_id, row["fecha"], row["riego_mm"], 
                round(row["riego_mm"] * PARCELAS[parcela_id]["area_ha"] * 10, 1),
                "preventivo" if row["clase_hoy"] == 1 else "urgente",
                int(row["clase_hoy"]), 
                round(row["theta_real"] - row["riego_mm"]/(row["zr"]*1000), 4), 
                row["theta_real"]
            ))

        if eventos:
            self.conn.executemany("""
                INSERT OR IGNORE INTO eventos_riego 
                (parcela_id, fecha, lamina_mm, lamina_m3, tipo_riego, trigger_clase, theta_antes, theta_esperada)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, eventos)

        self.conn.commit()
        return len(registros)

    def correr_todas_las_parcelas(self, escenario: str = "normal", et0_factor: float = 1.0, lluvia_factor: float = 1.0):
        """Batch processing de balance hídrico para todo el catálogo de parcelas y años."""
        anios = [int(r[0]) for r in self.conn.execute("SELECT DISTINCT substr(fecha,1,4) FROM clima_diario").fetchall()]
        
        for parcela_id in PARCELAS:
            for anio in anios:
                df = self.simular_temporada(parcela_id, anio, et0_factor=et0_factor, lluvia_factor=lluvia_factor)
                if not df.empty and escenario == "normal":
                    self.guardar_resultados(parcela_id, anio, df)

    def calcular_kpis(self, parcela_id: str = None) -> pd.DataFrame:
        """Cálculo de eficiencia hídrica comparativa vs riego tradicional."""
        query = """
            SELECT l.parcela_id, p.nombre, p.area_ha, substr(l.fecha,1,4) as anio,
                   COUNT(*) as dias, SUM(CASE WHEN l.theta_real < ? THEN 1 ELSE 0 END) as dias_deficit,
                   (SELECT SUM(e.lamina_mm) FROM eventos_riego e 
                    WHERE e.parcela_id = l.parcela_id AND substr(e.fecha,1,4) = substr(l.fecha,1,4)) as agua_mm
            FROM lecturas_sensor l JOIN parcelas p ON l.parcela_id = p.parcela_id
        """
        params = [SUELO["theta_umbral"]]
        if parcela_id:
            query += " WHERE l.parcela_id = ?"
            params.append(parcela_id)
        query += " GROUP BY l.parcela_id, anio"

        df = pd.read_sql_query(query, self.conn, params=params)
        if df.empty: return df

        # Benchmark: Riego tradicional (~1114mm/ciclo)
        agua_trad_mm = (130 / 7) * 60
        df["ish_pct"] = (df["dias_deficit"] / df["dias"] * 100).round(1)
        df["agua_m3"] = (df["agua_mm"].fillna(0) * df["area_ha"] * 10).round(0)
        df["ahorro_pct"] = ((agua_trad_mm - df["agua_mm"].fillna(0)) / agua_trad_mm * 100).round(1)
        
        return df

    def cerrar(self):
        self.conn.close()

if __name__ == "__main__":
    bh = BalanceHidrico()
    bh.correr_todas_las_parcelas()
    kpis = bh.calcular_kpis()
    bh.cerrar()