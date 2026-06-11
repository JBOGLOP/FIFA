"""Calibra el peso de mezcla Elo minimizando el RPS out-of-sample."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.evaluate import optimize_blend
from src.utils.config import load_settings


def main() -> None:
    cfg = load_settings()
    df = pd.read_csv("data/processed/matches.csv", parse_dates=["date"])

    grid = cfg["model"]["elo_blend_grid"]
    xi = cfg["model"]["xi"]
    print(f"Evaluando {len(grid)} pesos de mezcla Elo (xi={xi}) sobre {len(df)} partidos...")
    results = optimize_blend(df, grid, xi=xi)

    print("\nResultados (mejor RPS primero):")
    print(results.to_string(index=False))

    out = Path("outputs/reports/blend_optimization.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(out, index=False)

    best = results.iloc[0]
    print(f"\nMejor peso = {best['weight']} (RPS {best['mean_rps']:.4f}). Tabla -> {out}")
    print("Para usarlo, fija model.elo_blend_weight en config/settings.yaml a ese valor.")


if __name__ == "__main__":
    main()
