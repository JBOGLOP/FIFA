"""Ratings Elo: carga desde TSV de eloratings.net o cálculo desde el histórico."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pandas as pd


def load_elo(tsv_path: str | Path) -> pd.DataFrame:
    """Lee World.tsv: col 2 = código de equipo (2 letras), col 3 = Elo actual."""
    df = pd.read_csv(tsv_path, sep="\t", header=None)
    return pd.DataFrame({"code": df[2], "elo": df[3]})


def _gd_multiplier(gd: int) -> float:
    """Multiplicador por diferencia de goles (estilo World Football Elo Ratings)."""
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return (11 + gd) / 8.0


def compute_elo(df: pd.DataFrame, k: float = 20.0, hfa: float = 70.0,
                base: float = 1500.0) -> tuple[dict[str, float], float]:
    """Calcula Elo walk-forward desde el histórico y calibra beta (Elo->goles).

    Devuelve (ratings_finales, beta) donde beta es la pendiente de la supremacía de
    goles observada frente a la diferencia de Elo pre-partido (mínimos cuadrados por
    el origen). Usa los mismos nombres de equipo que el dataset.
    Espera columnas: date, team_home, team_away, goals_home, goals_away, neutral.
    """
    df = df.sort_values("date")
    ratings: dict[str, float] = defaultdict(lambda: base)
    sxy = sxx = 0.0  # para beta = sum(x*y)/sum(x*x)

    for h, a, gh, ga, neutral in zip(
        df["team_home"], df["team_away"], df["goals_home"], df["goals_away"], df["neutral"]
    ):
        rh, ra = ratings[h], ratings[a]
        hf = 0.0 if bool(neutral) else hfa
        elo_diff = (rh + hf) - ra
        exp_home = 1.0 / (1.0 + 10 ** (-elo_diff / 400.0))
        res_home = 1.0 if gh > ga else (0.5 if gh == ga else 0.0)
        mult = _gd_multiplier(abs(int(gh) - int(ga)))
        delta = k * mult * (res_home - exp_home)
        ratings[h] = rh + delta
        ratings[a] = ra - delta

        sup = float(gh - ga)
        sxy += elo_diff * sup
        sxx += elo_diff * elo_diff

    beta = sxy / sxx if sxx else 0.0
    return dict(ratings), beta


def elo_win_probability(elo_home: float, elo_away: float, home_field: float = 0.0) -> float:
    """Probabilidad de victoria local según Elo (regla estándar)."""
    diff = (elo_home + home_field) - elo_away
    return 1.0 / (1.0 + 10 ** (-diff / 400.0))
