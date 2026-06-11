"""Descarga de datos: histórico de partidos (Kaggle) y ratings Elo (eloratings.net).

El histórico de Kaggle (Mart Jürisoo) requiere la API de Kaggle configurada
(~/.kaggle/kaggle.json). Los TSV de Elo se bajan con un simple GET.
"""
from __future__ import annotations

from pathlib import Path

import requests

ELO_WORLD_URL = "https://www.eloratings.net/World.tsv"
KAGGLE_DATASET = "martj42/international-football-results-from-1872-to-2017"


def download_elo(dest: str | Path) -> Path:
    """Descarga el ranking Elo global actual (World.tsv)."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(ELO_WORLD_URL, timeout=30)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return dest


def download_results(dest_dir: str | Path) -> Path:
    """Descarga el histórico de partidos vía la API de Kaggle.

    Requiere `pip install kaggle` y credenciales en ~/.kaggle/kaggle.json.
    """
    from kaggle.api.kaggle_api_extended import KaggleApi

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(KAGGLE_DATASET, path=str(dest_dir), unzip=True)
    return dest_dir / "results.csv"


if __name__ == "__main__":
    print("Descargando Elo...")
    print(download_elo("data/raw/world_elo.tsv"))
    print("Descargando histórico de partidos...")
    print(download_results("data/raw"))
