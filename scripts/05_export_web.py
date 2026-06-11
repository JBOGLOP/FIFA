"""Paso 5 — Exporta los resultados de la simulación a docs/data/predictions.json.

Reúne las probabilidades (CSV de la simulación), la estructura de grupos, el árbol
del bracket y los metadatos de banderas/nombres en un único JSON que consume el
dashboard estático de docs/.
"""
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import load_settings, load_yaml

# Nombres en español para la UI.
ES = {
    "Mexico": "México", "South Africa": "Sudáfrica", "South Korea": "Corea del Sur",
    "Czech Republic": "Chequia", "Canada": "Canadá", "Bosnia and Herzegovina": "Bosnia",
    "Qatar": "Catar", "Switzerland": "Suiza", "Brazil": "Brasil", "Morocco": "Marruecos",
    "Haiti": "Haití", "Scotland": "Escocia", "United States": "Estados Unidos",
    "Paraguay": "Paraguay", "Australia": "Australia", "Turkey": "Turquía",
    "Germany": "Alemania", "Curaçao": "Curazao", "Ivory Coast": "Costa de Marfil",
    "Ecuador": "Ecuador", "Netherlands": "Países Bajos", "Japan": "Japón",
    "Sweden": "Suecia", "Tunisia": "Túnez", "Belgium": "Bélgica", "Egypt": "Egipto",
    "Iran": "Irán", "New Zealand": "Nueva Zelanda", "Spain": "España",
    "Cape Verde": "Cabo Verde", "Saudi Arabia": "Arabia Saudita", "Uruguay": "Uruguay",
    "France": "Francia", "Senegal": "Senegal", "Iraq": "Irak", "Norway": "Noruega",
    "Argentina": "Argentina", "Algeria": "Argelia", "Austria": "Austria",
    "Jordan": "Jordania", "Portugal": "Portugal", "DR Congo": "RD Congo",
    "Uzbekistan": "Uzbekistán", "Colombia": "Colombia", "England": "Inglaterra",
    "Croatia": "Croacia", "Ghana": "Ghana", "Panama": "Panamá",
}


def main() -> None:
    cfg = load_settings()
    groups = load_yaml("groups.yaml")  # sin alias: nombres "bonitos" originales
    groups_resolved = load_yaml("groups.yaml")
    bracket = load_yaml("bracket.yaml")
    flags = load_yaml("flags.yaml")

    df = pd.read_csv("outputs/simulations/tournament_probabilities.csv")

    # team (dataset) -> grupo y confederación
    team_group, team_conf = {}, {}
    for g, teams in groups_resolved["groups"].items():
        for t in teams:
            team_group[t] = g
    for conf, teams in groups_resolved.get("confederations", {}).items():
        for t in teams:
            team_conf[t] = conf

    def meta(team: str) -> dict:
        return {"flag": flags.get(team, ""), "es": ES.get(team, team)}

    teams = []
    for _, r in df.iterrows():
        t = r["team"]
        teams.append({
            "team": t, **meta(t),
            "group": team_group.get(t, ""), "conf": team_conf.get(t, ""),
            "group_win": round(float(r["group_win"]), 4),
            "runner_up": round(float(r["runner_up"]), 4),
            "best_third": round(float(r["best_third"]), 4),
            "qualified": round(float(r["qualified"]), 4),
            "reach_R16": round(float(r["reach_R16"]), 4),
            "reach_QF": round(float(r["reach_QF"]), 4),
            "reach_SF": round(float(r["reach_SF"]), 4),
            "reach_final": round(float(r["reach_final"]), 4),
            "champion": round(float(r["champion"]), 4),
        })

    by_name = {x["team"]: x for x in teams}

    # Grupos para las tarjetas: equipos con su prob de ganar/clasificar/3º
    groups_out = {}
    for g, members in groups_resolved["groups"].items():
        rows = sorted((by_name[m] for m in members if m in by_name),
                      key=lambda x: x["group_win"], reverse=True)
        groups_out[g] = [{"team": x["team"], "es": x["es"], "flag": x["flag"],
                          "group_win": x["group_win"], "qualified": x["qualified"],
                          "best_third": x["best_third"]} for x in rows]

    # Favorito por grupo (para etiquetar las ranuras del bracket)
    group_favorite = {g: rows[0] for g, rows in groups_out.items() if rows}

    payload = {
        "meta": {
            "n_iterations": cfg["simulation"]["n_iterations"],
            "generated": date.today().isoformat(),
            "model": f"Dixon-Coles (xi={cfg['model']['xi']}) + Elo blend "
                     f"(w={cfg['model']['elo_blend_weight']})",
        },
        "teams": sorted(teams, key=lambda x: x["champion"], reverse=True),
        "groups": groups_out,
        "group_favorite": group_favorite,
        "bracket": {
            "round_of_32": bracket["round_of_32"],
            "knockout_rounds": bracket["knockout_rounds"],
            "third_allowed": bracket["third_allowed"],
        },
    }

    out = Path("docs/data/predictions.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exportado {len(teams)} equipos -> {out}")


if __name__ == "__main__":
    main()
