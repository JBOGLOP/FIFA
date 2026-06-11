"""Evaluación del modelo: Rank Probability Score (RPS) y optimización de xi.

El RPS (Epstein, 1969) mide la calidad de pronósticos ordinales (victoria local /
empate / victoria visitante). Cuanto menor, mejor. Es la métrica estándar para
modelos de resultados de fútbol (Constantinou & Fenton, 2012).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .dixon_coles import fit_dixon_coles


def rps(probs: tuple[float, float, float], outcome: int) -> float:
    """RPS para 3 resultados ordenados [local, empate, visitante].

    `probs` = (p_local, p_empate, p_visitante); `outcome` = 0 local, 1 empate, 2 visitante.
    """
    obs = [0.0, 0.0, 0.0]
    obs[outcome] = 1.0
    cum_p = np.cumsum(probs)
    cum_o = np.cumsum(obs)
    return float(np.sum((cum_p[:-1] - cum_o[:-1]) ** 2) / (len(probs) - 1))


def _outcome(goals_home: int, goals_away: int) -> int:
    if goals_home > goals_away:
        return 0
    if goals_home == goals_away:
        return 1
    return 2


def evaluate_xi(df: pd.DataFrame, xi: float, valid_frac: float = 0.15) -> dict:
    """Ajusta Dixon-Coles con un xi dado sobre el tramo de entrenamiento y mide
    el RPS medio prediciendo el tramo de validación (out-of-sample).

    Solo evalúa partidos cuyos dos equipos aparecen en el entrenamiento.
    """
    df = df.sort_values("date").reset_index(drop=True)
    split = int(len(df) * (1 - valid_frac))
    train, valid = df.iloc[:split], df.iloc[split:]

    model = fit_dixon_coles(train, xi=xi)
    known = set(train["team_home"]).union(train["team_away"])

    scores, skipped, errored = [], 0, 0
    for _, m in valid.iterrows():
        if m["team_home"] not in known or m["team_away"] not in known:
            skipped += 1
            continue
        try:
            grid = model.predict(
                m["team_home"], m["team_away"], neutral_venue=bool(m["neutral"])
            )
        except ValueError:
            # La corrección Dixon-Coles puede dar una celda negativa en casos extremos.
            errored += 1
            continue
        probs = (grid.home_win, grid.draw, grid.away_win)
        scores.append(rps(probs, _outcome(m["goals_home"], m["goals_away"])))

    return {
        "xi": xi,
        "mean_rps": float(np.mean(scores)),
        "n_evaluated": len(scores),
        "n_skipped": skipped,
        "n_errored": errored,
    }


def optimize_xi(df: pd.DataFrame, xi_grid: list[float], valid_frac: float = 0.15) -> pd.DataFrame:
    """Evalúa cada xi del grid y devuelve los resultados ordenados por RPS (mejor primero)."""
    rows = [evaluate_xi(df, xi, valid_frac) for xi in xi_grid]
    return pd.DataFrame(rows).sort_values("mean_rps").reset_index(drop=True)


def _score_predictor(predictor, valid: pd.DataFrame, known: set) -> dict:
    """RPS medio de un predictor (con .predict) sobre el tramo de validación."""
    scores, skipped, errored = [], 0, 0
    for _, m in valid.iterrows():
        if m["team_home"] not in known or m["team_away"] not in known:
            skipped += 1
            continue
        try:
            grid = predictor.predict(
                m["team_home"], m["team_away"], neutral_venue=bool(m["neutral"])
            )
        except ValueError:
            errored += 1
            continue
        probs = (grid.home_win, grid.draw, grid.away_win)
        scores.append(rps(probs, _outcome(m["goals_home"], m["goals_away"])))
    return {"mean_rps": float(np.mean(scores)), "n_evaluated": len(scores),
            "n_skipped": skipped, "n_errored": errored}


def evaluate_blend(df: pd.DataFrame, weight: float, xi: float, valid_frac: float = 0.15) -> dict:
    """Ajusta el predictor mezclado (Dixon-Coles+Elo) en train y mide RPS out-of-sample."""
    from .blended import build_blended_predictor

    df = df.sort_values("date").reset_index(drop=True)
    split = int(len(df) * (1 - valid_frac))
    train, valid = df.iloc[:split], df.iloc[split:]
    predictor = build_blended_predictor(train, xi=xi, weight=weight)
    known = set(train["team_home"]).union(train["team_away"])
    res = _score_predictor(predictor, valid, known)
    res["weight"] = weight
    return res


def optimize_blend(df: pd.DataFrame, weights: list[float], xi: float,
                   valid_frac: float = 0.15) -> pd.DataFrame:
    """Evalúa cada peso de mezcla Elo y ordena por RPS (mejor primero)."""
    rows = [evaluate_blend(df, w, xi, valid_frac) for w in weights]
    cols = ["weight", "mean_rps", "n_evaluated", "n_skipped", "n_errored"]
    return pd.DataFrame(rows)[cols].sort_values("mean_rps").reset_index(drop=True)
