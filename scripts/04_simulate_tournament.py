"""Paso 4 — Simula el torneo completo (Monte Carlo) y guarda probabilidades."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.blended import build_blended_predictor
from src.models.dixon_coles import fit_dixon_coles
from src.simulation.monte_carlo import run_simulations
from src.utils.config import load_groups, load_settings, load_yaml


def main() -> None:
    cfg = load_settings()
    groups_cfg = load_groups()
    bracket = load_yaml("bracket.yaml")

    df = pd.read_csv("data/processed/matches.csv", parse_dates=["date"])
    if cfg["model"].get("use_elo_blend"):
        w = cfg["model"]["elo_blend_weight"]
        print(f"Ajustando modelo mezclado Dixon-Coles + Elo (peso={w})...")
        model = build_blended_predictor(df, xi=cfg["model"]["xi"], weight=w)
    else:
        print("Ajustando Dixon-Coles...")
        model = fit_dixon_coles(df, xi=cfg["model"]["xi"])

    n = cfg["simulation"]["n_iterations"]
    print(f"Simulando el torneo {n} veces...")
    results = run_simulations(
        model,
        groups_cfg["groups"],
        groups_cfg["hosts"],
        bracket,
        n_iterations=n,
        seed=cfg["simulation"]["random_seed"],
    )

    out = Path("outputs/simulations/tournament_probabilities.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(out, index=False)

    pd.set_option("display.float_format", lambda x: f"{x:.3f}")
    print("\nTop 15 candidatos al titulo:")
    print(results.head(15).to_string(index=False))
    print(f"\nResultados completos -> {out}")


if __name__ == "__main__":
    main()
