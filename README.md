# Predictor Mundial FIFA 2026 🏆

Modelo predictivo de resultados de la Copa Mundial FIFA 2026 (48 equipos, 104 partidos)
basado en **Dixon-Coles** con regularización **Elo** y simulación **Monte Carlo** del torneo.
Incluye **dashboard web** (GitHub Pages) e **integración bidireccional con Google Sheets**.

### 🌐 Dashboard en vivo: **https://jboglop.github.io/FIFA/**

## Objetivo

1. Estimar fuerzas de ataque/defensa por selección a partir del histórico internacional.
2. Predecir el marcador de cada partido (distribución de goles) con Dixon-Coles.
3. Simular el torneo completo (grupos → R32 con 8 mejores terceros → final) 10.000 veces
   para obtener probabilidades de avance y de título.

## Resultados actuales (favoritos al título)

| # | Selección | Campeón | Final | Semis |
|---|---|---|---|---|
| 1 | 🇦🇷 Argentina | 18.6% | 27.7% | 40.4% |
| 2 | 🇪🇸 España | 15.3% | 24.9% | 37.0% |
| 3 | 🇧🇷 Brasil | 10.1% | 18.7% | 33.4% |
| 4 | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra | 8.6% | 15.8% | 29.0% |
| 5 | 🇫🇷 Francia | 7.8% | 15.1% | 27.5% |

## Estructura del proyecto

```
.
├── config/             # groups, settings, bracket, flags, secrets (local)
├── data/{raw,interim,processed,external}/   # datos (no versionados)
├── src/
│   ├── data/           # descarga, preprocesado y cliente de Google Sheets
│   ├── features/       # cálculo de Elo desde el histórico
│   ├── models/         # Dixon-Coles, mezcla con Elo, evaluación (RPS)
│   ├── simulation/     # partidos, grupos, eliminatorias, Monte Carlo
│   └── utils/          # carga de configuración
├── scripts/            # pipeline ejecutable (01→05) + utilidades
├── docs/               # dashboard estático (GitHub Pages)
├── appscript/          # código y guía del Apps Script de BD_fifa
├── outputs/            # resultados de simulación e informes (no versionados)
└── tests/              # pytest
```

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> El histórico de partidos ya está incluido (carpeta `archive/`, copiado a `data/raw/`).
> En Windows, ejecuta siempre con `$env:PYTHONUTF8=1` para evitar errores de consola.

## Pipeline (orden de ejecución)

```powershell
$env:PYTHONUTF8=1
python scripts/02_build_dataset.py        # construye el dataset de entrenamiento
python scripts/optimize_xi.py             # (opcional) calibra el decaimiento xi por RPS
python scripts/optimize_blend.py          # (opcional) calibra el peso de mezcla Elo por RPS
python scripts/03_train_model.py          # ajusta el modelo y predice partidos de ejemplo
python scripts/04_simulate_tournament.py  # Monte Carlo del torneo (10.000 iteraciones)
python scripts/predict_matches.py         # predicción de marcadores (hoy + fase de grupos)
python scripts/05_export_web.py           # genera docs/data/predictions.json (dashboard)
```

> `scripts/01_download_data.py` descarga datos frescos (Kaggle + Elo), pero NO es necesario:
> los datos ya están en local y el modelo calcula el Elo del propio dataset.

## Modelo

- **Dixon-Coles** con decaimiento temporal (`xi=0.0008`, calibrado por RPS out-of-sample).
- **Localía solo para anfitriones** (EE.UU./México/Canadá) vía `neutral_venue`.
- **Regularización con Elo** (`elo_blend_weight=0.2`): mezcla la supremacía Dixon-Coles
  con la del Elo (calculado del histórico) para corregir el desbalance entre confederaciones.
- **Simulador del torneo**: grupos con desempates FIFA → 8 mejores terceros (matching
  bipartito) → **bracket oficial** de FIFA → eliminatorias con penales ponderados.

## Dashboard (GitHub Pages)

Sitio estático en [docs/](docs/), publicado desde la rama `main`, carpeta `/docs`.
Cinco vistas: **Favoritos**, **Partidos** (hoy + grupos), **Probabilidades por ronda**
(heatmap), **Grupos** y **Cuadro**. Se alimenta de:

- `docs/data/predictions.json` ← `scripts/05_export_web.py`
- `docs/data/matches.json` ← `scripts/predict_matches.py`

Para actualizarlo: regenera los JSON y `git push` (Pages reconstruye en ~1 min).

## Integración con Google Sheets (BD_fifa)

Flujo **bidireccional** vía Apps Script (sin credenciales de Google en Python). Despliegue:
[appscript/README.md](appscript/README.md). El token va en `config/secrets.yaml` (no versionado)
o en la variable de entorno `FIFA_SHEET_TOKEN`.

```powershell
python scripts/sheet_pull_results.py       # ENTRADA: lee resultados reales de la hoja
python scripts/02_build_dataset.py         #          los incorpora al entrenamiento
python scripts/sheet_push_predictions.py   # SALIDA: publica probabilidades de título
python scripts/sheet_push_matches.py       # SALIDA: publica predicciones de partidos
```

Pestañas de la hoja: `Resultados` (entrada), `Predicciones` y `Partidos` (salida).

> **Nota de red**: en esta máquina el TLS de Python es bloqueado por el firewall/antivirus;
> el cliente recurre automáticamente a `curl` (TLS del sistema). git usa `http.sslBackend
> schannel` por la misma razón.

## Fuentes de datos

- **Histórico de partidos**: Kaggle — *International football results from 1872 to 2026* (Mart Jürisoo)
- **Ratings Elo**: calculados del propio histórico (y eloratings.net opcional)
- **Bracket oficial**: FIFA / Wikipedia *2026 FIFA World Cup knockout stage*
- **Librería de modelado**: [`penaltyblog`](https://penaltyblog.readthedocs.io)

Para una guía completa de arquitectura, decisiones y operación, ver **[HANDOFF.md](HANDOFF.md)**.

## Licencia / atribución

Datos bajo CC BY-SA 4.0 (Kaggle, eloratings.net). Citar fuentes al publicar resultados.
