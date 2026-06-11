"""Modelo Dixon-Coles con decaimiento temporal y localía solo en sedes no neutrales.

penaltyblog estima un único parámetro de ventaja de local (home advantage) y permite
activarlo/desactivarlo por partido vía `neutral_venue`. Como ~90% de los partidos del
Mundial son en sede neutral, la localía solo debe contar para los anfitriones jugando
en casa. Entrenamos con TODOS los partidos pero marcando los neutrales para no inflar γ.
"""
from __future__ import annotations

import pandas as pd


def fit_dixon_coles(df: pd.DataFrame, xi: float = 0.0008):
    """Ajusta un Dixon-Coles ponderando por antigüedad y respetando sedes neutrales.

    Espera columnas: date, team_home, team_away, goals_home, goals_away, neutral.
    `neutral` (bool) desactiva la ventaja de local en ese partido.
    """
    import penaltyblog as pb

    weights = pb.models.dixon_coles_weights(df["date"], xi=xi)
    model = pb.models.DixonColesGoalModel(
        df["goals_home"],
        df["goals_away"],
        df["team_home"],
        df["team_away"],
        weights=weights,
        neutral_venue=df["neutral"].astype(int) if "neutral" in df else None,
    )
    model.fit()
    return model


def predict_match(model, home: str, away: str, neutral: bool = True):
    """Grilla de probabilidades de marcador. Por defecto sede neutral (sin localía)."""
    return model.predict(home, away, neutral_venue=neutral)


def predict_wc_match(model, home: str, away: str, hosts: set[str]):
    """Predice un partido del Mundial: solo hay localía si `home` es anfitrión.

    Pasa el anfitrión como equipo local para que reciba la ventaja; en cualquier
    otro emparejamiento el partido se trata como neutral.
    """
    neutral = home not in hosts
    return model.predict(home, away, neutral_venue=neutral)
