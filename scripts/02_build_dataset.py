"""Paso 2 — Limpia el histórico y construye el dataset de entrenamiento."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.preprocess import load_results, to_model_frame
from src.utils.config import load_settings


def main() -> None:
    cfg = load_settings()
    df = load_results(cfg["data"]["results_csv"], start_date=cfg["data"]["start_date"])
    model_df = to_model_frame(df)
    out = Path("data/processed/matches.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    model_df.to_csv(out, index=False)
    print(f"Dataset construido: {len(model_df)} partidos -> {out}")


if __name__ == "__main__":
    main()
