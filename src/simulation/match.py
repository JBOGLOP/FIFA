"""Simulador de partidos: muestrea marcadores desde el Dixon-Coles ajustado.

Cachea la matriz de probabilidades por (local, visitante, neutral) para no recalcular
la predicción en cada una de las miles de iteraciones Monte Carlo.
"""
from __future__ import annotations

import numpy as np

MAX_GOALS = 10


class MatchSimulator:
    def __init__(self, model, hosts: set[str], rng: np.random.Generator):
        self.model = model
        self.hosts = set(hosts)
        self.rng = rng
        self._cache: dict[tuple[str, str, bool], np.ndarray] = {}

    def _flat_probs(self, home: str, away: str, neutral: bool):
        """Devuelve (probs_planas_normalizadas, n_columnas) cacheado."""
        key = (home, away, neutral)
        cached = self._cache.get(key)
        if cached is None:
            grid = self.model.predict(home, away, max_goals=MAX_GOALS, neutral_venue=neutral)
            arr = np.asarray(grid.grid, dtype=float)
            ncols = arr.shape[1]
            flat = arr.ravel()
            flat = flat / flat.sum()  # renormaliza por si hay recortes numéricos
            cached = (flat, ncols)
            self._cache[key] = cached
        return cached

    def sample_score(self, home: str, away: str, neutral: bool = True) -> tuple[int, int]:
        """Muestrea un marcador (goles_local, goles_visitante)."""
        flat, ncols = self._flat_probs(home, away, neutral)
        idx = int(self.rng.choice(flat.size, p=flat))
        return idx // ncols, idx % ncols

    def _win_probs_no_draw(self, home: str, away: str, neutral: bool) -> float:
        """Probabilidad de que gane el LOCAL condicionada a que no haya empate."""
        grid = self.model.predict(home, away, max_goals=MAX_GOALS, neutral_venue=neutral)
        hw, aw = grid.home_win, grid.away_win
        return hw / (hw + aw)

    def play_match(self, home: str, away: str, neutral: bool = True) -> tuple[str, int, int]:
        """Partido de grupos: devuelve (ganador_o_'draw', goles_local, goles_visit)."""
        gh, ga = self.sample_score(home, away, neutral)
        if gh > ga:
            return home, gh, ga
        if ga > gh:
            return away, gh, ga
        return "draw", gh, ga

    def play_knockout(self, home: str, away: str, neutral: bool = True) -> str:
        """Eliminatoria: si hay empate en 90'+prórroga, se decide por 'penales'.

        Los penales se modelan con la fuerza relativa del propio modelo
        (prob. de victoria condicionada a no-empate), evitando un 50/50 plano.
        """
        gh, ga = self.sample_score(home, away, neutral)
        if gh > ga:
            return home
        if ga > gh:
            return away
        # Empate -> penales ponderados por la fuerza del modelo
        p_home = self._win_probs_no_draw(home, away, neutral)
        return home if self.rng.random() < p_home else away
