"""Carga de configuración del proyecto."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"


def load_yaml(name: str) -> dict:
    """Carga un YAML de la carpeta config/ por nombre de archivo."""
    with open(CONFIG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_groups() -> dict:
    """Carga los grupos aplicando los alias de nombres (-> nombres del dataset)."""
    cfg = load_yaml("groups.yaml")
    aliases = cfg.get("aliases", {})

    def fix(team: str) -> str:
        return aliases.get(team, team)

    cfg["groups"] = {g: [fix(t) for t in teams] for g, teams in cfg["groups"].items()}
    cfg["hosts"] = [fix(t) for t in cfg["hosts"]]
    if "confederations" in cfg:
        cfg["confederations"] = {
            c: [fix(t) for t in teams] for c, teams in cfg["confederations"].items()
        }
    return cfg


def load_settings() -> dict:
    return load_yaml("settings.yaml")
