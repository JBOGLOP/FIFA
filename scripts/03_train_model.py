"""Paso 3 — Ajusta el Dixon-Coles (con decaimiento temporal)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.dixon_coles import fit_dixon_coles, predict_match, predict_wc_match
from src.utils.config import load_groups, load_settings


def main() -> None:
    cfg = load_settings()
    df = pd.read_csv("data/processed/matches.csv", parse_dates=["date"])
    model = fit_dixon_coles(df, xi=cfg["model"]["xi"])
    hosts = set(load_groups()["hosts"])

    print(f"Modelo ajustado (xi={cfg['model']['xi']}).\n")

    print("Spain vs France (sede neutral):")
    print(predict_match(model, "Spain", "France", neutral=True))

    print("\nMexico vs South Africa (anfitrion en casa, con localia):")
    print(predict_wc_match(model, "Mexico", "South Africa", hosts))

    print("\nMexico vs South Africa (si fuese neutral, para comparar):")
    print(predict_match(model, "Mexico", "South Africa", neutral=True))


if __name__ == "__main__":
    main()
