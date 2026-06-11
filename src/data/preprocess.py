"""Limpieza y construcción del dataset de entrenamiento."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_results(csv_path: str | Path, start_date: str | None = None) -> pd.DataFrame:
    """Carga el histórico de partidos y opcionalmente lo filtra por fecha.

    Columnas esperadas: date, home_team, away_team, home_score, away_score,
    tournament, city, country, neutral.
    """
    df = pd.read_csv(csv_path, parse_dates=["date"])
    if start_date:
        df = df[df["date"] >= pd.Timestamp(start_date)]
    df = df.dropna(subset=["home_score", "away_score"])
    return df.reset_index(drop=True)


def to_model_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Adapta las columnas al formato que espera penaltyblog / el modelo."""
    return pd.DataFrame(
        {
            "date": df["date"],
            "team_home": df["home_team"],
            "team_away": df["away_team"],
            "goals_home": df["home_score"].astype(int),
            "goals_away": df["away_score"].astype(int),
            "neutral": df["neutral"].astype(bool),
        }
    )
