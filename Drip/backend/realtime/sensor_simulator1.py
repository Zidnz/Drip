import time
import random
import math
import logging
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# ============================================================
# CONFIGURACIÓN
# ============================================================

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

DB_NAME = "riego_sinaloa"

COLECCION_SENSORES = "lecturas_sensores"

INTERVALO_SEGUNDOS = 300

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)

log = logging.getLogger("SensorSim")

# ============================================================
# PARCELAS
# ============================================================

PARCELAS = {

    "P01": {
        "nombre": "Valle del Fuerte Norte",
        "municipio": "Los Mochis",
        "area_ha": 15.0
    },

    "P02": {
        "nombre": "Valle de Guasave",
        "municipio": "Guasave",
        "area_ha": 10.5
    },

    "P03": {
        "nombre": "Valle de Culiacan",
        "municipio": "Culiacan",
        "area_ha": 12.0
    },

    "P04": {
        "nombre": "Valle de Navolato",
        "municipio": "Navolato",
        "area_ha": 8.0
    },

    "P05": {
        "nombre": "Valle de Escuinapa",
        "municipio": "Escuinapa",
        "area_ha": 9.5
    },
}

FILAS = 3
COLUMNAS = 4

OFFSET_POSICION = {

    (1, 1): +1.5,
    (1, 2): +0.8,
    (1, 3): -0.3,
    (1, 4): -1.2,

    (2, 1): +0.5,
    (2, 2): +0.2,
    (2, 3): +0.1,
    (2, 4): -0.5,

    (3, 1): -0.8,
    (3, 2): -0.4,
    (3, 3): +0.6,
    (3, 4): +1.0,
}

# ============================================================
# TEMPERATURAS BASE POR PARCELA
# ============================================================

TEMPERATURAS_BASE = {

    "P01": 28.5,  # Los Mochis
    "P02": 29.0,  # Guasave
    "P03": 30.0,  # Culiacán
    "P04": 31.0,  # Navolato
    "P05": 32.0,  # Escuinapa (más cálido)
}

# ============================================================
# MODELO FÍSICO
# ============================================================

class ModeloFisico:

    @staticmethod
    def radiacion_solar(hora):

        if hora < 6 or hora > 19:
            return 0.0

        t_rel = (hora - 6) / 13.0

        return max(
            0.0,
            1100.0 * math.sin(math.pi * t_rel)
        )

    @staticmethod
    def delta_humedad(
        hora,
        radiacion,
        irrigando=False
    ):

        if irrigando:

            return random.uniform(0.5, 1.5)

        factor_rad = (
            radiacion / 1100.0
        ) * 0.05

        if hora < 6.5 or hora > 19.5:

            factor_rad *= 0.08

        return round(
            -factor_rad + random.gauss(0, 0.015),
            4
        )
    
    @staticmethod
    def temperatura_suelo(
        parcela_id,
        hora,
        humedad,
        radiacion
    ):
        """
        Calcula la temperatura del suelo basada en:
        - Temperatura base de la parcela
        - Hora del día (ciclo diario)
        - Humedad del suelo (más humedad = más fresca)
        - Radiación solar
        """
        
        # Temperatura base de la parcela
        temp_base = TEMPERATURAS_BASE.get(parcela_id, 29.0)
        
        # Ciclo diario de temperatura (máxima a las 15:00, mínima a las 6:00)
        if hora < 6 or hora > 18:
            # Noche: temperatura más fresca
            ciclo = -3.0
        elif 6 <= hora <= 15:
            # Mañana a mediodía: subiendo
            ciclo = -3.0 + (hora - 6) * (6.0 / 9.0)
        else:
            # Tarde: bajando
            ciclo = 3.0 - (hora - 15) * (6.0 / 9.0)
        
        # Factor de humedad (suelo húmedo = más fresco)
        # 40% humedad → -2°C, 20% humedad → +2°C
        factor_humedad = (30 - humedad) * 0.1
        
        # Factor de radiación (más radiación = más calor)
        factor_radiacion = (radiacion / 1100.0) * 3.0
        
        # Calcular temperatura final
        temp_suelo = temp_base + ciclo + factor_humedad + factor_radiacion
        
        # Ruido aleatorio (±0.5°C)
        temp_suelo += random.gauss(0, 0.3)
        
        # Limitar rangos realistas (15°C - 45°C)
        return round(max(15.0, min(45.0, temp_suelo)), 1)

