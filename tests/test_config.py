"""Tests básicos de configuración."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import load_groups, load_settings


def test_groups_has_12_groups_of_4():
    groups = load_groups()["groups"]
    assert len(groups) == 12
    assert all(len(teams) == 4 for teams in groups.values())
    # 48 equipos en total
    all_teams = [t for teams in groups.values() for t in teams]
    assert len(all_teams) == 48
    assert len(set(all_teams)) == 48  # sin duplicados


def test_settings_loads():
    cfg = load_settings()
    assert cfg["simulation"]["n_iterations"] > 0
    assert "xi" in cfg["model"]
