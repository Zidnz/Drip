# ============================================================
# PRIORIZACIÓN DE RIEGO
# ============================================================

class PriorizadorRiego:

    def priorizar(self, parcelas):

        ranking = []

        for p in parcelas:

            deficit = p["deficit_mm"]

            etc = p["etc"]

            area = p["area"]

            score = (
                deficit * 0.5 +
                etc * 0.3 +
                area * 0.2
            )

            ranking.append({

                "parcela":
                    p["parcela"],

                "score":
                    round(score, 2)
            })

        ranking = sorted(

            ranking,

            key=lambda x: x["score"],

            reverse=True
        )

        return ranking