"""Publica las predicciones de partidos (docs/data/matches.json) en la pestaña Partidos."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.gsheet import push_rows
from src.utils.config import load_settings

TAB = "Partidos"


def main() -> None:
    cfg = load_settings()["gsheet"]
    data = json.loads(Path("docs/data/matches.json").read_text(encoding="utf-8"))

    rows = []
    for m in data["matches"]:
        rows.append({
            "grupo": m["group"],
            "fecha": m["date"],
            "local": m["home_es"],
            "visitante": m["away_es"],
            "sede": m["venue"],
            "marcador_probable": m["score"],
            "xG_local": m["xg_home"],
            "xG_visitante": m["xg_away"],
            "P_local_%": m["p1"],
            "P_empate_%": m["px"],
            "P_visitante_%": m["p2"],
            "favorito": m["fav"],
            "top_marcadores": " · ".join(f"{t['s']} ({t['p']}%)" for t in m["top"]),
        })

    res = push_rows(cfg["endpoint"], rows, sheet=TAB)
    print(f"Publicados {res.get('written')} partidos en la pestaña '{res.get('sheet')}'.")


if __name__ == "__main__":
    main()
