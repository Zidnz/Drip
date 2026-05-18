# ============================================================
# DETECTOR DE FUGAS
# ============================================================

class DetectorFugas:

    def __init__(self):

        self.umbral_caida = 0.08

    # ========================================================

    def evaluar(
        self,
        theta_actual,
        theta_prev,
        riego_aplicado,
        etc
    ):

        alertas = []

        delta = theta_prev - theta_actual

        # ====================================================
        # CAÍDA ANORMAL
        # ====================================================

        if delta > self.umbral_caida:

            alertas.append(
                "Caída anormal de humedad detectada."
            )

        # ====================================================
        # RIEGO SIN EFECTO
        # ====================================================

        if (
            riego_aplicado > 20
            and abs(delta) < 0.01
        ):

            alertas.append(
                "Posible fuga o tubería dañada."
            )

        # ====================================================
        # EVAPORACIÓN ANORMAL
        # ====================================================

        if delta > (etc / 1000) * 1.5:

            alertas.append(
                "Consumo hídrico anormal."
            )

        return {

            "fuga_detectada":
                len(alertas) > 0,

            "alertas":
                alertas
        }