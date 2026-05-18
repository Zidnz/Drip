# =============================================================================
# IMPORTS
# =============================================================================

import sqlite3
import pandas as pd
import numpy as np
import joblib
import os
import sys
import time

from datetime import datetime

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from config import (
    DB_PATH,
    PARCELAS,
    SUELO,
    CLASES_RIEGO
)

# =============================================================================
# CLIMA REALTIME
# =============================================================================

from clima_realtime import descargar_clima_hoy

# =============================================================================
# MONGODB
# =============================================================================

from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "riego_sinaloa"
MONGO_COLLECTION = "lecturas_sensores"

# =============================================================================
# MODELOS IA
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RF_MODEL_PATH = os.path.join(
    BASE_DIR,
    "rf_model.pkl"
)

IF_MODEL_PATH = os.path.join(
    BASE_DIR,
    "if_model.pkl"
)

IF_SCALER_PATH = os.path.join(
    BASE_DIR,
    "if_scaler.pkl"
)

# =============================================================================
# EXPLICACIÓN NLP
# =============================================================================

def generar_explicacion(
    clase_final,
    theta_usado,
    etc_dia,
    confianza_pct,
    n_validos,
    clima_actual,
    pred_48h,
    fuga_detectada,
    prioridad,
    deficit_mm=0,
    sensores_stats=None,
    temp_suelo_promedio=None
):

    # =========================================================================
    # ESTADO RED
    # =========================================================================

    if n_validos >= 10:
        estado_red = (
            f"📡 RED DE SENSORES: Operativa "
            f"({n_validos}/12 sensores válidos)"
        )
    elif n_validos >= 6:
        estado_red = (
            f"📡 RED DE SENSORES: Parcial "
            f"({n_validos}/12 sensores válidos)"
        )
    else:
        estado_red = (
            f"📡 RED DE SENSORES: Degradada "
            f"({n_validos}/12 sensores válidos)"
        )

    # =========================================================================
    # CLIMA AMBIENTAL
    # =========================================================================

    clima_txt = (
        f"🌤 CLIMA AMBIENTAL:\n"
        f"   • Temperatura del aire: {clima_actual['temperatura']}°C\n"
        f"   • Humedad ambiental: {clima_actual['humedad']}%\n"
        f"   • Velocidad del viento: {clima_actual['viento']} m/s\n"
        f"   • ET0 (evapotranspiración): {clima_actual['et0']:.2f} mm/día"
    )

    # =========================================================================
    # DECISIÓN
    # =========================================================================

    if clase_final == 0:
        cuerpo = (
            f"💧 DECISIÓN: No regar\n"
            f"   • Humedad actual: {theta_usado:.1%}\n"
            f"   • Estado del suelo: Estable\n"
            f"   • ETc del cultivo: {etc_dia:.2f} mm/día"
        )
    elif clase_final == 1:
        cuerpo = (
            f"⚠ DECISIÓN: Regar pronto\n"
            f"   • Humedad actual: {theta_usado:.1%}\n"
            f"   • Déficit hídrico: {deficit_mm:.1f} mm\n"
            f"   • Plazo recomendado: 24-48 horas"
        )
    else:
        cuerpo = (
            f"🔴 DECISIÓN: Regar URGENTE\n"
            f"   • Humedad actual: {theta_usado:.1%}\n"
            f"   • Déficit hídrico: {deficit_mm:.1f} mm\n"
            f"   • Acción requerida: Inmediata"
        )

    # =========================================================================
    # PROYECCIÓN HÍDRICA
    # =========================================================================

    if pred_48h["estado"] == "critico":
        futuro = (
            f"📈 PROYECCIÓN:\n"
            f"   • Estado: Déficit crítico\n"
            f"   • Tiempo estimado: {pred_48h['horas']} horas"
        )
    elif pred_48h["estado"] == "preventivo":
        futuro = (
            f"📈 PROYECCIÓN:\n"
            f"   • Estado: Estrés moderado\n"
            f"   • Tiempo estimado: {pred_48h['horas']} horas"
        )
    else:
        futuro = (
            f"📈 PROYECCIÓN:\n"
            f"   • Estado: Condiciones estables\n"
            f"   • Autonomía: >7 días"
        )

    # =========================================================================
    # CLIMA DEL SUELO (SENSORES)
    # =========================================================================
    
    if sensores_stats:
        # Cantidad de sensores
        sensores_cantidad = f"🖧 SENSORES OPERATIVOS: {sensores_stats['validos']}/12"
        
        # Sensores no válidos
        if sensores_stats['no_validos'] > 0:
            sensores_cantidad += f" ({sensores_stats['no_validos']} fuera de servicio)"
        
        # Humedad mínima y máxima
        sensores_rango = (
            f"   • Rango de humedad: "
            f"{sensores_stats['min_theta']:.1%} - {sensores_stats['max_theta']:.1%}"
        )
        
        # Variabilidad
        sensores_variabilidad = (
            f"   • Variabilidad de humedad: ±{sensores_stats['std_theta']:.2%}"
        )
        
        # Temperatura del suelo
        if temp_suelo_promedio:
            temp_suelo_txt = (
                f"   • 🌡 Temperatura del suelo: {temp_suelo_promedio:.1f}°C"
            )
            # Comparar con temperatura del aire
            diff_temp = temp_suelo_promedio - clima_actual['temperatura']
            if diff_temp < 0:
                temp_suelo_txt += f" (más fresco que el aire por {abs(diff_temp):.1f}°C)"
            elif diff_temp > 0:
                temp_suelo_txt += f" (más cálido que el aire por {diff_temp:.1f}°C)"
            else:
                temp_suelo_txt += f" (igual que el aire)"
        else:
            temp_suelo_txt = "   • 🌡 Temperatura del suelo: No disponible"
        
        # Sensores críticos (por debajo del umbral)
        if sensores_stats['criticos'] > 0:
            sensores_criticos = (
                f"⚠ • SENSORES CRÍTICOS: {sensores_stats['criticos']} "
                f"con humedad < {SUELO['theta_critico']:.1%}"
            )
        else:
            sensores_criticos = "✓ • No hay sensores en estado crítico"
        
        # Zona más seca (si hay datos de ubicación)
        if sensores_stats.get('zona_mas_seca'):
            sensores_zona = (
                f"📍 • Zona más seca: {sensores_stats['zona_mas_seca']} "
                f"({sensores_stats['zona_humedad']:.1%})"
            )
        else:
            sensores_zona = ""
        
        # Combinar toda la información
        sensores_txt = (
            f"{sensores_cantidad}\n"
            f"{sensores_rango}\n"
            f"{sensores_variabilidad}\n"
            f"{temp_suelo_txt}\n"
            f"{sensores_criticos}"
        )
        
        if sensores_zona:
            sensores_txt += f"\n{sensores_zona}"
            
    else:
        sensores_txt = f"🖧 SENSORES: {n_validos}/12 operativos"
        if temp_suelo_promedio:
            sensores_txt += f"\n   • 🌡 Temperatura del suelo: {temp_suelo_promedio:.1f}°C"

    # =========================================================================
    # PRIORIDAD Y CONFIANZA
    # =========================================================================

    prioridad_txt = f"🎯 PRIORIDAD DE RIEGO: {prioridad}"
    confianza_txt = f"✓ CONFIANZA DEL SISTEMA: {confianza_pct:.1f}%"

    # =========================================================================
    # ARMAR RESPUESTA COMPLETA
    # =========================================================================

    return (
        f"{estado_red}\n\n"
        f"{clima_txt}\n\n"
        f"{cuerpo}\n\n"
        f"{futuro}\n\n"
        f"{sensores_txt}\n\n"
        f"{prioridad_txt} | {confianza_txt}"
    )

