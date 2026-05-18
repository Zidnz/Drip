import os
import json
from datetime import datetime

# =============================================================================
# GESTIÓN DE PERSISTENCIA NOSQL (MONGODB / TINYDB)
# =============================================================================

# Intento de carga de variables de entorno para Atlas
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env")
except ImportError:
    pass

# Configuración de conexión y fallback
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://riego_admin:TwX7fzRhGGIh1Qf3@riego-cluster.kq4djsj.mongodb.net/")
MONGO_DB_NAME = os.getenv("MONGO_DB", "riego_sinaloa")
USE_FALLBACK = not bool(MONGO_URI)

from config import BASE_DIR
NOSQL_DIR = os.path.join(BASE_DIR, "data", "nosql")
os.makedirs(NOSQL_DIR, exist_ok=True)

class NoSQLStore:
    """
    Clase de abstracción para almacenamiento de documentos (Logs y Lecturas Raw).
    Implementa un sistema hibrido MongoDB Atlas con Fallback a TinyDB local.
    """
    def __init__(self):
        if USE_FALLBACK:
            self._init_tinydb()
        else:
            self._init_mongodb()

    def _init_mongodb(self):
        """Inicializa driver de MongoDB y asegura índices de consulta."""
        try:
            from pymongo import MongoClient
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            client.admin.command("ping")
            db = client[MONGO_DB_NAME]
            
            self._log_col    = db["log_decisiones"]
            self._sensor_col = db["lecturas_sensor_raw"]
            self._backend    = "mongodb"
            
            # Índices optimizados para reportes y telemetría
            self._log_col.create_index([("parcela_id", 1), ("fecha", 1)])
            self._sensor_col.create_index([("parcela_id", 1), ("fecha", 1)])
            self._log_col.create_index([("modo_operacion", 1)])
            
        except Exception:
            self._init_tinydb()

    def _init_tinydb(self):
        """Inicializa base de datos basada en archivos JSON locales."""
        from tinydb import TinyDB
        self._log_col    = TinyDB(os.path.join(NOSQL_DIR, "log_decisiones.json")).table("decisiones")
        self._sensor_col = TinyDB(os.path.join(NOSQL_DIR, "lecturas.json")).table("lecturas")
        self._backend    = "tinydb"

    @property
    def backend(self):
        return self._backend

    def _ts(self, doc):
        """Inyecta timestamp de servidor al documento."""
        doc.setdefault("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return doc

    # Métodos de Inserción
    def insertar_log_decision(self, doc):
        doc = self._ts(doc)
        if self._backend == "mongodb":
            return str(self._log_col.insert_one(doc).inserted_id)
        return str(self._log_col.insert(doc))

    def insertar_lectura_sensor(self, doc):
        doc = self._ts(doc)
        if self._backend == "mongodb":
            return str(self._sensor_col.insert_one(doc).inserted_id)
        return str(self._sensor_col.insert(doc))

    def insertar_muchos_logs(self, docs):
        for d in docs: self._ts(d)
        if self._backend == "mongodb": self._log_col.insert_many(docs)
        else: self._log_col.insert_multiple(docs)
        return len(docs)

    def insertar_muchas_lecturas(self, docs):
        for d in docs: self._ts(d)
        if self._backend == "mongodb": self._sensor_col.insert_many(docs)
        else: self._sensor_col.insert_multiple(docs)
        return len(docs)

    # Métodos de Consulta y Filtrado
    def obtener_logs_parcela(self, parcela_id, fecha_inicio=None, fecha_fin=None):
        if self._backend == "mongodb":
            f = {"parcela_id": parcela_id}
            if fecha_inicio and fecha_fin:
                f["fecha"] = {"$gte": fecha_inicio, "$lte": fecha_fin}
            return list(self._log_col.find(f, {"_id": 0}))
        
        from tinydb import Query
        Q = Query()
        base = Q.parcela_id == parcela_id
        if fecha_inicio and fecha_fin:
            return self._log_col.search(base & (Q.fecha >= fecha_inicio) & (Q.fecha <= fecha_fin))
        return self._log_col.search(base)

    def obtener_logs_modo_asistido(self, parcela_id=None):
        if self._backend == "mongodb":
            f = {"modo_operacion": "asistido"}
            if parcela_id: f["parcela_id"] = parcela_id
            return list(self._log_col.find(f, {"_id": 0}))
        
        from tinydb import Query
        Q = Query()
        base = Q.modo_operacion == "asistido"
        if parcela_id:
            return self._log_col.search(base & (Q.parcela_id == parcela_id))
        return self._log_col.search(base)

    def obtener_lecturas_anomalas(self, parcela_id=None):
        """Recupera documentos marcados como anómalos por el Isolation Forest."""
        if self._backend == "mongodb":
            f = {"calidad": "mala"}
            if parcela_id: f["parcela_id"] = parcela_id
            return list(self._sensor_col.find(f, {"_id": 0}))
        
        from tinydb import Query
        Q = Query()
        base = Q.calidad == "mala"
        if parcela_id:
            return self._sensor_col.search(base & (Q.parcela_id == parcela_id))
        return self._sensor_col.search(base)

    def obtener_resumen_por_parcela(self, parcela_id):
        """Genera agregaciones de estados de decisión y confianza."""
        logs = self.obtener_logs_parcela(parcela_id)
        if not logs:
            return {"parcela_id": parcela_id, "total_logs": 0}
        
        clases = {0: 0, 1: 0, 2: 0}
        modos  = {"normal": 0, "divergente": 0, "asistido": 0}
        confs  = {"Alta": 0, "Media": 0, "Baja": 0}
        
        for log in logs:
            d = log.get("decision", {})
            c  = d.get("clase_final")
            m  = log.get("modo_operacion", "normal")
            cf = d.get("confianza", "Media")
            
            if c is not None: clases[c] = clases.get(c, 0) + 1
            modos[m]  = modos.get(m, 0) + 1
            confs[cf] = confs.get(cf, 0) + 1
            
        return {
            "parcela_id":    parcela_id,
            "total_logs":    len(logs),
            "clases":        clases,
            "modos":         modos,
            "confianza":     confs,
            "pct_asistido":  round(modos.get("asistido", 0) / len(logs) * 100, 1),
        }

    def total_documentos(self):
        if self._backend == "mongodb":
            return {
                "log_decisiones":      self._log_col.count_documents({}),
                "lecturas_sensor_raw": self._sensor_col.count_documents({}),
                "backend":             "MongoDB Atlas",
            }
        return {
            "log_decisiones":      len(self._log_col),
            "lecturas_sensor_raw": len(self._sensor_col),
            "backend":             "TinyDB (local)",
        }

    def exportar_logs_json(self, parcela_id, ruta):
        logs = self.obtener_logs_parcela(parcela_id)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    def limpiar_todo(self):
        """Truncado de todas las colecciones/tablas."""
        if self._backend == "mongodb":
            self._log_col.delete_many({})
            self._sensor_col.delete_many({})
        else:
            self._log_col.truncate()
            self._sensor_col.truncate()

if __name__ == "__main__":
    # Test unitario de persistencia
    store = NoSQLStore()
    
    test_doc = {
        "parcela_id": "P03", 
        "fecha": datetime.now().strftime("%Y-%m-%d"), 
        "modo_operacion": "normal",
        "decision": {"clase_final": 0, "confianza": "Alta"}
    }
    
    insert_id = store.insertar_log_decision(test_doc)
    stats = store.total_documentos()