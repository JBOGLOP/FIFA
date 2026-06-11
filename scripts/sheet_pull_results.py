"""Entrada: lee resultados reales de la hoja BD_fifa y los guarda para el dataset.

Salida: data/external/sheet_results.csv (esquema del modelo). Luego ejecuta
02_build_dataset.py: incluirá estos partidos junto al histórico.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.gsheet import fetch_sheet
from src.utils.config import load_settings


def main() -> None:
    cfg = load_settings()["gsheet"]
    df = fetch_sheet(cfg["endpoint"], sheet=cfg["results_tab"])
    if df.empty:
        print("La pestaña de resultados está vacía; nada que importar.")
        return

    # Normaliza al esquema del histórico (results.csv).
    out = pd.DataFrame({
        "date": pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d"),
        "home_team": df["home_team"],
        "away_team": df["away_team"],
        "home_score": pd.to_numeric(df["home_score"], errors="coerce"),
        "away_score": pd.to_numeric(df["away_score"], errors="coerce"),
        "tournament": "FIFA World Cup",
        "city": "", "country": "",
        "neutral": df.get("neutral", True),
    }).dropna(subset=["home_score", "away_score"])

    dest = Path("data/external/sheet_results.csv")
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest, index=False)
    print(f"Importados {len(out)} resultados -> {dest}")
    print("Ejecuta scripts/02_build_dataset.py para incorporarlos al entrenamiento.")


if __name__ == "__main__":
    main()