# =============================================================================
# SENSOR REALTIME
# =============================================================================

class SensorRealtime:

    def __init__(self):

        self.client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        self.db = self.client[MONGO_DB]

        self.col = self.db[MONGO_COLLECTION]

        print("MongoDB conectado correctamente")

    # =========================================================================
    # OBTENER LECTURA
    # =========================================================================

    def generar_lectura_parcela(
        self,
        parcela_id
    ):

        docs = list(

            self.col.find({

                "parcela_id": parcela_id

            }).sort(

                "timestamp",
                -1

            ).limit(12)
        )

        sensores = {}
        suma = 0.0
        n_validos = 0
        zonas_criticas = []
        temperaturas_suelo = []

        for d in docs:

            sensor_id = d.get("sensor_id")

            theta_sensor = round(
                d.get("valor_reportado", 0) / 100,
                4
            )

            theta_real = round(
                d.get("valor_real", 0) / 100,
                4
            )

            valido = not d.get(
                "es_anomalia",
                False
            )
            
            # Leer temperatura del suelo
            temp_suelo = d.get("temp_suelo", None)

            sensores[sensor_id] = {

                "theta_sensor": theta_sensor,
                "theta_real": theta_real,
                "valido": valido,
                "temp_suelo": temp_suelo
            }

            if valido:

                suma += theta_sensor
                n_validos += 1
                
                # Agregar temperatura si existe
                if temp_suelo is not None:
                    temperaturas_suelo.append(temp_suelo)

            if theta_sensor < SUELO["theta_critico"]:

                zonas_criticas.append(sensor_id)

        # =========================================================================
        # SI NO HAY DATOS
        # =========================================================================

        if len(docs) == 0:

            return {

                "sin_datos": True,
                "sensores": {},
                "theta_ponderado": SUELO["theta_fc"],
                "n_validos": 0,
                "zonas_criticas": [],
                "temp_suelo_promedio": None
            }

        # =========================================================================
        # THETA PROMEDIO
        # =========================================================================

        if n_validos > 0:
            theta_prom = round(suma / n_validos, 4)
            temp_suelo_prom = round(sum(temperaturas_suelo) / len(temperaturas_suelo), 1) if temperaturas_suelo else None
        else:
            theta_prom = SUELO["theta_fc"]
            temp_suelo_prom = None

        return {

            "sin_datos": False,
            "sensores": sensores,
            "theta_ponderado": theta_prom,
            "n_validos": n_validos,
            "zonas_criticas": zonas_criticas,
            "temp_suelo_promedio": temp_suelo_prom
        }

    # =========================================================================
    # CERRAR
    # =========================================================================

    def cerrar(self):

        self.client.close()

