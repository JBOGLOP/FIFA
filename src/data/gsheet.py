"""Cliente de la hoja BD_fifa vía el web app de Apps Script (doGet/doPost).

No necesita credenciales de Google: usa el endpoint /exec. El token de escritura se
lee de la variable de entorno FIFA_SHEET_TOKEN o de config/secrets.yaml (no versionado).

Transporte: intenta `requests`; si el handshake TLS falla (en algunas máquinas el
OpenSSL de Python es bloqueado por antivirus/firewall mientras el TLS del sistema sí
pasa), recurre a `curl` del sistema. Así funciona en cualquier entorno.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import requests

TOKEN_ENV = "FIFA_SHEET_TOKEN"
_SECRETS = Path(__file__).resolve().parents[2] / "config" / "secrets.yaml"


def _resolve_token(token: str | None) -> str | None:
    """Token explícito > variable de entorno > config/secrets.yaml (local)."""
    if token:
        return token
    if os.environ.get(TOKEN_ENV):
        return os.environ[TOKEN_ENV]
    if _SECRETS.exists():
        import yaml
        return (yaml.safe_load(_SECRETS.read_text(encoding="utf-8")) or {}).get("sheet_token")
    return None


def _curl_json(args: list[str], body: bytes | None = None) -> dict:
    """Ejecuta curl (sigue redirecciones) y parsea la salida JSON.

    El body se escribe a un archivo temporal (--data-binary @file) para que curl
    fije Content-Length; leerlo por stdin usaría chunked y Google responde 411.
    """
    curl = shutil.which("curl")
    if not curl:
        raise RuntimeError("curl no disponible para el transporte de respaldo")

    tmp_path = None
    try:
        full = [curl, "-sL", *args]
        if body is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
                tmp.write(body)
                tmp_path = tmp.name
            full += ["--data-binary", f"@{tmp_path}"]
        proc = subprocess.run(full, capture_output=True, timeout=90)
        if proc.returncode != 0:
            raise RuntimeError(f"curl fallo ({proc.returncode}): {proc.stderr.decode(errors='ignore')}")
        return json.loads(proc.stdout.decode("utf-8"))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _get(endpoint: str, params: dict) -> dict:
    try:
        r = requests.get(endpoint, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{endpoint}?{query}" if query else endpoint
        return _curl_json([url])


def _post(endpoint: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    try:
        r = requests.post(endpoint, data=body,
                          headers={"Content-Type": "application/json"}, timeout=60)
        r.raise_for_status()
        return r.json()
    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
        # Sin -X POST: --data-binary ya hace POST en la 1ª petición y, al seguir el
        # 302 de Apps Script, curl cambia a GET (forzar POST en el redirect da 411).
        return _curl_json(["-H", "Content-Type: application/json", endpoint], body=body)


def fetch_sheet(endpoint: str, sheet: str = "Resultados") -> pd.DataFrame:
    """Lee una pestaña de la hoja y la devuelve como DataFrame (GET)."""
    data = _get(endpoint, {"sheet": sheet})
    if data.get("error"):
        raise RuntimeError(f"Apps Script: {data['error']}")
    return pd.DataFrame(data.get("rows", []))


def push_rows(endpoint: str, rows: list[dict], sheet: str = "Predicciones",
              token: str | None = None) -> dict:
    """Escribe filas en una pestaña (POST). Sobrescribe el contenido de la pestaña."""
    token = _resolve_token(token)
    if not token:
        raise RuntimeError(
            f"Falta el token: define {TOKEN_ENV} o config/secrets.yaml (sheet_token)"
        )
    data = _post(endpoint, {"token": token, "sheet": sheet, "rows": rows})
    if data.get("error"):
        raise RuntimeError(f"Apps Script: {data['error']}")
    return data
