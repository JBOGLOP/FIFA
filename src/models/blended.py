"""Predictor que regulariza Dixon-Coles con Elo (mitiga el efecto confederación).

Idea: el "tempo" del partido (goles totales esperados) lo aporta Dixon-Coles, pero la
SUPREMACÍA (qué equipo es favorito y por cuánto) se mezcla con la que implica el Elo,
que está mejor anclado entre confederaciones. Expone `predict` con la misma firma que
`DixonColesGoalModel.predict`, así que es intercambiable en el simulador y la evaluación.
"""
from __future__ import annotations

import penaltyblog as pb

from ..features.elo import compute_elo
from .dixon_coles import fit_dixon_coles

ELO_BASE = 1500.0
ELO_HFA = 70.0
MIN_LAMBDA = 0.05


class BlendedPredictor:
    def __init__(self, dc_model, elo: dict[str, float], beta: float, rho: float,
                 weight: float, hfa: float = ELO_HFA):
        self.dc = dc_model
        self.elo = elo
        self.beta = beta
        self.rho = rho
        self.w = weight
        self.hfa = hfa

    def predict(self, home: str, away: str, max_goals: int = 10, neutral_venue: bool = False):
        g = self.dc.predict(home, away, max_goals=max_goals, neutral_venue=neutral_venue)
        lam, mu = g.home_goal_expectation, g.away_goal_expectation
        total, s_dc = lam + mu, lam - mu

        hf = 0.0 if neutral_venue else self.hfa
        elo_diff = self.elo.get(home, ELO_BASE) + hf - self.elo.get(away, ELO_BASE)
        s_elo = self.beta * elo_diff

        s = (1 - self.w) * s_dc + self.w * s_elo
        lam2 = max((total + s) / 2.0, MIN_LAMBDA)
        mu2 = max((total - s) / 2.0, MIN_LAMBDA)
        return pb.models.create_dixon_coles_grid(lam2, mu2, rho=self.rho, max_goals=max_goals)


def build_blended_predictor(df, xi: float, weight: float) -> BlendedPredictor:
    """Ajusta Dixon-Coles + Elo sobre `df` y devuelve el predictor mezclado."""
    dc = fit_dixon_coles(df, xi=xi)
    rho = float(dc.get_params()["rho"])
    elo, beta = compute_elo(df)
    return BlendedPredictor(dc, elo, beta, rho, weight)
