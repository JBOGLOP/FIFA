"""Salida: publica las predicciones de la última simulación en la hoja BD_fifa.

Requiere la variable de entorno FIFA_SHEET_TOKEN (el mismo token del Apps Script).
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.gsheet import push_rows
from src.utils.config import load_settings

PCT_COLS = ["group_win", "runner_up", "best_third", "qualified",
            "reach_R16", "reach_QF", "reach_SF", "reach_final", "champion"]


def main() -> None:
    cfg = load_settings()["gsheet"]
    df = pd.read_csv("outputs/simulations/tournament_probabilities.csv")
    # Redondea a porcentaje legible en la hoja.
    for c in PCT_COLS:
        df[c] = (df[c] * 100).round(2)
    rows = df.to_dict(orient="records")

    res = push_rows(cfg["endpoint"], rows, sheet=cfg["predictions_tab"])
    print(f"Publicadas {res.get('written')} filas en la pestaña '{res.get('sheet')}'.")


if __name__ == "__main__":
    main()
