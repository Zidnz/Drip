import sqlite3
import pandas as pd
import numpy as np
import joblib
import os, sys
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix

# Configuración de rutas para módulos internos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, SUELO

MODELO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "if_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "if_scaler.pkl")

# =============================================================================
# DETECCIÓN DE ANOMALÍAS (ISOLATION FOREST)
# =============================================================================

def construir_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ingeniería de características basada en series temporales y física del suelo.
    Calcula variaciones, medias móviles y z-scores para identificar outliers.
    """
    theta_imp = df["theta_sensor"].fillna(df["theta_sensor"].median())
    feats = pd.DataFrame()
    
    # Características de valor absoluto y deltas
    feats["theta_sensor"]    = theta_imp
    feats["diff_1d"]         = theta_imp.diff(1).fillna(0)
    feats["diff_2d"]         = theta_imp.diff(2).fillna(0)
    
    # Ventanas móviles para contexto temporal
    feats["rolling_std_3d"]  = theta_imp.rolling(3, min_periods=1).std().fillna(0)
    feats["rolling_mean_5d"] = theta_imp.rolling(5, min_periods=1).mean().fillna(theta_imp.mean())
    
    # Análisis estadístico (Z-Score)
    media = theta_imp.mean()
    std   = theta_imp.std() + 1e-6
    feats["z_score"]         = (theta_imp - media) / std
    
    # Flags de límites físicos (Capacidad de campo + margen)
    feats["fuera_rango"]     = ((theta_imp < 0.05) | (theta_imp > SUELO["theta_sat"] + 0.05)).astype(int)
    
    # Diferencia residual vs modelo físico si está disponible
    feats["diff_vs_bh"] = (theta_imp - df["theta_real"].fillna(theta_imp)).abs() if "theta_real" in df.columns else 0.0
    
    return feats

class DetectorAnomalias:
    """
    Implementación de Isolation Forest para la calificación de calidad de telemetría.
    """
    def __init__(self):
        self.conn          = sqlite3.connect(DB_PATH)
        self.modelo        = None
        self.scaler        = None
        self.contaminacion = 0.08 # Porcentaje estimado de outliers en el dataset

    def cargar_datos(self) -> pd.DataFrame:
        """Carga el histórico de lecturas para entrenamiento/inferencia."""
        return pd.read_sql_query("""
            SELECT id, parcela_id, fecha, dia_ciclo, etapa,
                   theta_real, theta_sensor, tipo_error, kc
            FROM lecturas_sensor ORDER BY parcela_id, fecha
        """, self.conn)

    def entrenar(self, df: pd.DataFrame):
        """
        Ajusta el modelo Isolation Forest sobre lecturas válidas.
        Serializa el modelo y el escalador para inferencia en tiempo real.
        """
        df_train = df[df["theta_sensor"].notna()].copy()
        feats    = construir_features(df_train)
        X        = feats.values
        
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.modelo = IsolationForest(
            n_estimators=200,
            contamination=self.contaminacion,
            max_samples="auto",
            random_state=42,
            n_jobs=-1
        )
        self.modelo.fit(X_scaled)
        
        joblib.dump(self.modelo, MODELO_PATH)
        joblib.dump(self.scaler, SCALER_PATH)

    def predecir(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Evalúa la calidad de la señal. 
        Retorna 'mala' si se detecta anomalía o dato nulo.
        """
        if self.modelo is None:
            raise RuntimeError("Modelo no inicializado.")

        resultados = []
        for parcela_id in df["parcela_id"].unique():
            df_p = df[df["parcela_id"] == parcela_id].copy().reset_index(drop=True)

            for i, row in df_p.iterrows():
                # Caso: Pérdida de conectividad / NaN
                if pd.isna(row["theta_sensor"]):
                    resultados.append({
                        "id": row["id"], "parcela_id": parcela_id, "fecha": row["fecha"], 
                        "theta_real": row["theta_real"], "theta_sensor": None, 
                        "tipo_error": row["tipo_error"], "if_score": 1.0, "calidad": "mala"
                    })
                    continue

                # Inferencia con ventana deslizante de 5 días
                inicio  = max(0, i - 4)
                ventana = df_p.iloc[inicio:i + 1]
                feats   = construir_features(ventana)
                X_row   = self.scaler.transform(feats.iloc[[-1]].values)

                prediccion = self.modelo.predict(X_row)[0]
                score_raw  = self.modelo.score_samples(X_row)[0]
                
                resultados.append({
                    "id": row["id"], "parcela_id": parcela_id, "fecha": row["fecha"], 
                    "theta_real": row["theta_real"], "theta_sensor": row["theta_sensor"],
                    "tipo_error": row["tipo_error"], "if_score": round(-score_raw, 4), 
                    "calidad": "mala" if prediccion == -1 else "buena"
                })

        return pd.DataFrame(resultados)

    def guardar_en_mongodb(self, df_pred: pd.DataFrame):
        """Persistencia de resultados en capa NoSQL para auditoría de sensores."""
        try:
            from nosql_store import NoSQLStore
            store = NoSQLStore()
            documentos = []
            for _, row in df_pred.iterrows():
                doc = {
                    "parcela_id": row["parcela_id"], "fecha": row["fecha"],
                    "theta_real": row["theta_real"], "theta_sensor": row["theta_sensor"],
                    "if_score": row["if_score"], "calidad": row["calidad"]
                }
                
                # Metadata adicional para diagnóstico de fallas
                if row["calidad"] == "mala":
                    doc["accion_tomada"] = "fallback_bh"
                    doc["razon_anomalia"] = (
                        "dato_faltante" if row["theta_sensor"] is None else 
                        "valor_aberrante" if row["if_score"] > 0.3 else "patron_inusual"
                    )
                documentos.append(doc)

            store.insertar_muchas_lecturas(documentos)
        except Exception:
            pass

    def evaluar(self, df_pred: pd.DataFrame):
        """Genera métricas de performance (Precision/Recall) contra errores simulados."""
        def etiqueta_real(tipo):
            return "mala" if tipo in ["spike", "faltante"] else "buena"

        df_e = df_pred[df_pred["tipo_error"].notna()].copy()
        df_e["real"] = df_e["tipo_error"].apply(etiqueta_real)
        
        print(classification_report(df_e["real"], df_e["calidad"], zero_division=0))

    def cerrar(self):
        self.conn.close()

if __name__ == "__main__":
    det = DetectorAnomalias()
    df_raw = det.cargar_datos()
    det.entrenar(df_raw)
    df_res = det.predecir(df_raw)
    det.evaluar(df_res)
    det.guardar_en_mongodb(df_res)
    det.cerrar()