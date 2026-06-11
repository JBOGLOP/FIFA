"""Cliente de la hoja BD_fifa vía el web app de Apps Script (doGet/doPost).

No necesita credenciales de Google: usa el endpoint /exec. El token de escritura se
lee de la variable de entorno FIFA_SHEET_TOKEN (no se versiona).
"""
from __future__ import annotations

import os

import pandas as pd
import requests

TOKEN_ENV = "FIFA_SHEET_TOKEN"


def fetch_sheet(endpoint: str, sheet: str = "Resultados") -> pd.DataFrame:
    """Lee una pestaña de la hoja y la devuelve como DataFrame (GET)."""
    resp = requests.get(endpoint, params={"sheet": sheet}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Apps Script: {data['error']}")
    return pd.DataFrame(data.get("rows", []))


def push_rows(endpoint: str, rows: list[dict], sheet: str = "Predicciones",
              token: str | None = None) -> dict:
    """Escribe filas en una pestaña (POST). Sobrescribe el contenido de la pestaña."""
    token = token or os.environ.get(TOKEN_ENV)
    if not token:
        raise RuntimeError(f"Falta el token: define la variable de entorno {TOKEN_ENV}")
    resp = requests.post(
        endpoint,
        json={"token": token, "sheet": sheet, "rows": rows},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raise RuntimeError(f"Apps Script: {data['error']}")
    return data
