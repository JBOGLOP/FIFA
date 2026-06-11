"""Paso 1 — Descarga el histórico de partidos y los ratings Elo."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.download import download_elo, download_results


def main() -> None:
    print("-> Elo (eloratings.net)...")
    print("  ", download_elo("data/raw/world_elo.tsv"))
    print("-> Historico de partidos (Kaggle)...")
    try:
        print("  ", download_results("data/raw"))
    except Exception as exc:  # noqa: BLE001
        print("  [!] Falló la descarga de Kaggle:", exc)
        print("      Configura kaggle.json o descarga results.csv a mano en data/raw/.")


if __name__ == "__main__":
    main()
