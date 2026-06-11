"""Optimiza el parámetro de decaimiento temporal xi minimizando el RPS out-of-sample.

Recorre el grid definido en config/settings.yaml (model.xi_grid), evalúa cada valor
y guarda la tabla de resultados. Actualiza model.xi en settings.yaml con el mejor.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.evaluate import optimize_xi
from src.utils.config import load_settings


def main() -> None:
    cfg = load_settings()
    df = pd.read_csv("data/processed/matches.csv", parse_dates=["date"])

    grid = cfg["model"]["xi_grid"]
    print(f"Evaluando {len(grid)} valores de xi sobre {len(df)} partidos...")
    results = optimize_xi(df, grid, valid_frac=0.15)

    print("\nResultados (mejor RPS primero):")
    print(results.to_string(index=False))

    out = Path("outputs/reports/xi_optimization.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(out, index=False)

    best = results.iloc[0]
    print(f"\nMejor xi = {best['xi']} (RPS {best['mean_rps']:.4f}). Tabla -> {out}")
    print("Para usarlo, fija model.xi en config/settings.yaml a ese valor.")


if __name__ == "__main__":
    main()
