# ============================================================
# DIGITAL TWIN
# ============================================================

class DigitalTwin:

    def __init__(self, suelo):

        self.suelo = suelo

    # ========================================================

    def simular_riego(
        self,
        theta_actual,
        lamina_mm
    ):

        theta_final = (
            theta_actual +
            (lamina_mm / 900)
        )

        return round(theta_final, 4)

    # ========================================================

    def comparar_escenarios(
        self,
        theta_actual
    ):

        escenarios = []

        for lamina in [0, 20, 40, 60]:

            theta_final = (
                self.simular_riego(
                    theta_actual,
                    lamina
                )
            )

            escenarios.append({

                "lamina_mm": lamina,

                "theta_final": theta_final
            })

        return escenarios