import sqlite3
import numpy as np
from datetime import datetime
import os, sys

# Inserción de rutas para acceso a parámetros globales
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, SUELO, SENSOR_ERRORES, PARCELAS, CLASES_RIEGO

# Configuración de topología de la red por parcela
SENSORES_CONFIG = {
    "S01": {"fila": "norte",  "col": 1, "zona": "borde_NW",  "peso": 1.0},
    "S02": {"fila": "norte",  "col": 2, "zona": "borde_N",   "peso": 1.0},
    "S03": {"fila": "norte",  "col": 3, "zona": "borde_N",   "peso": 1.0},
    "S04": {"fila": "norte",  "col": 4, "zona": "borde_NE",  "peso": 1.0},
    "S05": {"fila": "centro", "col": 1, "zona": "centro_W",  "peso": 2.0},
    "S06": {"fila": "centro", "col": 2, "zona": "centro",    "peso": 2.0},
    "S07": {"fila": "centro", "col": 3, "zona": "centro",    "peso": 2.0},
    "S08": {"fila": "centro", "col": 4, "zona": "centro_E",  "peso": 2.0},
    "S09": {"fila": "sur",    "col": 1, "zona": "borde_SW",  "peso": 1.0},
    "S10": {"fila": "sur",    "col": 2, "zona": "borde_S",   "peso": 1.0},
    "S11": {"fila": "sur",    "col": 3, "zona": "borde_S",   "peso": 1.0},
    "S12": {"fila": "sur",    "col": 4, "zona": "borde_SE",  "peso": 1.0},
}

class SensorRealtime:
    """
    Motor de generación de telemetría sintética con variabilidad espacial y fallos aleatorios.
    """
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.rng = np.random.default_rng(int(datetime.now().timestamp() * 1000) % (2**32))
        self._deriva = {sid: 0.0 for sid in SENSORES_CONFIG}

    def _generar_lectura_sensor(self, sensor_id, theta_base, dia_ciclo):
        """Aplica modelos de ruido y deriva sobre la humedad teórica (BH)."""
        cfg = SENSORES_CONFIG[sensor_id]
        
        # Variabilidad espacial intrínseca del lote
        offset = {"norte": -0.005, "sur": -0.003, "centro": 0.002}
        theta_zona = np.clip(theta_base + self.rng.normal(offset[cfg["fila"]], 0.007), 
                             SUELO["theta_pwp"] * 0.9, SUELO["theta_fc"])
        
        # Calcular theta_real base (siempre presente)
        theta_real = round(theta_zona, 4)

        # Simulación de fallos críticos (Dato faltante o Spikes)
        if self.rng.random() < SENSOR_ERRORES["prob_faltante"]:
            return {
                "sensor_id": sensor_id, 
                "zona": cfg["zona"], 
                "peso": cfg["peso"],
                "theta_real": theta_real,  # ← AGREGADO: siempre presente
                "theta_sensor": None, 
                "valido": False, 
                "tipo_error": "faltante"
            }

        if self.rng.random() < SENSOR_ERRORES["prob_spike"]:
            magnitud = float(self.rng.choice(SENSOR_ERRORES["spike_magnitud"]))
            return {
                "sensor_id": sensor_id, 
                "zona": cfg["zona"], 
                "peso": cfg["peso"],
                "theta_real": theta_real,  # ← AGREGADO: siempre presente
                "theta_sensor": round(theta_zona + magnitud, 4), 
                "valido": False, 
                "tipo_error": "spike"
            }

        # Simulación de degradación (Ruido gaussiano y Deriva temporal)
        ruido = self.rng.normal(0, SENSOR_ERRORES["ruido_std"])
        self._deriva[sensor_id] = 0.0 if dia_ciclo % SENSOR_ERRORES["reset_calibracion"] == 0 else self._deriva[sensor_id] + SENSOR_ERRORES["deriva_diaria"]
        
        theta_s = np.clip(theta_zona + ruido + self._deriva[sensor_id], 0.01, SUELO["theta_sat"] + 0.02)
        
        return {
            "sensor_id": sensor_id, 
            "zona": cfg["zona"], 
            "peso": cfg["peso"],
            "theta_real": theta_real,  # ← AGREGADO: siempre presente
            "theta_sensor": round(theta_s, 4),
            "valido": True, 
            "tipo_error": "ninguno" if abs(ruido) < 0.005 else "ruido"
        }

    def generar_lectura_parcela(self, parcela_id, fecha):
        """Agrega las lecturas de los 12 nodos y calcula el estado hídrico actual."""
        row = self.conn.execute("SELECT theta_real, dia_ciclo FROM lecturas_sensor WHERE parcela_id=? AND fecha=?", (parcela_id, fecha)).fetchone()
        theta_base, dia_ciclo = (row[0], row[1]) if row else (SUELO["theta_umbral"] + 0.02, 65)

        lecturas = {sid: self._generar_lectura_sensor(sid, theta_base, dia_ciclo) for sid in SENSORES_CONFIG}
        
        # Agregación ponderada (Solo sensores válidos)
        validos = [l for l in lecturas.values() if l["valido"]]
        n_validos = len(validos)
        peso_acum = sum(l["peso"] for l in validos)
        theta_prom = round(sum(l["theta_sensor"] * l["peso"] for l in validos) / peso_acum, 4) if peso_acum > 0 else theta_base

        # Clasificación de alarmas por zona crítica
        criticas = [l["zona"] for l in validos if l["theta_sensor"] < SUELO["theta_critico"]]

        # Calcular clase_final basada en humedad (para compatibilidad)
        if theta_prom < SUELO["theta_critico"]:
            clase_final = 2  # Urgente
        elif theta_prom < SUELO["theta_umbral"]:
            clase_final = 1  # Preventivo
        else:
            clase_final = 0  # No regar

        return {
            "parcela_id": parcela_id, 
            "fecha": fecha, 
            "theta_promedio": theta_prom,
            "theta_bh": theta_base,  # ← AGREGADO: balance hídrico
            "confianza_pct": round(n_validos / 12 * 100, 1), 
            "n_sensores_validos": n_validos,
            "alerta_zona_critica": len(criticas) > 0, 
            "zonas_criticas": criticas,
            "clase_final": clase_final,  # ← AGREGADO: clase por humedad
            "modo_operacion": "normal" if n_validos >= 9 else "degradado" if n_validos >= 6 else "asistido",
            "sensores": lecturas
        }

    def cerrar(self):
        self.conn.close()