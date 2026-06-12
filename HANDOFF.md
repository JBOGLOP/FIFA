# HANDOFF — Predictor Mundial FIFA 2026

Documento de traspaso completo: arquitectura, decisiones de diseño, operación y
puntos delicados del proyecto. Pensado para que cualquiera (o tú dentro de unos meses)
pueda retomarlo sin contexto previo.

- **Repo**: https://github.com/JBOGLOP/FIFA
- **Dashboard en vivo**: https://jboglop.github.io/FIFA/
- **Hoja de datos**: Google Sheet `BD_fifa` (propietario `jwbogoyal@gmail.com`)
- **Estado**: completo y operativo de punta a punta (modelo → simulación → predicciones
  de partido → dashboard público → Google Sheets bidireccional).

---

## 1. Qué hace, en una frase

Estima la fuerza de cada selección a partir del histórico internacional, predice el
marcador de cualquier partido con un modelo **Dixon-Coles regularizado con Elo**, y
**simula el torneo 10.000 veces** (Monte Carlo) para dar probabilidades de avance y título.
Los resultados se publican en un **dashboard web** y en una **Google Sheet**.

## 2. Resultados actuales

Favoritos al título (10.000 simulaciones, semilla fija 42):
Argentina 18.6% · España 15.3% · Brasil 10.1% · Inglaterra 8.6% · Francia 7.8% ·
Portugal 7.0% · Marruecos 5.3% · Colombia 5.0%.

