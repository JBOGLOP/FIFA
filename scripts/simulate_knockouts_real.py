"""Simula SOLO las eliminatorias partiendo del cuadro REAL del Round of 32.

Usa config/knockout_bracket.yaml (cruces reales) + el árbol de bracket.yaml. Respeta
los partidos de eliminatorias ya jugados (de real_results.yaml). Monte Carlo -> prob.
de avance y título por equipo + predicción de cada cruce del R32.
Salida: docs/data/knockout.json.
"""
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.blended import build_blended_predictor
from src.simulation.match import MatchSimulator
from src.utils.config import load_settings, load_yaml
from src.utils.display import es, flag

GROUP_END = "2026-06-27"
ROUND = {**{i: "R32" for i in range(73, 89)}, **{i: "R16" for i in range(89, 97)},
         **{i: "QF" for i in range(97, 101)}, 101: "SF", 102: "SF", 104: "F"}
REACH = {"R16": ["reach_R16"], "QF": ["reach_R16", "reach_QF"],
         "SF": ["reach_R16", "reach_QF", "reach_SF"],
         "F": ["reach_R16", "reach_QF", "reach_SF", "reach_final"]}
STAGES = ["reach_R16", "reach_QF", "reach_SF", "reach_final", "champion"]


def played_knockouts(reals):
    """{frozenset(equipos): ganador} para cruces de eliminatorias ya jugados."""
    out = {}
    for r in reals:
        if r["date"] <= GROUP_END:
            continue
        winner = r["home"] if r["hs"] >= r["as"] else r["away"]
        out[frozenset((r["home"], r["away"]))] = winner
    return out


def main() -> None:
    cfg = load_settings()
    bracket = load_yaml("bracket.yaml")
    r32 = load_yaml("knockout_bracket.yaml")["round_of_32"]
    reals = load_yaml("real_results.yaml")["results"]
    played = played_knockouts(reals)
    n = cfg["simulation"]["n_iterations"]
    champ_match = bracket["champion_match"]

    df = pd.read_csv("data/processed/matches.csv", parse_dates=["date"])
    model = build_blended_predictor(df, xi=cfg["model"]["xi"], weight=cfg["model"]["elo_blend_weight"])
    rng = np.random.default_rng(cfg["simulation"]["random_seed"])
    sim = MatchSimulator(model, hosts=set(), rng=rng)  # eliminatorias = neutral

    counts = defaultdict(lambda: defaultdict(int))
    r32_home_adv = defaultdict(int)  # veces que avanza el "home" de cada cruce R32

    for _ in range(n):
        mw, reached = {}, {}
        for m in r32:
            home, away = m["home"], m["away"]
            reached[home] = reached[away] = "R32"
            key = frozenset((home, away))
            if key in played:
                w = played[key]
            else:
                w = sim.play_knockout(home, away, neutral=True)
            if w == home:
                r32_home_adv[m["id"]] += 1
            mw[m["id"]] = w
        for m in bracket["knockout_rounds"]:
            home, away = mw[m["home"]], mw[m["away"]]
            rnd = ROUND[m["id"]]
            reached[home] = reached[away] = rnd
            key = frozenset((home, away))
            mw[m["id"]] = played[key] if key in played else sim.play_knockout(home, away, neutral=True)
        champ = mw[champ_match]
        for team, rnd in reached.items():
            for hito in REACH.get(rnd, []):
                counts[team][hito] += 1
        counts[champ]["champion"] += 1

    teams = []
    for team, c in counts.items():
        row = {"team": team, "es": es(team), "flag": flag(team)}
        row.update({s: round(c.get(s, 0) / n, 4) for s in STAGES})
        teams.append(row)
    teams.sort(key=lambda x: x["champion"], reverse=True)

    r32_out = []
    for m in r32:
        key = frozenset((m["home"], m["away"]))
        r32_out.append({
            "id": m["id"], "home": m["home"], "away": m["away"],
            "home_es": es(m["home"]), "away_es": es(m["away"]),
            "home_flag": flag(m["home"]), "away_flag": flag(m["away"]),
            "p_home": round(r32_home_adv[m["id"]] / n, 3),
            "played": key in played, "winner": played.get(key, ""),
            "winner_es": es(played[key]) if key in played else "",
        })

    payload = {
        "meta": {"generated": date.today().isoformat(), "n_iterations": n,
                 "note": "Simulación sembrada con el cuadro real del Round of 32."},
        "champion": teams, "round_of_32": r32_out,
    }
    Path("docs/data/knockout.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Favoritos al título (cuadro real de eliminatorias):")
    for t in teams[:10]:
        print(f"  {t['es']}: {t['champion']*100:.1f}%  (final {t['reach_final']*100:.0f}%)")
    print("\n-> docs/data/knockout.json")


if __name__ == "__main__":
    main()
