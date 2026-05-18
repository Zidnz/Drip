import sqlite3
import pandas as pd
import numpy as np
import joblib
import os
import sys
import time

from datetime import datetime, timedelta

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    DB_PATH,
    PARCELAS,
    SUELO,
    CLASES_RIEGO
)

from clima_realtime import descargar_clima_hoy
from aletas import enviar_telegram   # 🔥 NUEVO

# =============================================================================
# MODELOS
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RF_MODEL_PATH = os.path.join(BASE_DIR, "rf_model.pkl")
IF_MODEL_PATH = os.path.join(BASE_DIR, "if_model.pkl")
IF_SCALER_PATH = os.path.join(BASE_DIR, "if_scaler.pkl")


# =============================================================================
# GENERADOR EXPLICACIÓN
# =============================================================================

def generar_explicacion(
    modo,
    clase_final,
    theta_usado,
    etc_dia,
    lluvia_3d,
    confianza_pct,
    n_validos,
    zonas_criticas,
    clima_actual,
    pred_48h,
    fuga_detectada,
    prioridad,
    deficit_mm=0
):
    return f"""
🌾 SISTEMA IA AGRÍCOLA

🌱 Humedad: {theta_usado:.1%}
🌤️ ET0: {clima_actual['et0']} mm/día
📉 Déficit: {deficit_mm:.1f} mm

🔮 3 días: {pred_48h['theta_3d']:.1%}
🔮 7 días: {pred_48h['theta_7d']:.1%}

📌 Prioridad: {prioridad}
🤖 Confianza: {confianza_pct}%
"""


# =============================================================================
# CLASE PRINCIPAL
# =============================================================================

class Recomendador:

    def __init__(self):

        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)

        self.rf_model = joblib.load(RF_MODEL_PATH) if os.path.exists(RF_MODEL_PATH) else None
        self.if_model = joblib.load(IF_MODEL_PATH) if os.path.exists(IF_MODEL_PATH) else None
        self.if_scaler = joblib.load(IF_SCALER_PATH) if os.path.exists(IF_SCALER_PATH) else None

        from sensor import SensorRealtime
        self.sensor = SensorRealtime()

        # 🔥 NUEVO: control anti-spam
        self.ultima_alerta = {}

    # =====================================================
    # PREDICCIÓN FUTURA
    # =====================================================

    def predecir_futuro(self, theta_actual, et0, lluvia=0):

        theta = theta_actual
        historial = []

        for _ in range(7):

            etc = et0 * 0.85
            theta = theta + ((lluvia * 0.8 - etc) / 900)

            historial.append(theta)

        estado = "normal"
        horas = 168

        for i, t in enumerate(historial):

            if t < SUELO["theta_critico"]:
                return {
                    "estado": "critico",
                    "horas": (i + 1) * 24,
                    "theta_3d": historial[2],
                    "theta_7d": historial[6]
                }

            elif t < SUELO["theta_umbral"]:
                return {
                    "estado": "preventivo",
                    "horas": (i + 1) * 24,
                    "theta_3d": historial[2],
                    "theta_7d": historial[6]
                }

        return {
            "estado": estado,
            "horas": horas,
            "theta_3d": historial[2],
            "theta_7d": historial[6]
        }

    # =====================================================
    # PRIORIDAD
    # =====================================================

    def calcular_prioridad(self, theta):

        deficit = SUELO["theta_fc"] - theta

        if deficit > 0.12:
            return 1
        elif deficit > 0.08:
            return 2
        elif deficit > 0.05:
            return 3
        return 4

    # =====================================================
    # MOTOR PRINCIPAL
    # =====================================================

    def recomendar(self, parcela_id, fecha):

        lectura = self.sensor.generar_lectura_parcela(parcela_id, fecha)

        info = PARCELAS[parcela_id]

        clima = descargar_clima_hoy(info["lat"], info["lon"], info["nombre"])

        theta = lectura["theta_bh"]

        pred = self.predecir_futuro(theta, clima["et0"], clima.get("lluvia", 0))

        prioridad = self.calcular_prioridad(theta)

        clase_final = 2 if theta < SUELO["theta_critico"] else 1 if theta < SUELO["theta_umbral"] else 0

        lamina_mm = max(0, (SUELO["theta_fc"] - theta) * 900)

        lamina_mm = min(lamina_mm, 80)

        # =====================================================
        # 🔥 ALERTAS TELEGRAM
        # =====================================================

        mensaje = None

        if clase_final == 2:

            mensaje = f"""
🚨 ALERTA CRÍTICA

📍 {info['nombre']}
🌱 Humedad: {theta:.1%}
💧 Riego urgente: {lamina_mm:.1f} mm
⚠️ Estrés hídrico severo
"""

        elif clase_final == 1:

            mensaje = f"""
⚠️ ALERTA PREVENTIVA

📍 {info['nombre']}
🌱 Humedad: {theta:.1%}
💧 Programar riego
"""

        elif pred["estado"] == "critico":

            mensaje = f"""
🔮 ALERTA PREDICTIVA

📍 {info['nombre']}
⏳ En {pred['horas']}h habrá déficit crítico
"""

        # =====================================================
        # ANTI-SPAM
        # =====================================================

        ahora = datetime.now()
        ultima = self.ultima_alerta.get(parcela_id)

        if ultima:

            if (ahora - ultima).total_seconds() < 3600:
                mensaje = None

        if mensaje:
            enviar_telegram(mensaje)
            self.ultima_alerta[parcela_id] = ahora

        # =====================================================
        # RESULTADO FINAL
        # =====================================================

        return {
            "parcela": info["nombre"],
            "theta": theta,
            "prioridad": prioridad,
            "prediccion": pred,
            "lamina_mm": lamina_mm
        }

    # =====================================================
    # TODAS LAS PARCELAS
    # =====================================================

    def recomendar_todas_parcelas(self):

        resultados = []

        for p in PARCELAS:

            r = self.recomendar(p, datetime.now().strftime("%Y-%m-%d"))
            resultados.append(r)

            print(f"{r['parcela']} → Prioridad {r['prioridad']}")

        return resultados

    # =====================================================
    # CIERRE
    # =====================================================

    def cerrar(self):
        self.sensor.cerrar()
        self.conn.close()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":

    rec = Recomendador()

    try:
        while True:

            rec.recomendar_todas_parcelas()

            time.sleep(300)

    except KeyboardInterrupt:
        rec.cerrar()