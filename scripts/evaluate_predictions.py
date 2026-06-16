"""Backtest walk-forward sobre los partidos ya jugados del Mundial.

Para cada resultado real (en orden cronológico) ajusta el modelo SOLO con datos
previos a ese partido, predice y compara con lo ocurrido. Mide:
  - Acierto 1X2 (la opción más probable coincide con el resultado).
  - RPS medio (calidad probabilística; menor es mejor).
  - Marcador exacto acertado.

Es una evaluación honesta (sin fuga de datos) de cómo "aprende" el modelo.
"""
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.preprocess import load_results, to_model_frame
from src.models.blended import build_blended_predictor
from src.models.evaluate import rps, _outcome
from src.simulation.match import MAX_GOALS
from src.utils.config import load_groups, load_settings, load_yaml

OUTCOME = {0: "1", 1: "X", 2: "2"}


def main() -> None:
    cfg = load_settings()
    xi, w = cfg["model"]["xi"], cfg["model"]["elo_blend_weight"]
    hosts = set(load_groups()["hosts"])
    reals = sorted(load_yaml("real_results.yaml")["results"], key=lambda r: r["date"])

    # Dataset base SIN los partidos del Mundial (evita fuga de datos).
    base = to_model_frame(load_results(cfg["data"]["results_csv"], cfg["data"]["start_date"]))
    played = {(r["date"], frozenset((r["home"], r["away"]))) for r in reals}
    keep = ~base.apply(
        lambda x: (x["date"].strftime("%Y-%m-%d"),
                   frozenset((x["team_home"], x["team_away"]))) in played, axis=1)
    history = base[keep].reset_index(drop=True)

    # Agrupa por fecha: se ajusta UNA vez por jornada (predice ese día con el modelo
    # entrenado solo con días anteriores; sigue siendo walk-forward sin fuga de datos).
    by_date = defaultdict(list)
    for r in reals:
        by_date[r["date"]].append(r)

    rows, scores = [], []
    for d in sorted(by_date):
        model = build_blended_predictor(history, xi=xi, weight=w)
        new_hist = []
        for r in by_date[d]:
            if r["away"] in hosts and r["home"] not in hosts:
                mh, ma, gh, ga = r["away"], r["home"], r["as"], r["hs"]
            else:
                mh, ma, gh, ga = r["home"], r["away"], r["hs"], r["as"]
            neutral = mh not in hosts
            g = model.predict(mh, ma, max_goals=MAX_GOALS, neutral_venue=neutral)
            probs = (g.home_win, g.draw, g.away_win)
            pick, actual = int(np.argmax(probs)), _outcome(gh, ga)
            arr = np.asarray(g.grid); ps = np.unravel_index(arr.argmax(), arr.shape)
            sc = rps(probs, actual); scores.append(sc)
            rows.append({
                "fecha": r["date"], "partido": f"{r['home']} {r['hs']}-{r['as']} {r['away']}",
                "pred_1X2": OUTCOME[pick], "real_1X2": OUTCOME[actual],
                "acierto_1X2": bool(pick == actual),
                "marcador_pred": f"{ps[0]}-{ps[1]}" if mh == r["home"] else f"{ps[1]}-{ps[0]}",
                "acierto_exacto": bool(ps[0] == gh and ps[1] == ga), "RPS": round(sc, 3),
            })
            new_hist.append({"date": pd.Timestamp(d), "team_home": mh, "team_away": ma,
                             "goals_home": gh, "goals_away": ga, "neutral": neutral})
        history = pd.concat([history, pd.DataFrame(new_hist)], ignore_index=True)

    df = pd.DataFrame(rows)
    n = len(df)
    hits, exact, mrps = int(df["acierto_1X2"].sum()), int(df["acierto_exacto"].sum()), float(np.mean(scores))
    print(df.to_string(index=False))
    print(f"\nPartidos evaluados: {n}")
    print(f"Acierto 1X2:  {hits}/{n}  ({hits/n*100:.0f}%)")
    print(f"Marcador exacto: {exact}/{n}  ({exact/n*100:.0f}%)")
    print(f"RPS medio: {mrps:.3f}  (baseline azar ~0.22; menor es mejor)")

    Path("outputs/reports").mkdir(parents=True, exist_ok=True)
    df.to_csv("outputs/reports/prediction_accuracy.csv", index=False, encoding="utf-8-sig")

    # JSON para el dashboard
    payload = {
        "meta": {"generated": date.today().isoformat(), "n": n, "hits_1x2": hits,
                 "pct_1x2": round(hits / n * 100, 1) if n else 0,
                 "exact_hits": exact, "mean_rps": round(mrps, 3)},
        "matches": rows,
    }
    Path("docs/data/accuracy.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("JSON -> docs/data/accuracy.json")


if __name__ == "__main__":
    main()
