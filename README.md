# Predictor Mundial FIFA 2026 🏆

Modelo predictivo de resultados de la Copa Mundial FIFA 2026 (48 equipos, 104 partidos)
basado en **Poisson / Dixon-Coles** con ratings **Elo** y simulación **Monte Carlo** del torneo.

## Objetivo

1. Estimar fuerzas de ataque/defensa por selección a partir del histórico de partidos internacionales.
2. Predecir el marcador de cada partido (distribución de goles) con Dixon-Coles + decaimiento temporal.
3. Simular el torneo completo (fase de grupos → R32 con 8 mejores terceros → final) 10.000+ veces
   para obtener probabilidades de avance y de título.

## Estructura del proyecto

```
.
├── config/            # Configuración: equipos, grupos, calendario, parámetros del modelo
├── data/
│   ├── raw/           # Datos descargados sin tocar (CSV de Kaggle, TSV de Elo)
│   ├── interim/       # Datos en proceso de limpieza
│   ├── processed/     # Datasets listos para entrenar
│   └── external/      # Rankings FIFA, cuotas, fuentes auxiliares
├── notebooks/         # Exploración y prototipos (Jupyter)
├── src/
│   ├── data/          # Descarga y preprocesado de datos
│   ├── features/      # Cálculo de Elo y features
│   ├── models/        # Dixon-Coles / Poisson
│   ├── simulation/    # Simulador del torneo + Monte Carlo
│   └── utils/         # Utilidades (nombres de equipos, desempates FIFA)
├── outputs/
│   ├── figures/       # Gráficos
│   ├── reports/       # Informes
│   └── simulations/   # Resultados de las simulaciones
├── scripts/           # Scripts ejecutables de punta a punta (pipeline)
└── tests/             # Tests
```

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Pipeline (orden de ejecución)

```powershell
python scripts/01_download_data.py        # Descarga histórico + Elo (datos ya en archive/)
python scripts/02_build_dataset.py        # Limpia y construye el dataset de entrenamiento
python scripts/optimize_xi.py             # (opcional) calibra el decaimiento temporal xi por RPS
python scripts/optimize_blend.py          # (opcional) calibra el peso de mezcla Elo por RPS
python scripts/03_train_model.py          # Ajusta el modelo y predice partidos de ejemplo
python scripts/04_simulate_tournament.py  # Monte Carlo del torneo (10.000 iteraciones)
```

> En Windows, ejecuta con `$env:PYTHONUTF8=1` para evitar errores de codificación en consola.

### Modelo

- **Dixon-Coles** con decaimiento temporal (`xi`, calibrado por RPS).
- **Localía solo para anfitriones** (EE.UU./México/Canadá) vía `neutral_venue`.
- **Regularización con Elo** (`elo_blend_weight`): mezcla la supremacía Dixon-Coles con
  la del Elo calculado del histórico, para corregir el desbalance entre confederaciones.

### Dashboard (GitHub Pages)

El sitio estático vive en [docs/](docs/) y se publica con GitHub Pages (rama `main`,
carpeta `/docs`). Genera su JSON con `python scripts/05_export_web.py`.

### Integración con Google Sheets (BD_fifa)

Flujo bidireccional vía Apps Script (sin credenciales de Google en Python). Ver
[appscript/README.md](appscript/README.md) para el despliegue.

```powershell
$env:FIFA_SHEET_TOKEN = "tu-token"            # el mismo del Apps Script
python scripts/sheet_pull_results.py          # entrada: lee resultados reales de la hoja
python scripts/02_build_dataset.py            # los incorpora al entrenamiento
python scripts/04_simulate_tournament.py      # recalcula
python scripts/sheet_push_predictions.py      # salida: publica predicciones en la hoja
```

## Fuentes de datos

- **Histórico de partidos**: Kaggle — *International football results from 1872 to 2026* (Mart Jürisoo)
- **Ratings Elo**: eloratings.net (`World.tsv`)
- **Ranking FIFA**: inside.fifa.com
- **Librería de modelado**: [`penaltyblog`](https://penaltyblog.readthedocs.io)

## Licencia / atribución

Datos bajo CC BY-SA 4.0 (Kaggle, eloratings.net). Citar fuentes al publicar resultados.
