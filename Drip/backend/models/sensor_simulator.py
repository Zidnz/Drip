# =============================================================================
# models/sensor_simulator.py — Simulador de Sensores de Humedad del Suelo
# =============================================================================
# QUÉ HACE:
#   Toma la humedad "real" calculada por el balance hídrico (θ_real) y le
#   agrega errores realistas para simular lo que leería un sensor físico.
#
# POR QUÉ LO HACEMOS ASÍ:
#   En campo real, un sensor capacitivo (como el EC-5 o CS655) no mide θ
#   perfectamente. Tiene: ruido eléctrico, deriva de calibración, fallas
#   intermitentes y lecturas aberrantes. Estos errores son exactamente lo
#   que el Isolation Forest debe detectar.
#
# 4 TIPOS DE ERRORES SIMULADOS:
#   1. Ruido gaussiano   → Variación aleatoria de ±1% (σ=0.010)
#   2. Deriva acumulada  → El sensor se descalibra 0.03%/día
#   3. Spike (valor aberrante) → 3% de probabilidad por día
#   4. Dato faltante (NaN)    → 5% de probabilidad por día
#
# REFERENCIA:
#   Chandola, V., Banerjee, A., & Kumar, V. (2009).
#   Anomaly detection: A survey. ACM Computing Surveys, 41(3).
# =============================================================================

import sqlite3
import pandas as pd
import numpy as np
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, PARCELAS, SUELO, SENSOR_ERRORES, SEED_BASE


