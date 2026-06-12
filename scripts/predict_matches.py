"""Predicciones de marcador: partidos de hoy y toda la fase de grupos.

Para cada partido calcula goles esperados, probabilidades 1/X/2 y los marcadores
más probables, usando el modelo mezclado Dixon-Coles + Elo. La localía solo se
aplica a anfitriones (México A1, Canadá B1, EE.UU. D1) en sus partidos.
"""
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.blended import build_blended_predictor
from src.simulation.match import MAX_GOALS
from src.utils.config import load_groups, load_settings

# Nombres en español (para mostrar). Reusa el mapa del exportador web si crece.
ES = {
    "Mexico": "México", "South Africa": "Sudáfrica", "South Korea": "Corea del Sur",
    "Czech Republic": "Chequia", "Canada": "Canadá", "United States": "EE.UU.",
    "Turkey": "Turquía", "Curaçao": "Curazao", "Ivory Coast": "Costa de Marfil",
    "Netherlands": "Países Bajos", "Japan": "Japón", "Germany": "Alemania",
    "Spain": "España", "Brazil": "Brasil", "Belgium": "Bélgica", "Croatia": "Croacia",
    "England": "Inglaterra", "France": "Francia", "Morocco": "Marruecos",
    "Saudi Arabia": "Arabia Saudita", "Egypt": "Egipto", "Iran": "Irán",
    "New Zealand": "Nueva Zelanda", "Cape Verde": "Cabo Verde", "Senegal": "Senegal",
    "Norway": "Noruega", "Algeria": "Argelia", "Austria": "Austria", "Jordan": "Jordania",
    "Portugal": "Portugal", "DR Congo": "RD Congo", "Uzbekistan": "Uzbekistán",
    "Panama": "Panamá", "Ghana": "Ghana", "Scotland": "Escocia", "Haiti": "Haití",
    "Switzerland": "Suiza", "Qatar": "Catar", "Bosnia and Herzegovina": "Bosnia",
    "Sweden": "Suecia", "Tunisia": "Túnez", "Australia": "Australia", "Iraq": "Irak",
    "Paraguay": "Paraguay", "Ecuador": "Ecuador", "Uruguay": "Uruguay",
    "Colombia": "Colombia", "Argentina": "Argentina", "Senegal ": "Senegal",
}

# Partidos de HOY (11 jun 2026). (local, visitante) -- el anfitrión va de local.
TODAY = [("Mexico", "South Africa"), ("South Korea", "Czech Republic")]


def es(t):
    return ES.get(t, t)


def top_scores(grid, n=3):
    arr = np.asarray(grid.grid, dtype=float)
    ncols = arr.shape[1]
    flat = arr.ravel()
    idx = np.argsort(flat)[::-1][:n]
    return [(i // ncols, i % ncols, flat[i]) for i in idx]


def predict(model, home, away, hosts):
    neutral = home not in hosts
    g = model.predict(home, away, max_goals=MAX_GOALS, neutral_venue=neutral)
    scores = top_scores(g, 3)
    likely = scores[0]
    return {
        "local": es(home), "visitante": es(away),
        "sede": "casa" if not neutral else "neutral",
        "xG_local": round(g.home_goal_expectation, 2),
        "xG_visit": round(g.away_goal_expectation, 2),
        "P_local": round(g.home_win, 3),
        "P_empate": round(g.draw, 3),
        "P_visit": round(g.away_win, 3),
        "marcador": f"{likely[0]}-{likely[1]}",
        "top3": " · ".join(f"{h}-{a} ({p*100:.0f}%)" for h, a, p in scores),
    }


def fmt_block(rows):
    for r in rows:
        bar = max([(r["P_local"], r["local"]), (r["P_empate"], "Empate"),
                   (r["P_visit"], r["visitante"])], key=lambda x: x[0])
        print(f"  {r['local']} vs {r['visitante']}  ({r['sede']})")
        print(f"     xG {r['xG_local']}-{r['xG_visit']} | "
              f"1 {r['P_local']*100:.0f}% / X {r['P_empate']*100:.0f}% / 2 {r['P_visit']*100:.0f}%"
              f" | favorito: {bar[1]}")
        print(f"     marcadores probables: {r['top3']}")


def main():
    cfg = load_settings()
    groups = load_groups()
    hosts = set(groups["hosts"])
    df = pd.read_csv("data/processed/matches.csv", parse_dates=["date"])
    model = build_blended_predictor(df, xi=cfg["model"]["xi"],
                                    weight=cfg["model"]["elo_blend_weight"])

    print("=" * 60)
    print("PARTIDOS DE HOY — 11 de junio de 2026")
    print("=" * 60)
    fmt_block([predict(model, h, a, hosts) for h, a in TODAY])

    print("\n" + "=" * 60)
    print("FASE DE GRUPOS — los 72 partidos")
    print("=" * 60)
    all_rows = []
    for g, teams in groups["groups"].items():
        print(f"\n--- Grupo {g} ---")
        rows = []
        for a, b in combinations(teams, 2):
            # El anfitrión juega de local; si ninguno lo es, da igual (sede neutral).
            home, away = (b, a) if b in hosts else (a, b)
            rows.append(predict(model, home, away, hosts))
        fmt_block(rows)
        for r in rows:
            r["grupo"] = g
        all_rows.extend(rows)

    out = Path("outputs/reports/group_predictions.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(all_rows).to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nTabla completa -> {out}")


if __name__ == "__main__":
    main()
