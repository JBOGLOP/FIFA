"""Predicciones de marcador: partidos de hoy y toda la fase de grupos.

Imprime un resumen, guarda un CSV y exporta docs/data/matches.json (para el
dashboard y para publicar en la hoja). La localía solo se aplica a anfitriones.
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
from src.simulation.match import MAX_GOALS
from src.utils.config import load_groups, load_settings, load_yaml

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
    "Colombia": "Colombia", "Argentina": "Argentina",
}

# "Hoy" se calcula con la fecha real del sistema (auto-actualiza cada día).
TODAY_DATE = date.today().isoformat()


def es(t):
    return ES.get(t, t)


def top_scores(grid, n=3):
    arr = np.asarray(grid.grid, dtype=float)
    ncols = arr.shape[1]
    flat = arr.ravel()
    idx = np.argsort(flat)[::-1][:n]
    return [(int(i // ncols), int(i % ncols), float(flat[i])) for i in idx]


def predict(model, home, away, hosts):
    neutral = home not in hosts
    g = model.predict(home, away, max_goals=MAX_GOALS, neutral_venue=neutral)
    scores = top_scores(g, 3)
    p1, px, p2 = g.home_win, g.draw, g.away_win
    fav = max([(p1, es(home)), (px, "Empate"), (p2, es(away))], key=lambda x: x[0])[1]
    return {
        "home": home, "away": away, "home_es": es(home), "away_es": es(away),
        "venue": "casa" if not neutral else "neutral",
        "xg_home": round(g.home_goal_expectation, 2),
        "xg_away": round(g.away_goal_expectation, 2),
        "p1": round(p1 * 100, 1), "px": round(px * 100, 1), "p2": round(p2 * 100, 1),
        "fav": fav,
        "score": f"{scores[0][0]}-{scores[0][1]}",
        "top": [{"s": f"{h}-{a}", "p": round(p * 100, 1)} for h, a, p in scores],
    }


def build_rows(model, groups, hosts):
    """Usa el calendario oficial (config/fixtures.yaml). El anfitrión juega de local."""
    team_group = {t: g for g, ts in groups["groups"].items() for t in ts}
    fixtures = load_yaml("fixtures.yaml")["fixtures"]

    rows = []
    for fx in fixtures:
        lh, la = fx["home"], fx["away"]
        # El anfitrión recibe la localía aunque la ficha lo liste como visitante.
        home, away = (la, lh) if (la in hosts and lh not in hosts) else (lh, la)
        r = predict(model, home, away, hosts)
        r["group"] = team_group.get(home) or team_group.get(away, "")
        r["date"] = fx["date"]
        r["today"] = fx["date"] == TODAY_DATE
        rows.append(r)

    # Jornada = orden de la fecha dentro de cada grupo (J1/J2/J3).
    dates_by_group = defaultdict(set)
    for r in rows:
        dates_by_group[r["group"]].add(r["date"])
    rank = {g: {d: i + 1 for i, d in enumerate(sorted(ds))} for g, ds in dates_by_group.items()}
    for r in rows:
        r["matchday"] = rank[r["group"]][r["date"]]

    rows.sort(key=lambda r: (r["date"], r["group"]))
    return rows


def print_summary(rows):
    today = [r for r in rows if r["today"]]
    print("=" * 56, f"\nPARTIDOS DE HOY — {TODAY_DATE}\n" + "=" * 56)
    for r in today:
        print(f"  {r['home_es']} vs {r['away_es']} ({r['venue']}): {r['score']} | "
              f"1 {r['p1']:.0f}% / X {r['px']:.0f}% / 2 {r['p2']:.0f}% | fav: {r['fav']}")
    print("\n" + "=" * 56, "\nFASE DE GRUPOS\n" + "=" * 56)
    cur = None
    for r in rows:
        if r["group"] != cur:
            cur = r["group"]; print(f"\n--- Grupo {cur} ---")
        print(f"  {r['home_es']} {r['score']} {r['away_es']}  "
              f"({r['p1']:.0f}/{r['px']:.0f}/{r['p2']:.0f}) fav: {r['fav']}")


def main():
    cfg = load_settings()
    groups = load_groups()
    hosts = set(groups["hosts"])
    df = pd.read_csv("data/processed/matches.csv", parse_dates=["date"])
    model = build_blended_predictor(df, xi=cfg["model"]["xi"],
                                    weight=cfg["model"]["elo_blend_weight"])

    rows = build_rows(model, groups, hosts)
    print_summary(rows)

    # CSV detallado
    flat = [{**{k: v for k, v in r.items() if k != "top"},
             "top3": " · ".join(f"{t['s']} ({t['p']}%)" for t in r["top"])} for r in rows]
    csv_out = Path("outputs/reports/group_predictions.csv")
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(flat).to_csv(csv_out, index=False, encoding="utf-8-sig")

    # JSON para el dashboard
    payload = {"meta": {"generated": date.today().isoformat(),
                        "model": f"Dixon-Coles (xi={cfg['model']['xi']}) + Elo "
                                 f"(w={cfg['model']['elo_blend_weight']})"},
               "matches": rows}
    json_out = Path("docs/data/matches.json")
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nCSV -> {csv_out}\nJSON -> {json_out}")


if __name__ == "__main__":
    main()