# =============================================================================
# RECOMENDADOR
# =============================================================================

class Recomendador:

    def __init__(self):

        self.conn = sqlite3.connect(
            DB_PATH,
            check_same_thread=False
        )

        self.rf_model = None

        self.if_model = None

        self.if_scaler = None

        if os.path.exists(RF_MODEL_PATH):

            self.rf_model = joblib.load(
                RF_MODEL_PATH
            )

            print("Random Forest cargado")

        if os.path.exists(IF_MODEL_PATH):

            self.if_model = joblib.load(
                IF_MODEL_PATH
            )

            self.if_scaler = joblib.load(
                IF_SCALER_PATH
            )

            print("Isolation Forest cargado")

        self.sensor = SensorRealtime()
        
        # Configuración de profundidad de raíces (en mm)
        self.profundidad_raices_mm = 300  # 30 cm para cultivos como maíz, trigo

    # =========================================================================
    # PREDICCIÓN FUTURA (CORREGIDA)
    # =========================================================================

    def predecir_futuro(
        self,
        theta_actual,
        et0
    ):
        """
        Predice la evolución de la humedad del suelo en los próximos 7 días.
        
        Args:
            theta_actual: Humedad actual (% en decimal, ej: 0.42 = 42%)
            et0: Evapotranspiración de referencia (mm/día)
        
        Returns:
            dict: Estado y horas hasta déficit crítico
        """
        
        theta = theta_actual
        historial = []
        
        # Convertir ET0 a ETc (cultivo específico)
        # Kc = 0.85 para cultivos en desarrollo
        kc = 0.85
        
        # Profundidad del suelo que las raíces pueden explorar (mm)
        # Convertir a mm de agua por punto porcentual de humedad
        # 1% de humedad en 300mm de suelo = 3mm de agua
        mm_por_porcentaje = self.profundidad_raices_mm / 100
        
        for dia in range(1, 8):  # 7 días
            
            etc = et0 * kc  # ETc en mm/día
            
            # Convertir pérdida de mm a cambio en porcentaje de humedad
            perdida_porcentaje = etc / mm_por_porcentaje / 100
            
            # Aplicar pérdida
            theta = theta - perdida_porcentaje
            
            historial.append(theta)
            
            # Verificar estado crítico (punto de marchitez permanente)
            if theta < SUELO["theta_critico"]:
                horas = max(24, dia * 24)  # Mínimo 24 horas
                return {
                    "estado": "critico",
                    "horas": horas,
                    "theta_final": theta
                }
            
            # Verificar estado preventivo (umbral de riego)
            elif theta < SUELO["theta_umbral"]:
                horas = max(24, dia * 24)
                return {
                    "estado": "preventivo",
                    "horas": horas,
                    "theta_final": theta
                }
        
        # Si después de 7 días no hay déficit
        return {
            "estado": "normal",
            "horas": 168,  # 7 días
            "theta_final": theta
        }

    # =========================================================================
    # PRIORIDAD
    # =========================================================================

    def calcular_prioridad(
        self,
        theta
    ):

        deficit = (
            SUELO["theta_fc"] - theta
        )

        if deficit > 0.12:

            return 1  # Urgente

        elif deficit > 0.08:

            return 2  # Alta

        elif deficit > 0.04:

            return 3  # Media

        return 4  # Baja

    # =========================================================================
    # CALCULAR DÉFICIT
    # =========================================================================
    
    def calcular_deficit_mm(self, theta):
        """
        Calcula el déficit hídrico en mm
        """
        deficit_porcentaje = max(0, SUELO["theta_umbral"] - theta)
        mm_por_porcentaje = self.profundidad_raices_mm / 100
        deficit_mm = deficit_porcentaje * mm_por_porcentaje * 100
        return deficit_mm

    # =========================================================================
    # RECOMENDAR
    # =========================================================================

    def recomendar(
        self,
        parcela_id
    ):

        lectura = self.sensor.generar_lectura_parcela(
            parcela_id
        )

        info = PARCELAS[parcela_id]

        clima_actual = descargar_clima_hoy(
            info["lat"],
            info["lon"],
            info["nombre"]
        )

        theta = lectura["theta_ponderado"]

        n_validos = lectura["n_validos"]

        confianza = (
            n_validos / 12
        ) * 100

        etc = clima_actual["et0"] * 0.85
        
        # Obtener temperatura del suelo
        temp_suelo_promedio = lectura.get("temp_suelo_promedio")

        pred = self.predecir_futuro(
            theta,
            clima_actual["et0"]
        )

        prioridad = self.calcular_prioridad(
            theta
        )

        # =========================================================================
        # DECISIÓN
        # =========================================================================

        if theta < SUELO["theta_critico"]:

            clase_final = 2  # Crítico

        elif theta < SUELO["theta_umbral"]:

            clase_final = 1  # Preventivo

        else:

            clase_final = 0  # Normal

        # =========================================================================
        # LÁMINA DE RIEGO
        # =========================================================================

        if clase_final > 0:

            # Calcular lámina necesaria para llegar a capacidad de campo
            deficit_porcentaje = SUELO["theta_fc"] - theta
            mm_por_porcentaje = self.profundidad_raices_mm / 100
            lamina_mm = round(
                min(
                    deficit_porcentaje * mm_por_porcentaje * 100,
                    80  # Máximo 80 mm por riego
                ),
                1
            )

        else:

            lamina_mm = 0.0

        # =========================================================================
        # DÉFICIT PARA EXPLICACIÓN
        # =========================================================================
        
        deficit_mm = self.calcular_deficit_mm(theta)

        # =========================================================================
        # CALCULAR ESTADÍSTICAS COMPLETAS DE SENSORES
        # =========================================================================
        
        sensores_validos = []
        sensores_todos = []
        sensores_criticos_ids = []
        zonas_humedad = {}  # Para identificar zonas más secas
        
        for sensor_id, s in lectura["sensores"].items():
            theta_val = s["theta_sensor"]
            sensores_todos.append(theta_val)
            
            if s["valido"]:
                sensores_validos.append(theta_val)
                
                # Identificar sensores críticos
                if theta_val < SUELO["theta_critico"]:
                    sensores_criticos_ids.append(sensor_id)
                
                # Extraer zona del sensor (ej: P01_F1C1 -> F1 es la zona)
                if "_F" in sensor_id:
                    # Extrae el número de frente (F1, F2, F3)
                    zona = sensor_id.split("_F")[1][0]
                    zona_key = f"Frente {zona}"
                    if zona_key not in zonas_humedad:
                        zonas_humedad[zona_key] = []
                    zonas_humedad[zona_key].append(theta_val)
        
        # Calcular estadísticas
        if sensores_validos:
            min_theta = min(sensores_validos)
            max_theta = max(sensores_validos)
            std_theta = np.std(sensores_validos) if len(sensores_validos) > 1 else 0
            
            # Encontrar zona más seca
            zona_mas_seca = None
            zona_humedad_min = 1.0
            for zona, humedades in zonas_humedad.items():
                humedad_promedio = sum(humedades) / len(humedades)
                if humedad_promedio < zona_humedad_min:
                    zona_humedad_min = humedad_promedio
                    zona_mas_seca = zona
            
            sensores_stats = {
                "validos": len(sensores_validos),
                "no_validos": 12 - len(sensores_validos),
                "min_theta": min_theta,
                "max_theta": max_theta,
                "std_theta": std_theta,
                "criticos": len(sensores_criticos_ids),
                "zona_mas_seca": zona_mas_seca,
                "zona_humedad": zona_humedad_min if zona_mas_seca else None
            }
        else:
            sensores_stats = {
                "validos": 0,
                "no_validos": 12,
                "min_theta": 0,
                "max_theta": 0,
                "std_theta": 0,
                "criticos": 0,
                "zona_mas_seca": None,
                "zona_humedad": None
            }

        # =========================================================================
        # RESULTADO
        # =========================================================================

        return {

            "parcela": parcela_id,

            "nombre": info["nombre"],

            "municipio": info["municipio"],

            "theta": theta,

            "decision":
                CLASES_RIEGO[clase_final]["nombre"],

            "lamina_mm":
                lamina_mm,

            "volumen_m3":
                round(
                    lamina_mm
                    * info["area_ha"]
                    * 10,
                    1
                ),

            "n_validos":
                n_validos,

            "confianza":
                confianza,

            "sensores":
                lectura["sensores"],

            "temp_suelo_promedio":
                temp_suelo_promedio,

            "explicacion":
                generar_explicacion(

                    clase_final,

                    theta,

                    etc,

                    confianza,

                    n_validos,

                    clima_actual,

                    pred,

                    False,

                    prioridad,

                    deficit_mm=deficit_mm,
                    
                    sensores_stats=sensores_stats,
                    
                    temp_suelo_promedio=temp_suelo_promedio
                )
        }

    # =========================================================================
    # MOSTRAR SENSORES
    # =========================================================================

    def mostrar_sensores(
        self,
        sensores
    ):

        print("\nSENSORES:")
        print("-" * 70)

        for sid, s in sorted(sensores.items()):

            estado = (
                "OK"
                if s["valido"]
                else "ANOMALIA"
            )
            
            # Mostrar temperatura del suelo si existe
            temp_info = ""
            if s.get("temp_suelo"):
                temp_info = f" | Suelo: {s['temp_suelo']:.1f}°C"

            print(
                f"{sid:<8}"
                f" | Reportado: {s['theta_sensor']:.2%}"
                f" | Real: {s['theta_real']:.2%}"
                f" | Estado: {estado}"
                f"{temp_info}"
            )

    # =========================================================================
    # TODAS LAS PARCELAS
    # =========================================================================

    def recomendar_todas_parcelas(self):

        print("=" * 80)
        print("SISTEMA IA AGRÍCOLA PREDICTIVO")
        print("=" * 80)

        ranking = []

        for parcela_id in PARCELAS.keys():

            try:

                resultado = self.recomendar(
                    parcela_id
                )

                ranking.append((

                    parcela_id,

                    resultado["nombre"],

                    resultado["theta"]
                ))

                print("\n" + "=" * 80)

                print(
                    f"PARCELA: "
                    f"{resultado['parcela']} "
                    f"- {resultado['nombre']}"
                )

                print(
                    f"MUNICIPIO: "
                    f"{resultado['municipio']}"
                )

                print("-" * 80)

                print(
                    f"HUMEDAD PROMEDIO: "
                    f"{resultado['theta']:.2%}"
                )

                print(
                    f"SENSORES VÁLIDOS: "
                    f"{resultado['n_validos']}/12"
                )

                print(
                    f"CONFIANZA DEL SISTEMA: "
                    f"{resultado['confianza']:.1f}%"
                )

                print(
                    f"DECISIÓN: "
                    f"{resultado['decision']}"
                )

                print(
                    f"LÁMINA: "
                    f"{resultado['lamina_mm']} mm"
                )

                print(
                    f"VOLUMEN: "
                    f"{resultado['volumen_m3']} m³"
                )

                self.mostrar_sensores(
                    resultado["sensores"]
                )

                print("\nRESUMEN DEL SISTEMA")
                print("-" * 60)

                print(
                    resultado["explicacion"]
                )

                print("=" * 80)

            except Exception as e:

                print(
                    f"\nError en parcela "
                    f"{parcela_id}: {e}"
                )
                
                import traceback
                traceback.print_exc()

        # =========================================================================
        # RANKING
        # =========================================================================

        print("\n")
        print("=" * 80)
        print("RANKING GLOBAL")
        print("=" * 80)

        ranking = sorted(
            ranking,
            key=lambda x: x[2]
        )

        for i, r in enumerate(ranking, 1):

            print(
                f"{i}. "
                f"{r[0]} - {r[1]} "
                f"| Humedad: {r[2]:.2%}"
            )

        print("=" * 80)

    # =========================================================================
    # CERRAR
    # =========================================================================

    def cerrar(self):

        self.sensor.cerrar()

        self.conn.close()

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":

    print("INICIANDO SISTEMA IA DE RIEGO")
    print("=" * 80)

    rec = Recomendador()

    try:

        while True:

            rec.recomendar_todas_parcelas()

            print(
                "\nEsperando siguiente ciclo "
                "(5 minutos)..."
            )

            time.sleep(300)

    except KeyboardInterrupt:

        print("\nSistema detenido manualmente")

    finally:

        print("\nCerrando conexiones...")

        rec.cerrar()

        print("Sistema cerrado correctamente")