class SensorSimulator:
    """
    Simulador de sensor de humedad del suelo para las 5 parcelas de Sinaloa.

    Lee θ_real de SQLite (calculado por el Balance Hídrico) y genera
    θ_sensor con errores realistas, guardando el resultado en la misma tabla.
    """

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.errores = SENSOR_ERRORES
        print("Simulador de Sensores iniciado")
        print(f"  Errores: ruido σ={self.errores['ruido_std']} | "
              f"deriva {self.errores['deriva_diaria']}/día | "
              f"spike p={self.errores['prob_spike']} | "
              f"faltante p={self.errores['prob_faltante']}")

    def simular_sensor(self, parcela_id: str, prob_faltante_override: float = None) -> pd.DataFrame:
        """
        Genera lecturas de sensor para UNA parcela completa.

        Proceso por cada día:
          1. Leer θ_real del Balance Hídrico (SQLite)
          2. Aplicar ruido gaussiano (siempre presente)
          3. Aplicar deriva acumulada (crece con el tiempo)
          4. Con probabilidad p_spike → generar valor aberrante
          5. Con probabilidad p_faltante → reemplazar con NaN

        El resultado se guarda en SQLite (columna theta_sensor y tipo_error).

        prob_faltante_override: Si se pasa, reemplaza la probabilidad de
            datos faltantes del config (útil para el escenario de falla masiva).
        """
        prob_faltante = prob_faltante_override or self.errores["prob_faltante"]

        # Cargar los registros del balance hídrico para esta parcela
        df = pd.read_sql_query("""
            SELECT id, parcela_id, fecha, dia_ciclo, theta_real
            FROM lecturas_sensor
            WHERE parcela_id = ?
            ORDER BY fecha
        """, self.conn, params=(parcela_id,))

        if df.empty:
            print(f"  ✗ {parcela_id}: sin datos. Correr balance_hidrico.py primero.")
            return pd.DataFrame()

        # Semilla reproducible por parcela (misma parcela → mismos errores)
        semilla = SEED_BASE + hash(parcela_id) % 1000
        rng = np.random.default_rng(semilla)

        # Acumuladores
        deriva_acum  = 0.0   # Deriva acumulada del sensor
        registros_actualizados = []
        filas_resultado = []

        for idx, row in df.iterrows():
            theta_real = row["theta_real"]
            dia        = row["dia_ciclo"]
            tipo_error = "ninguno"
            theta_sensor = theta_real  # Empezamos con el valor real

            # ── Error 1: Ruido gaussiano ──────────────────────────────────
            # Siempre presente — modela la imprecisión de la electrónica
            ruido = rng.normal(0, self.errores["ruido_std"])
            theta_sensor += ruido

            # ── Error 2: Deriva acumulada ─────────────────────────────────
            # El sensor se descalibra gradualmente con el tiempo.
            # Cada 'reset_calibracion' días se recalibra (deriva vuelve a 0).
            reset_cada = self.errores["reset_calibracion"]
            if dia % reset_cada == 0 and dia > 0:
                deriva_acum = 0.0  # Recalibración del sensor
            else:
                deriva_acum += self.errores["deriva_diaria"]

            theta_sensor += deriva_acum

            # Si solo hubo ruido/deriva, el error es "ruido" o "deriva"
            if abs(ruido) > 0.005:
                tipo_error = "ruido"
            if abs(deriva_acum) > 0.015:
                tipo_error = "deriva"

            # ── Error 3: Spike (valor aberrante) ─────────────────────────
            # Con probabilidad p_spike el sensor reporta un valor absurdo.
            # Esto simula: cortocircuito, interferencia electromagnética,
            # agua en los conectores, vibración mecánica.
            if rng.random() < self.errores["prob_spike"]:
                # El spike puede ser hacia arriba o hacia abajo
                magnitud = rng.choice(self.errores["spike_magnitud"])
                theta_sensor = theta_real + magnitud
                tipo_error = "spike"

            # ── Error 4: Dato faltante (NaN) ──────────────────────────────
            # Con probabilidad p_faltante el sensor no envía datos.
            # Esto simula: pérdida de señal, batería descargada, cable cortado.
            if rng.random() < prob_faltante:
                theta_sensor = None  # NaN en la base de datos
                tipo_error = "faltante"

            # ── Límites físicos del sensor ─────────────────────────────────
            # Un sensor real no puede reportar fuera de su rango de operación.
            # Si el spike lleva el valor a >60% o <0%, lo marcamos como spike
            # (el Isolation Forest lo detectará igual).
            if theta_sensor is not None:
                # Los spikes extremos son los más fáciles de detectar
                if theta_sensor > SUELO["theta_sat"] + 0.05:
                    tipo_error = "spike"  # Sobre saturación
                elif theta_sensor < 0:
                    tipo_error = "spike"  # Negativo es imposible físicamente
                # Redondear a 4 decimales para realismo
                theta_sensor = round(theta_sensor, 4)

            registros_actualizados.append((theta_sensor, tipo_error, int(row["id"])))
            filas_resultado.append({
                "parcela_id":   row["parcela_id"],
                "fecha":        row["fecha"],
                "dia_ciclo":    dia,
                "theta_real":   theta_real,
                "theta_sensor": theta_sensor,
                "tipo_error":   tipo_error,
                "deriva_acum":  round(deriva_acum, 5),
            })

        # Actualizar la tabla lecturas_sensor con los valores del sensor
        self.conn.executemany("""
            UPDATE lecturas_sensor
            SET theta_sensor = ?, tipo_error = ?
            WHERE id = ?
        """, registros_actualizados)
        self.conn.commit()

        return pd.DataFrame(filas_resultado)

    def resumen_errores(self, parcela_id: str) -> dict:
        """
        Calcula estadísticas de errores para una parcela.
        Útil para verificar que la simulación es realista.
        """
        df = pd.read_sql_query("""
            SELECT tipo_error, COUNT(*) as n
            FROM lecturas_sensor
            WHERE parcela_id = ?
            GROUP BY tipo_error
        """, self.conn, params=(parcela_id,))

        total = df["n"].sum()
        resumen = {"parcela_id": parcela_id, "total_dias": total}
        for _, row in df.iterrows():
            resumen[row["tipo_error"]] = {
                "n":   int(row["n"]),
                "pct": round(row["n"] / total * 100, 1)
            }
        return resumen

    def simular_todas(self, prob_faltante_override: float = None):
        """Simula sensores para las 5 parcelas."""
        print(f"\nSimulando sensores para {len(PARCELAS)} parcelas...")
        if prob_faltante_override:
            print(f"  Modo falla masiva: p_faltante={prob_faltante_override}")

        for parcela_id, info in PARCELAS.items():
            print(f"\n  [{parcela_id}] {info['nombre']}")
            df = self.simular_sensor(parcela_id, prob_faltante_override)

            if df.empty:
                continue

            res = self.resumen_errores(parcela_id)
            print(f"    Total días: {res['total_dias']}")
            for tipo in ["ninguno", "ruido", "deriva", "spike", "faltante"]:
                if tipo in res:
                    print(f"    {tipo:<10} {res[tipo]['n']:>5} días "
                          f"({res[tipo]['pct']}%)")

    def cerrar(self):
        self.conn.close()


def main():
    print("\n" + "="*60)
    print("  SIMULADOR DE SENSORES — MAÍZ EN SINALOA")
    print("="*60)

    sim = SensorSimulator()
    sim.simular_todas()

    # Verificación rápida de sanidad
    print("\n" + "="*60)
    print("  VERIFICACIÓN DE SANIDAD")
    print("="*60)
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN theta_sensor IS NULL THEN 1 ELSE 0 END) as faltantes,
               SUM(CASE WHEN tipo_error = 'spike' THEN 1 ELSE 0 END) as spikes
        FROM lecturas_sensor
    """).fetchone()
    print(f"  Total registros:   {row[0]:,}")
    print(f"  Datos faltantes:   {row[1]:,} ({row[1]/row[0]*100:.1f}%)")
    print(f"  Spikes detectados: {row[2]:,} ({row[2]/row[0]*100:.1f}%)")
    conn.close()

    print("\n  ✓ Simulación de sensores completada")
    print("  Siguiente paso: python models/isolation_forest.py")

    sim.cerrar()


if __name__ == "__main__":
    main()