España queda como favorita "natural" (Elo #1 y mercado) pero Argentina lidera por su
posición más favorable en el bracket oficial (España vía grupo H y Argentina vía grupo J
caen en mitades opuestas; solo pueden cruzarse en la final).

## 3. Arquitectura y flujo de datos

```
                  archive/ (CSV Kaggle, 49k partidos)
                         │ copia
                         ▼
   Google Sheet ──GET──► data/raw/results.csv ──┐
   (Resultados)          + data/external/        │ 02_build_dataset
                         sheet_results.csv        ▼
                                          data/processed/matches.csv (11.842 desde 2014)
                                                  │
                         ┌────────────────────────┼─────────────────────────┐
                         ▼                         ▼                         ▼
                  optimize_xi / blend      03_train_model           04_simulate (Monte Carlo)
                  (calibran por RPS)        (modelo + ejemplos)      tournament_probabilities.csv
                                                                          │
                          ┌───────────────────────────────────────────────┤
                          ▼                          ▼                      ▼
                  predict_matches.py          05_export_web.py      sheet_push_*.py ──POST──►
                  matches.json                predictions.json      Google Sheet (Predicciones,
                          │                          │              Partidos)
                          └──────────► docs/ ◄───────┘
                                        │ git push
                                        ▼
                              GitHub Pages (dashboard en vivo)
```

## 4. Entorno

- **Python 3.14.5**, entorno virtual en `.venv`. `penaltyblog 1.11.0` SÍ funciona en 3.14.
- Dependencias en `requirements.txt` (numpy, pandas, scipy, penaltyblog, requests, pyyaml,
  matplotlib/seaborn, pytest, jupyter).
- **Windows**: ejecutar SIEMPRE con `$env:PYTHONUTF8=1` (la consola usa cp1252 y los
  caracteres como `→`/acentos lanzan `UnicodeEncodeError`).
- **Red / TLS (importante)**: el OpenSSL que trae Python 3.14 en esta máquina es
  bloqueado por el firewall/antivirus (`SSLEOFError: UNEXPECTED_EOF`) tanto hacia PyPI
  como hacia `script.google.com`. El TLS del sistema (curl/Schannel) **sí** pasa. Por eso:
  - El cliente de Sheets (`src/data/gsheet.py`) intenta `requests` y, si el TLS falla,
    recurre a `curl`.
  - git está configurado con `http.sslBackend schannel`.

## 5. El modelo

### 5.1 Dixon-Coles con decaimiento temporal
`src/models/dixon_coles.py`. Usa `penaltyblog.models.DixonColesGoalModel`. Cada partido se
pondera por antigüedad con `w = exp(-xi · días)`. **`xi=0.0008`** (calibrado, ver 5.4).
Vida media ≈ 2,4 años: decaimiento suave, correcto para selecciones (juegan poco y espaciado).

### 5.2 Localía solo para anfitriones
penaltyblog soporta `neutral_venue` en el ajuste (array por partido) y en la predicción
(booleano). Se entrena con la columna `neutral` del dataset, así la ventaja de local **γ**
se estima solo con partidos no neutrales (no se infla con clasificatorios de local). Al
predecir el Mundial, la localía se aplica **solo** cuando un anfitrión (EE.UU./México/Canadá)
juega en casa → `predict_wc_match`. Efecto medido: +0,36 goles y +9 pts de prob. de victoria.

### 5.3 Regularización con Elo
`src/features/elo.py` calcula un Elo walk-forward desde el propio histórico (con
multiplicador por diferencia de goles) y calibra `beta` (Elo → goles). `src/models/blended.py`
(`BlendedPredictor`) **mantiene el "tempo"** (goles totales esperados) de Dixon-Coles pero
**mezcla la supremacía** (quién es favorito y por cuánto) con la que implica el Elo:

```
s = (1-w)·s_DC + w·s_Elo      # w = elo_blend_weight = 0.2
λ = (total + s)/2 ; μ = (total - s)/2     → create_dixon_coles_grid(λ, μ, rho)
```

Esto corrige el **desbalance entre confederaciones** (pocos partidos cruzados → Dixon-Coles
infla a CONMEBOL). Antes del blend, Brasil/Argentina salían por encima de España; con el
blend España vuelve a su sitio. Además mejora ligeramente el RPS.

### 5.4 Calibración (RPS)
`src/models/evaluate.py`. Se entrena con el 85% más antiguo y se mide el **Rank Probability
Score** prediciendo el 15% más reciente (out-of-sample). `optimize_xi` y `optimize_blend`
recorren rejillas y eligen el mínimo RPS. Resultado: `xi=0.0008`, `elo_blend_weight=0.2`.

## 6. El simulador del torneo

- **`src/simulation/match.py`** — `MatchSimulator`: muestrea marcadores de la grilla del
  modelo (cachea por (local, visitante, neutral) para no recalcular en cada iteración).
  En eliminatorias, los empates se deciden por "penales" ponderados por la fuerza del modelo.
  ⚠️ La grilla de penaltyblog es `(max_goals, max_goals)`; usar la forma real para el índice.
- **`src/simulation/tournament.py`** — fase de grupos (round-robin) + **desempates FIFA**
  (puntos → dif. goles → goles → head-to-head → sorteo) y selección de mejores terceros.
- **`src/simulation/knockout.py`** — **asignación de los 8 terceros** por matching bipartito
  (algoritmo de Kuhn, respetando los conjuntos permitidos) + simulación del **bracket oficial**.
- **`src/simulation/monte_carlo.py`** — corre N simulaciones y agrega probabilidades por
  equipo (ganar grupo, clasificar, mejor tercero, octavos, cuartos, semis, final, campeón).

## 7. Configuración (`config/`)

| Archivo | Contenido |
|---|---|
| `groups.yaml` | 12 grupos, anfitriones, confederaciones y **alias** de nombres (Czechia→Czech Republic, Curacao→Curaçao). |
| `settings.yaml` | Parámetros: `data.start_date`, `model.xi`, `model.elo_blend_weight`, `simulation.n_iterations`/`seed`, `gsheet.endpoint`/tabs, desempates. |
| `bracket.yaml` | **Bracket oficial FIFA** (partidos 73-104): R32, conjuntos permitidos de terceros y árbol de eliminatorias. |
| `flags.yaml` | Código ISO de cada selección para las banderas (flagcdn.com). |
| `secrets.yaml` | **Local, NO versionado**. `sheet_token` (token del Apps Script). |

## 8. Scripts (`scripts/`)

| Script | Qué hace |
|---|---|
| `01_download_data.py` | Descarga histórico (Kaggle) + Elo. Opcional (datos ya en local). |
| `02_build_dataset.py` | Construye `data/processed/matches.csv`; incorpora `sheet_results.csv` si existe. |
| `optimize_xi.py` | Calibra el decaimiento `xi` por RPS → `outputs/reports/xi_optimization.csv`. |
| `optimize_blend.py` | Calibra el peso de mezcla Elo por RPS → `blend_optimization.csv`. |
| `03_train_model.py` | Ajusta el modelo y muestra predicciones de ejemplo. |
| `04_simulate_tournament.py` | Monte Carlo del torneo → `tournament_probabilities.csv`. |
| `predict_matches.py` | Predice los 72 partidos de grupos (+ hoy) → `matches.json` + CSV. |
| `05_export_web.py` | Genera `docs/data/predictions.json` para el dashboard. |
| `sheet_pull_results.py` | ENTRADA: lee la pestaña `Resultados` → `data/external/sheet_results.csv`. |
| `sheet_push_predictions.py` | SALIDA: publica probabilidades de título en la pestaña `Predicciones`. |
| `sheet_push_matches.py` | SALIDA: publica predicciones de partido en la pestaña `Partidos`. |

## 9. Dashboard (`docs/`)

Sitio estático (HTML + CSS + vanilla JS + Chart.js por CDN), servido por GitHub Pages
desde `main /docs`. Cinco vistas: **Favoritos** (gráfico + tabla), **Partidos** (hoy +
grupos, con xG y barras 1/X/2), **Probabilidades por ronda** (heatmap), **Grupos** y
**Cuadro** (bracket oficial). Consume `data/predictions.json` y `data/matches.json`.
Banderas vía `flagcdn.com`.

> El dashboard usa JSON estáticos, **no** el endpoint de Apps Script: las respuestas de
> Apps Script (ContentService) no llevan cabeceras CORS, así que el navegador no puede
> leerlas (Python/curl sí). El flujo es: Python genera el JSON → git push → Pages.

## 10. Integración Google Sheets (`appscript/` + `src/data/gsheet.py`)

Bidireccional **vía Apps Script** (sin credenciales de Google en Python):

- **`appscript/Code.gs`**: web app con `doGet` (lee una pestaña → JSON), `doPost`
  (escribe filas, exige `TOKEN`) y `setup` (crea pestañas). Desplegado por el usuario;
  ver `appscript/README.md`. El `TOKEN` del editor debe coincidir con `config/secrets.yaml`.
- **`src/data/gsheet.py`**: `fetch_sheet` (GET) y `push_rows` (POST). Token desde
  `FIFA_SHEET_TOKEN` o `config/secrets.yaml`. Transporte: `requests` → fallback `curl`.
- **Pestañas**: `Resultados` (entrada manual del usuario), `Predicciones` y `Partidos` (salida).

### Trampas resueltas (no reintroducir)
1. **TLS de Python bloqueado** → fallback a `curl` (ver §4).
2. **curl + stdin = HTTP 411** (chunked sin Content-Length) → el body va a un archivo
   temporal con `--data-binary @file`.
3. **`-X POST` re-postea en el redirect 302** de Apps Script (→ 411) → NO usar `-X POST`;
   con `--data-binary` curl hace POST y sigue el 302 como GET (lo que Apps Script espera).

## 11. Git / GitHub / Pages

- Repo `JBOGLOP/FIFA`, rama `main`. git con `http.sslBackend schannel` (ver §4).
- Credenciales en Git Credential Manager (cacheadas; el push autentica solo).
- **GitHub Pages** activado vía API (source: `main` /docs). Build automático en ~1 min al hacer push.
- `.gitignore` excluye: `.venv/`, `data/`, `outputs/`, `archive/`, `archive.zip`, `.claude/`,
  `config/secrets.yaml`, y los punteros de Google Drive (`*.gsheet`, etc.). **SÍ** se versiona
  `docs/` incluido `docs/data/*.json`.

## 12. Cómo hacer tareas comunes

**Ciclo diario (un comando):** añade los resultados del día a `config/real_results.yaml`
y ejecuta `python scripts/run_daily.py` (flags `--no-sheet`, `--no-git`). Encadena:
`load_real_results` → `02_build_dataset` → `04_simulate_tournament` → `predict_matches`
→ `05_export_web` → push a Sheets → commit + push a GitHub. "Hoy" se detecta con la fecha
del sistema. El git solo commitea si hay cambios (resultados nuevos cambian el JSON).

**Recalcular manualmente (paso a paso):**
```powershell
$env:PYTHONUTF8=1
python scripts/load_real_results.py     # resultados reales -> dataset + hoja
python scripts/02_build_dataset.py
python scripts/04_simulate_tournament.py
python scripts/predict_matches.py
python scripts/05_export_web.py
git add -A; git commit -m "Actualiza"; git push   # refresca el dashboard
python scripts/sheet_push_predictions.py
python scripts/sheet_push_matches.py
```

**Resultados reales**: viven en `config/real_results.yaml` (versionado, acumulado).
`load_real_results.py` los escribe a `data/external/sheet_results.csv` (lo recoge
`02_build_dataset`) y los publica en la pestaña `Resultados`. Alternativa manual: el
usuario los escribe directamente en la pestaña `Resultados` y se usa `sheet_pull_results.py`.

**Cambiar parámetros:** edita `config/settings.yaml` (`model.xi`, `model.elo_blend_weight`,
`simulation.n_iterations`, `simulation.random_seed`).

## 13. Limitaciones conocidas

- **Calendario**: `config/fixtures.yaml` tiene las fechas locales oficiales de los 72
  partidos de grupos (fuente ESPN). `predict_matches.py` las usa y marca "hoy" con la
  fecha real del sistema. Falta el horario (hora) y la sede de cada partido.
- **Penales**: modelados con la fuerza relativa del modelo, no con datos reales de tandas.
- **Sin xG por jugador / lesiones / forma individual**: el modelo es a nivel selección.
- **Datos**: el dataset llega hasta la fecha de descarga; refrescar con `01_download_data.py`
  (necesita red) o metiendo resultados por la hoja.

## 14. Tests

`pytest` (5 tests): validan la configuración (12 grupos × 4 = 48 equipos), el matching de
terceros, el orden de mejores terceros y la simulación de un grupo con un modelo simulado.
```powershell
$env:PYTHONUTF8=1; .\.venv\Scripts\python.exe -m pytest -q
```

## 15. Trabajo futuro (ideas)

- Calendario completo de partidos (fechas/sedes) para la vista de "próximos partidos".
- Validación walk-forward del torneo entero contra Mundiales pasados.
- Intervalos de confianza por bootstrap sobre las probabilidades.
- Actualización automática durante el torneo (cron que lee la hoja, recalcula y publica).
- `doGet` con JSONP o un proxy para que el dashboard consuma la hoja en vivo (saltar CORS).
