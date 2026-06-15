"""Carga los resultados reales (config/real_results.yaml) al dataset y a la hoja.

Escribe data/external/sheet_results.csv (lo recoge 02_build_dataset) y publica la
pestaña Resultados de BD_fifa. Idempotente: representa SIEMPRE el acumulado completo.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.gsheet import push_rows
from src.utils.config import load_settings, load_yaml


def main(push_sheet: bool = True) -> None:
    results = load_yaml("real_results.yaml")["results"]
    if not results:
        print("Sin resultados que cargar.")
        return

    # 1) Dataset: data/external/sheet_results.csv (esquema del histórico)
    df = pd.DataFrame([{
        "date": r["date"], "home_team": r["home"], "away_team": r["away"],
        "home_score": r["hs"], "away_score": r["as"],
        "tournament": "FIFA World Cup", "city": "", "country": "",
        "neutral": r["neutral"],
    } for r in results])
    dest = Path("data/external/sheet_results.csv")
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False)
    print(f"{len(df)} resultados -> {dest}")

    # 2) Hoja: pestaña Resultados (best-effort; el CSV ya quedó escrito)
    if push_sheet:
        cfg = load_settings()["gsheet"]
        rows = [{"date": r["date"], "home_team": r["home"], "away_team": r["away"],
                 "home_score": r["hs"], "away_score": r["as"], "neutral": r["neutral"]}
                for r in results]
        try:
            res = push_rows(cfg["endpoint"], rows, sheet=cfg["results_tab"])
            print(f"Hoja '{res.get('sheet')}': {res.get('written')} filas.")
        except Exception as exc:  # noqa: BLE001
            print(f"[!] No se pudo publicar en la hoja (se continúa): {exc}")


if __name__ == "__main__":
    main(push_sheet="--no-sheet" not in sys.argv)


