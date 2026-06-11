"""Fase de grupos, desempates FIFA, selección de mejores terceros y eliminatorias.

Formato 48 equipos: 12 grupos de 4 -> 12 primeros + 12 segundos + 8 mejores terceros
= 32 equipos al Round of 32, luego octavos, cuartos, semis y final.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .match import MatchSimulator


@dataclass
class TeamStats:
    team: str
    group: str = ""
    points: int = 0
    gf: int = 0
    ga: int = 0

    @property
    def gd(self) -> int:
        return self.gf - self.ga


def _decide_venue(a: str, b: str, hosts: set[str]) -> tuple[str, str, bool]:
    """Devuelve (local, visitante, neutral). Solo hay localía si un anfitrión juega."""
    if a in hosts:
        return a, b, False
    if b in hosts:
        return b, a, False
    return a, b, True


def _h2h_key(team: str, subset: list[str], results: dict) -> tuple[int, int, int]:
    """Mini-tabla (puntos, dif. goles, goles) solo entre los equipos empatados."""
    pts = gf = ga = 0
    for (h, a), (gh, ga_) in results.items():
        if h == team and a in subset:
            gf += gh; ga += ga_
            pts += 3 if gh > ga_ else (1 if gh == ga_ else 0)
        elif a == team and h in subset:
            gf += ga_; ga += gh
            pts += 3 if ga_ > gh else (1 if gh == ga_ else 0)
    return (pts, gf - ga, gf)


def _rank_teams(stats: dict[str, TeamStats], results: dict, rng: np.random.Generator) -> list[str]:
    """Ordena equipos por criterios FIFA: puntos, GD, GF, head-to-head y, si persiste, azar."""
    teams = list(stats)
    rand = {t: rng.random() for t in teams}  # desempate final (sorteo)

    def primary(t: str):
        s = stats[t]
        return (s.points, s.gd, s.gf)

    teams.sort(key=lambda t: (primary(t), _h2h_key(t, teams, results), rand[t]), reverse=True)

    # Resuelve head-to-head solo dentro de bloques con (puntos, GD, GF) idénticos
    ordered: list[str] = []
    i = 0
    while i < len(teams):
        j = i + 1
        while j < len(teams) and primary(teams[j]) == primary(teams[i]):
            j += 1
        block = teams[i:j]
        if len(block) > 1:
            block.sort(key=lambda t: (_h2h_key(t, block, results), rand[t]), reverse=True)
        ordered.extend(block)
        i = j
    return ordered


def simulate_group(group: str, teams: list[str], sim: MatchSimulator):
    """Simula un grupo (todos contra todos). Devuelve (ranking, stats_por_equipo)."""
    stats = {t: TeamStats(t, group) for t in teams}
    results: dict[tuple[str, str], tuple[int, int]] = {}

    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            home, away, neutral = _decide_venue(teams[i], teams[j], sim.hosts)
            _, gh, ga = sim.play_match(home, away, neutral=neutral)
            results[(home, away)] = (gh, ga)
            stats[home].gf += gh; stats[home].ga += ga
            stats[away].gf += ga; stats[away].ga += gh
            if gh > ga:
                stats[home].points += 3
            elif ga > gh:
                stats[away].points += 3
            else:
                stats[home].points += 1; stats[away].points += 1

    ranking = _rank_teams(stats, results, sim.rng)
    return ranking, stats


def rank_best_thirds(thirds: list[TeamStats], rng: np.random.Generator, n: int = 8) -> list[TeamStats]:
    """Selecciona los n mejores terceros por puntos, GD, GF (y azar si persiste el empate)."""
    rand = {s.team: rng.random() for s in thirds}
    thirds = sorted(thirds, key=lambda s: (s.points, s.gd, s.gf, rand[s.team]), reverse=True)
    return thirds[:n]
