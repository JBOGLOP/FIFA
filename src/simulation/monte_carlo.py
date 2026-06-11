"""Motor Monte Carlo: simula el torneo completo N veces y agrega probabilidades."""
from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd

from .knockout import simulate_knockouts
from .match import MatchSimulator
from .tournament import rank_best_thirds, simulate_group

# Columnas de salida: probabilidad de alcanzar cada hito.
STAGES = ["group_win", "runner_up", "best_third", "qualified",
          "reach_R16", "reach_QF", "reach_SF", "reach_final", "champion"]

# Mapea la "ronda máxima alcanzada" (de knockout) a los hitos acumulativos.
_REACH = {
    "R16": ["reach_R16"],
    "QF": ["reach_R16", "reach_QF"],
    "SF": ["reach_R16", "reach_QF", "reach_SF"],
    "F": ["reach_R16", "reach_QF", "reach_SF", "reach_final"],
}


def run_simulations(model, groups: dict, hosts, bracket: dict,
                    n_iterations: int = 10000, seed: int = 42) -> pd.DataFrame:
    """Corre N simulaciones y devuelve un DataFrame de probabilidades por equipo."""
    rng = np.random.default_rng(seed)
    sim = MatchSimulator(model, set(hosts), rng)
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for _ in range(n_iterations):
        winners, runners, third_team_of_group = {}, {}, {}
        all_thirds = []

        for g, teams in groups.items():
            ranking, stats = simulate_group(g, teams, sim)
            winners[g], runners[g], third_team_of_group[g] = ranking[0], ranking[1], ranking[2]
            counts[ranking[0]]["group_win"] += 1
            counts[ranking[1]]["runner_up"] += 1
            counts[ranking[0]]["qualified"] += 1
            counts[ranking[1]]["qualified"] += 1
            all_thirds.append(stats[ranking[2]])

        best8 = rank_best_thirds(all_thirds, rng, n=8)
        qualifying_groups = [s.group for s in best8]
        for s in best8:
            counts[s.team]["best_third"] += 1
            counts[s.team]["qualified"] += 1

        reached, champion = simulate_knockouts(
            winners, runners, third_team_of_group, qualifying_groups, bracket, sim
        )
        for team, rnd in reached.items():
            for hito in _REACH.get(rnd, []):
                counts[team][hito] += 1
        counts[champion]["champion"] += 1

    return _to_frame(counts, n_iterations)


def _to_frame(counts: dict, n: int) -> pd.DataFrame:
    rows = []
    for team, c in counts.items():
        row = {"team": team}
        row.update({s: c.get(s, 0) / n for s in STAGES})
        rows.append(row)
    df = pd.DataFrame(rows).fillna(0.0)
    return df.sort_values("champion", ascending=False).reset_index(drop=True)