# ============================================================
# ESTADOS SENSOR
# ============================================================

class Estado:

    NORMAL = "NORMAL"

    DERIVA = "DERIVA"

    ATASCADO = "ATASCADO"

    RECUPERACION = "RECUPERACION"

# ============================================================
# SENSOR
# ============================================================

class SensorHumedad:

    PROB_FALLO = 0.05

    def __init__(
        self,
        parcela_id,
        fila,
        columna
    ):

        self.parcela_id = parcela_id

        self.fila = fila

        self.columna = columna

        self.sensor_id = (
            f"{parcela_id}_F{fila}C{columna}"
        )

        base = (
            42.0
            + OFFSET_POSICION.get(
                (fila, columna),
                0.0
            )
        )

        self.valor_real = (
            base + random.uniform(-3, 3)
        )
        
        # Inicializar temperatura del suelo
        self.temp_suelo = None

        self.estado = Estado.NORMAL

    def leer(
        self,
        hora,
        irrigando,
        radiacion
    ):

        delta = ModeloFisico.delta_humedad(
            hora,
            radiacion,
            irrigando
        )

        self.valor_real = max(
            10.0,
            min(
                80.0,
                self.valor_real + delta
            )
        )

        valor_reportado = round(

            self.valor_real
            + random.gauss(0, 0.12),

            2
        )
        
        # Calcular temperatura del suelo
        self.temp_suelo = ModeloFisico.temperatura_suelo(
            self.parcela_id,
            hora,
            self.valor_real,
            radiacion
        )

        return {

            "sensor_id": self.sensor_id,

            "parcela_id": self.parcela_id,

            "fila": self.fila,

            "columna": self.columna,

            "timestamp":
                datetime.now(timezone.utc),

            "valor_real":
                round(self.valor_real, 2),

            "valor_reportado":
                valor_reportado,

            "temp_suelo":
                self.temp_suelo,  # NUEVO CAMPO

            "estado_sensor":
                self.estado,

            "es_anomalia":
                False
        }

# ============================================================
# FLOTA
# ============================================================

class FlotaSensores:

    def __init__(self):

        self.sensores = []

        self._crear()

    def _crear(self):

        for parcela_id in PARCELAS:

            for fila in range(1, FILAS + 1):

                for col in range(1, COLUMNAS + 1):

                    self.sensores.append(

                        SensorHumedad(
                            parcela_id,
                            fila,
                            col
                        )
                    )

        log.info(
            f"Flota lista: "
            f"{len(self.sensores)} sensores"
        )

    def leer_todos(self):

        ahora = datetime.now()

        hora = (
            ahora.hour
            + ahora.minute / 60.0
        )

        radiacion = (
            ModeloFisico.radiacion_solar(hora)
        )

        return [

            s.leer(
                hora,
                False,
                radiacion
            )

            for s in self.sensores
        ]

# ============================================================
# MONGODB
# ============================================================

class EscritorMongoDB:

    def __init__(self):

        client = MongoClient(MONGO_URI)

        db = client[DB_NAME]

        self.col = db[
            COLECCION_SENSORES
        ]

        log.info(
            "MongoDB conectado OK"
        )

    def insertar(
        self,
        lecturas
    ):

        r = self.col.insert_many(
            lecturas
        )

        return len(r.inserted_ids)

# ============================================================
# MAIN
# ============================================================

def main():

    log.info("=" * 60)

    log.info(
        "SIMULADOR EXTERNO DE SENSORES"
    )

    log.info("=" * 60)

    flota = FlotaSensores()

    escritor = EscritorMongoDB()

    while True:

        lecturas = flota.leer_todos()

        insertados = escritor.insertar(
            lecturas
        )

        log.info(
            f"{insertados} documentos insertados"
        )

        time.sleep(
            INTERVALO_SEGUNDOS
        )

if __name__ == "__main__":

    main()