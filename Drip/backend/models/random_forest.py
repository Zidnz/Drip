import sqlite3
import pandas as pd
import numpy as np
import joblib
import os, sys
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix

# Configuración de rutas para módulos internos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, SUELO, CLASES_RIEGO

RF_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rf_model.pkl")

# =============================================================================
# INGENIERÍA DE CARACTERÍSTICAS Y PREDICCIÓN (RANDOM FOREST)
# =============================================================================

def construir_features_rf(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera el vector de 11 características para el modelo predictivo.
    Incluye dinámicas temporales (deltas) y variables de estado agronómico.
    """
    feats = pd.DataFrame()

    # Series temporales de humedad y tendencia
    theta = df["theta_usado"].fillna(df["theta_real"])
    feats["theta_hoy"]    = theta
    feats["theta_ayer"]   = theta.shift(1).fillna(theta.mean())
    feats["theta_antier"] = theta.shift(2).fillna(theta.mean())
    feats["tendencia_3d"] = theta.diff(3).fillna(0) # Pendiente del contenido de agua

    # Métricas de déficit y estrés
    feats["deficit_actual"] = (SUELO["theta_fc"] - theta).clip(lower=0)

    # Variables climáticas acumuladas y actuales
    feats["et0_hoy"]      = df["et0"].fillna(df["et0"].mean())
    feats["et0_media_3d"] = df["et0"].rolling(3, min_periods=1).mean()
    feats["lluvia_3d"]    = df["lluvia"].rolling(3, min_periods=1).sum().fillna(0)

    # Parámetros del ciclo del cultivo
    feats["kc"]           = df["kc"].fillna(0.5)
    feats["dia_ciclo"]    = df["dia_ciclo"].fillna(65)

    # Codificación ordinal de etapas fenológicas
    etapa_map = {"Inicial": 0, "Desarrollo": 1, "Media (Floración)": 2, "Final (Madurez)": 3}
    feats["etapa_cod"] = df["etapa"].map(etapa_map).fillna(1)

    return feats

class PredictorRiego:
    """
    Modelo de clasificación para la predicción del estado hídrico en t+3 días.
    """
    def __init__(self):
        self.conn   = sqlite3.connect(DB_PATH)
        self.modelo = None

    def cargar_datos(self) -> pd.DataFrame:
        """
        Merge de lecturas de sensor y clima. 
        Implementa lógica de selección de humedad (Sensor validado vs BH).
        """
        return pd.read_sql_query("""
            SELECT
                ls.parcela_id, ls.fecha, ls.dia_ciclo, ls.etapa, ls.kc,
                ls.theta_real, ls.theta_sensor, ls.tipo_error, ls.clase_hoy, ls.clase_t3,
                cd.et0, cd.lluvia,
                CASE
                    WHEN ls.theta_sensor IS NOT NULL AND ls.tipo_error NOT IN ('spike','faltante')
                    THEN ls.theta_sensor ELSE ls.theta_real
                END as theta_usado
            FROM lecturas_sensor ls
            LEFT JOIN clima_diario cd ON ls.parcela_id = cd.parcela_id AND ls.fecha = cd.fecha
            WHERE ls.clase_t3 IS NOT NULL ORDER BY ls.parcela_id, ls.fecha
        """, self.conn)

    def entrenar(self, df: pd.DataFrame):
        """
        Ajuste del clasificador Random Forest con balanceo de clases y validación cruzada.
        """
        feats = construir_features_rf(df)
        X, y = feats.values, df["clase_t3"].astype(int).values

        # Hiperparámetros optimizados para evitar overfitting en series temporales
        self.modelo = RandomForestClassifier(
            n_estimators=300,
            max_depth=12,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )

        # Validación cruzada estratificada para evaluar estabilidad
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cross_val_score(self.modelo, X, y, cv=cv, scoring="f1_weighted")

        self.modelo.fit(X, y)
        joblib.dump(self.modelo, RF_MODEL_PATH)
        
        return feats, y

    def evaluar_final(self, X_feats, y_true):
        """Generación de métricas de performance y matriz de confusión."""
        y_pred = self.modelo.predict(X_feats.values)
        clases_id = sorted(list(set(y_true) | set(y_pred)))
        nombres = [CLASES_RIEGO[i]["nombre"] for i in clases_id]
        
        print(classification_report(y_true, y_pred, labels=clases_id, target_names=nombres, zero_division=0))

    def predecir_dia(self, parcela_id: str, fecha: str) -> dict:
        """
        Inferencia de estado hídrico a futuro (t+3) para una parcela específica.
        Requiere ventana histórica de 5 días para el cálculo de características.
        """
        if self.modelo is None and os.path.exists(RF_MODEL_PATH):
            self.modelo = joblib.load(RF_MODEL_PATH)

        df_ctx = pd.read_sql_query("""
            SELECT ls.parcela_id, ls.fecha, ls.dia_ciclo, ls.etapa, ls.kc,
                   ls.theta_real, ls.theta_sensor, ls.tipo_error, cd.et0, cd.lluvia,
                   CASE WHEN ls.theta_sensor IS NOT NULL AND ls.tipo_error NOT IN ('spike','faltante')
                        THEN ls.theta_sensor ELSE ls.theta_real END as theta_usado
            FROM lecturas_sensor ls
            LEFT JOIN clima_diario cd ON ls.parcela_id=cd.parcela_id AND ls.fecha=cd.fecha
            WHERE ls.parcela_id=? AND ls.fecha<=? ORDER BY ls.fecha DESC LIMIT 5
        """, self.conn, params=(parcela_id, fecha))

        if df_ctx.empty: return {"error": "Datos insuficientes"}

        df_ctx = df_ctx.iloc[::-1].reset_index(drop=True)
        feats  = construir_features_rf(df_ctx)
        X_pred = feats.iloc[[-1]].values

        clase = int(self.modelo.predict(X_pred)[0])
        probas = self.modelo.predict_proba(X_pred)[0]
        
        return {
            "parcela_id": parcela_id, "fecha": fecha, "clase_t3": clase,
            "nombre": CLASES_RIEGO[clase]["nombre"],
            "confianza_rf": round(float(probas[clase]), 3)
        }

    def cerrar(self):
        self.conn.close()

if __name__ == "__main__":
    pred = PredictorRiego()
    df_train = pred.cargar_datos()
    features, targets = pred.entrenar(df_train)
    pred.evaluar_final(features, targets)
    pred.cerrar()