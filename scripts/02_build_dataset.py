"""Paso 2 — Limpia el histórico y construye el dataset de entrenamiento."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.preprocess import load_results, to_model_frame
from src.utils.config import load_settings


def main() -> None:
    cfg = load_settings()
    df = load_results(cfg["data"]["results_csv"], start_date=cfg["data"]["start_date"])
    model_df = to_model_frame(df)

    # Incorpora resultados reales traídos de la hoja (sheet_pull_results.py), si existen.
    sheet_csv = Path("data/external/sheet_results.csv")
    if sheet_csv.exists():
        extra = to_model_frame(load_results(sheet_csv))
        model_df = (pd.concat([model_df, extra], ignore_index=True)
                    .drop_duplicates(subset=["date", "team_home", "team_away"], keep="last"))
        print(f"  + {len(extra)} resultados de la hoja BD_fifa")

    out = Path("data/processed/matches.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    model_df.to_csv(out, index=False)
    print(f"Dataset construido: {len(model_df)} partidos -> {out}")


if __name__ == "__main__":
    main()
