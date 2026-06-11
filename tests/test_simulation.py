"""Tests de la lógica de simulación (sin depender del modelo entrenado)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.simulation.knockout import assign_thirds
from src.simulation.match import MatchSimulator
from src.simulation.tournament import TeamStats, rank_best_thirds, simulate_group
from src.utils.config import load_yaml


class FakeGrid:
    """Grilla determinista: equipo más fuerte (por 'rating') marca más."""

    def __init__(self, home_strong: bool):
        n = 4
        self.grid = np.zeros((n, n))
        # marcador casi seguro 2-0 a favor del local si home_strong, si no 0-2
        self.grid[2, 0] = 1.0 if home_strong else 0.0
        self.grid[0, 2] = 0.0 if home_strong else 1.0
        self.home_win = 1.0 if home_strong else 0.0
        self.away_win = 0.0 if home_strong else 1.0


class FakeModel:
    """Modelo simulado: gana siempre el equipo alfabéticamente menor."""

    def predict(self, home, away, max_goals=15, normalize=True, neutral_venue=False):
        return FakeGrid(home_strong=(home < away))


def test_assign_thirds_respects_constraints():
    bracket = load_yaml("bracket.yaml")
    allowed = bracket["third_allowed"]
    qualifying = ["A", "B", "C", "D", "E", "F", "G", "H"]
    assignment = assign_thirds(qualifying, allowed)
    # Cada ranura recibe un grupo permitido y todos los grupos son distintos
    assert len(set(assignment.values())) == len(assignment)
    for slot, grp in assignment.items():
        assert grp in allowed[slot]


def test_rank_best_thirds_orders_by_points():
    rng = np.random.default_rng(0)
    thirds = [TeamStats("X", "A", points=6), TeamStats("Y", "B", points=3),
              TeamStats("Z", "C", points=9)]
    best = rank_best_thirds(thirds, rng, n=2)
    assert [t.team for t in best] == ["Z", "X"]


def test_simulate_group_returns_full_ranking():
    rng = np.random.default_rng(0)
    sim = MatchSimulator(FakeModel(), hosts=set(), rng=rng)
    ranking, stats = simulate_group("A", ["Alpha", "Bravo", "Charlie", "Delta"], sim)
    assert len(ranking) == 4
    assert ranking[0] == "Alpha"  # gana siempre el menor alfabéticamente
    assert sum(s.points for s in stats.values()) > 0
