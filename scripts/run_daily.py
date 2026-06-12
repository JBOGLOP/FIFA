"""Ciclo diario en un comando: resultados reales -> modelo -> dashboard + hoja + GitHub.

Uso:
    python scripts/run_daily.py              # todo (dataset, simula, publica, git push)
    python scripts/run_daily.py --no-sheet   # sin publicar en Google Sheets
    python scripts/run_daily.py --no-git     # sin commit/push a GitHub

Antes de correrlo, añade los resultados del día en config/real_results.yaml.
"""
import argparse
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def run(script: str, *args: str) -> None:
    subprocess.run([PY, str(ROOT / "scripts" / script), *args],
                   check=True, cwd=ROOT, env=ENV)


def run_git() -> None:
    files = ["config/real_results.yaml", "docs/data/predictions.json", "docs/data/matches.json"]
    subprocess.run(["git", "add", *files], cwd=ROOT, env=ENV)
    # ¿hay algo que commitear?
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT, env=ENV)
    if staged.returncode == 0:
        print("  Sin cambios para GitHub.")
        return
    subprocess.run(["git", "commit", "-m", f"Actualiza predicciones ({date.today().isoformat()})"],
                   cwd=ROOT, env=ENV, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, env=ENV, check=True)
    print("  Dashboard actualizado en https://jboglop.github.io/FIFA/")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-sheet", action="store_true", help="no publicar en Google Sheets")
    ap.add_argument("--no-git", action="store_true", help="no hacer commit/push a GitHub")
    opts = ap.parse_args()

    steps = [
        ("Cargar resultados reales", "load_real_results.py",
         ["--no-sheet"] if opts.no_sheet else []),
        ("Construir dataset", "02_build_dataset.py", []),
        ("Simular torneo (Monte Carlo)", "04_simulate_tournament.py", []),
        ("Predecir partidos", "predict_matches.py", []),
        ("Exportar dashboard (JSON)", "05_export_web.py", []),
    ]
    if not opts.no_sheet:
        steps += [
            ("Publicar predicciones en la hoja", "sheet_push_predictions.py", []),
            ("Publicar partidos en la hoja", "sheet_push_matches.py", []),
        ]

    for i, (label, script, args) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {label}…")
        run(script, *args)

    if not opts.no_git:
        print("\n[git] Publicando en GitHub…")
        run_git()

    print("\n✓ Ciclo diario completado.")


if __name__ == "__main__":
    main()
