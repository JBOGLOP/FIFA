"""Calcula el cuadro REAL del Round of 32 a partir de los resultados de grupos.

Tallya las clasificaciones (puntos, dif. goles, goles + head-to-head), saca los 8
mejores terceros, asigna terceros a las ranuras del bracket y resuelve los 16 cruces
reales del R32 -> config/knockout_bracket.yaml.
"""
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.simulation.knockout import assign_thirds
from src.simulation.tournament import TeamStats, _rank_teams, rank_best_thirds
from src.utils.config import load_groups, load_yaml

GROUP_END = "2026-06-27"  # último día de fase de grupos


def main() -> None:
    groups = load_groups()
    bracket = load_yaml("bracket.yaml")
    reals = load_yaml("real_results.yaml")["results"]

    team_group = {t: g for g, ts in groups["groups"].items() for t in ts}
    group_results = reals_by_group(reals, team_group)

    # Clasificación por grupo (criterios FIFA; rng fijo para desempates residuales).
    rng = np.random.default_rng(0)
    winners, runners, thirds_stats = {}, {}, []
    third_team_of_group = {}
    for g, teams in groups["groups"].items():
        stats, results = group_results[g]
        ranking = _rank_teams(stats, results, rng)
        winners[g], runners[g] = ranking[0], ranking[1]
        third_team_of_group[g] = ranking[2]
        thirds_stats.append(stats[ranking[2]])

    best8 = rank_best_thirds(thirds_stats, rng, n=8)
    qualifying_groups = [s.group for s in best8]
    assignment = assign_thirds(qualifying_groups, bracket["third_allowed"])
    third_for_slot = {f"W{slot}": third_team_of_group[grp] for slot, grp in assignment.items()}

    def resolve(token, home_slot):
        if token.startswith("T:"):
            return third_for_slot[home_slot]
        if token.startswith("W"):
            return winners[token[1:]]
        if token.startswith("R"):
            return runners[token[1:]]
        raise ValueError(token)

    r32 = []
    for m in bracket["round_of_32"]:
        home = resolve(m["home"], m["home"])
        away = resolve(m["away"], m["home"])
        r32.append({"id": m["id"], "home": home, "away": away})

    # Salida
    out = {"round_of_32": r32}
    Path("config/knockout_bracket.yaml").write_text(
        yaml.safe_dump(out, allow_unicode=True, sort_keys=False), encoding="utf-8")

    print("Clasificados por grupo (1º / 2º / 3º):")
    for g in sorted(groups["groups"]):
        print(f"  {g}: {winners[g]} / {runners[g]} / {third_team_of_group[g]}")
    print("\nMejores 8 terceros:", [s.team for s in best8])
    print("\nRound of 32 (cruces reales):")
    for m in r32:
        print(f"  M{m['id']}: {m['home']} vs {m['away']}")
    print("\n-> config/knockout_bracket.yaml")


def reals_by_group(reals, team_group):
    """Construye {grupo: (stats_por_equipo, results_dict)} desde los resultados de grupos."""
    from collections import defaultdict
    stats = defaultdict(dict)
    results = defaultdict(dict)
    for r in reals:
        if r["date"] > GROUP_END:
            continue
        h, a = r["home"], r["away"]
        g = team_group.get(h)
        if g is None or team_group.get(a) != g:
            continue  # no es partido de grupo
        for t in (h, a):
            if t not in stats[g]:
                stats[g][t] = TeamStats(t, g)
        hs, as_ = int(r["hs"]), int(r["as"])
        stats[g][h].gf += hs; stats[g][h].ga += as_
        stats[g][a].gf += as_; stats[g][a].ga += hs
        if hs > as_:
            stats[g][h].points += 3
        elif as_ > hs:
            stats[g][a].points += 3
        else:
            stats[g][h].points += 1; stats[g][a].points += 1
        results[g][(h, a)] = (hs, as_)
    return {g: (stats[g], results[g]) for g in stats}


if __name__ == "__main__":
    main()
