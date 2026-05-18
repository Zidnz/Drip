import numpy as np

# ============================================================
# PREDICTOR FUTURO DE HUMEDAD (VERSIÓN LENGUAJE HUMANO)
# ============================================================

class PredictorFuturo:

    def __init__(self, suelo):
        self.suelo = suelo

    # ========================================================

    def predecir_dias(
        self,
        theta_actual,
        et0,
        kc,
        lluvia_prevista=0,
        dias=7
    ):

        predicciones = []

        theta = theta_actual

        for dia in range(1, dias + 1):

            etc = et0 * kc

            delta = (lluvia_prevista - etc) / (0.9 * 1000)

            theta = theta + delta

            theta = np.clip(
                theta,
                self.suelo["theta_pwp"],
                self.suelo["theta_fc"]
            )

            estado, mensaje = self._clasificar(theta, dia)

            predicciones.append({

                "dia": dia,
                "theta": round(theta, 4),
                "etc": round(etc, 2),
                "estado": estado,
                "mensaje": mensaje
            })

        return predicciones

    # ========================================================

    def _clasificar(self, theta, dia):

        # 🔴 CRÍTICO
        if theta < self.suelo["theta_umbral"]:

            return (
                "critico",
                f"En aproximadamente {dia} días "
                f"el cultivo empezará a sufrir falta de agua "
                f"y podría entrar en estrés hídrico."
            )

        # 🟡 PREVENTIVO
        elif theta < self.suelo["theta_fc"] * 0.85:

            return (
                "preventivo",
                f"En {dia} días el suelo estará con poca humedad. "
                f"Se recomienda considerar riego preventivo."
            )

        # 🟢 ESTABLE
        return (
            "estable",
            f"En {dia} días el cultivo se mantiene en condiciones estables "
            f"sin riesgo de estrés hídrico."
        )

    # ========================================================

    def detectar_estres_futuro(self, predicciones):

        for p in predicciones:

            if p["estado"] == "critico":

                return (
                    True,
                    p["mensaje"]
                )

        return (
            False,
            "El cultivo se mantiene estable en el periodo analizado."
        )