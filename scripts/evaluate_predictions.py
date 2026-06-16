"""Backtest walk-forward sobre los partidos ya jugados del Mundial.

Para cada resultado real (en orden cronológico) ajusta el modelo SOLO con datos
previos a ese partido, predice y compara con lo ocurrido. Mide:
  - Acierto 1X2 (la opción más probable coincide con el resultado).
  - RPS medio (calidad probabilística; menor es mejor).
  - Marcador exacto acertado.

Es una evaluación honesta (sin fuga de datos) de cómo "aprende" el modelo.
"""
import sys
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
    reals = load_yaml("real_results.yaml")["results"]
    reals = sorted(reals, key=lambda r: r["date"])

    # Dataset base SIN los partidos del Mundial (evita fuga de datos).
    base = to_model_frame(load_results(cfg["data"]["results_csv"], cfg["data"]["start_date"]))
    played = {(r["date"], frozenset((r["home"], r["away"]))) for r in reals}
    keep = ~base.apply(
        lambda x: (x["date"].strftime("%Y-%m-%d"),
                   frozenset((x["team_home"], x["team_away"]))) in played, axis=1)
    history = base[keep].reset_index(drop=True)

    rows, scores = [], []
    for r in reals:
        # Orientación del modelo: el anfitrión juega de local.
        if r["away"] in hosts and r["home"] not in hosts:
            mh, ma, gh, ga = r["away"], r["home"], r["as"], r["hs"]
        else:
            mh, ma, gh, ga = r["home"], r["away"], r["hs"], r["as"]
        neutral = mh not in hosts

        model = build_blended_predictor(history, xi=xi, weight=w)
        g = model.predict(mh, ma, max_goals=MAX_GOALS, neutral_venue=neutral)
        probs = (g.home_win, g.draw, g.away_win)
        pick = int(np.argmax(probs))
        actual = _outcome(gh, ga)
        arr = np.asarray(g.grid); pred_score = np.unravel_index(arr.argmax(), arr.shape)
        r_score = rps(probs, actual)
        scores.append(r_score)
        rows.append({
            "fecha": r["date"], "partido": f"{r['home']} {r['hs']}-{r['as']} {r['away']}",
            "pred_1X2": OUTCOME[pick], "real_1X2": OUTCOME[actual],
            "acierto_1X2": pick == actual,
            "marcador_pred": f"{pred_score[0]}-{pred_score[1]}" if (mh == r["home"])
                             else f"{pred_score[1]}-{pred_score[0]}",
            "acierto_exacto": (pred_score[0] == gh and pred_score[1] == ga),
            "RPS": round(r_score, 3),
        })
        # Añade el partido jugado al historial para el siguiente (aprendizaje incremental).
        history = pd.concat([history, pd.DataFrame([{
            "date": pd.Timestamp(r["date"]), "team_home": mh, "team_away": ma,
            "goals_home": gh, "goals_away": ga, "neutral": neutral}])], ignore_index=True)

    df = pd.DataFrame(rows)
    n = len(df)
    print(df.to_string(index=False))
    print(f"\nPartidos evaluados: {n}")
    print(f"Acierto 1X2:  {df['acierto_1X2'].sum()}/{n}  ({df['acierto_1X2'].mean()*100:.0f}%)")
    print(f"Marcador exacto: {df['acierto_exacto'].sum()}/{n}  ({df['acierto_exacto'].mean()*100:.0f}%)")
    print(f"RPS medio: {np.mean(scores):.3f}  (baseline azar ~0.22; menor es mejor)")

    out = Path("outputs/reports/prediction_accuracy.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nDetalle -> {out}")


if __name__ == "__main__":
    main()
