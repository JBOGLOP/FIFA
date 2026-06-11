# Guía de investigación: construir un modelo predictivo Poisson/Dixon-Coles en Python para la Copa Mundial FIFA 2026

## TL;DR
- El Mundial 2026 (11 junio–19 julio) tiene 48 equipos en 12 grupos (A–L), 104 partidos en 16 estadios de EE.UU., México y Canadá; los 12 ganadores de grupo, 12 segundos y 8 mejores terceros pasan a unos nuevos dieciseisavos (Round of 32). Todos los grupos y el calendario completo ya están confirmados (sorteo del 5 dic 2025 + repechajes de marzo 2026).
- Para alimentar un Dixon-Coles, la mejor base es el dataset de Kaggle de Mart Jürisoo (49.393 resultados internacionales desde 1872, CSV) combinado con ratings Elo de eloratings.net (TSV descargable directamente) y el paquete Python `penaltyblog`, que ya implementa Dixon-Coles, decaimiento temporal y simulación.
- Los favoritos según mercados y Elo son España (Elo 2.155, #1; cuota ~+450/+475), Argentina (Elo 2.114, #2), Francia (Elo 2.062, #3; +475/+500) e Inglaterra (Elo 2.021, #4; +650/+700); Portugal y Brasil completan el grupo de aspirantes. Noruega (Haaland), Marruecos, Colombia y Croacia son las "dark horses" más citadas.

## Key Findings

1. **Formato y calendario**: 104 partidos del 11 junio al 19 julio 2026. Fase de grupos del 11 al 27 de junio; Round of 32 del 28 junio al 3 julio; octavos 4–7 julio; cuartos 9–11 julio; semifinales 14 y 15 julio; tercer puesto 18 julio; final 19 julio en MetLife Stadium (East Rutherford, NJ). EE.UU. alberga 78 partidos, México y Canadá 13 cada uno.
2. **48 equipos confirmados** en 12 grupos; anfitriones en posiciones predeterminadas: México A1, Canadá B1, EE.UU. D1. Los últimos 6 cupos se decidieron en repechajes de marzo 2026 (Bosnia, Suecia, Türkiye, Chequia vía UEFA; RD Congo e Irak vía repechaje interconfederación). Italia quedó fuera por tercera vez consecutiva.
3. **Datos para el modelo**: existen fuentes gratuitas y de pago bien documentadas: dataset Kaggle de Jürisoo (histórico de resultados), eloratings.net (TSV), rankings FIFA, archivo SPI de FiveThirtyEight (descontinuado pero descargable), y APIs (football-data.org gratis, API-Football desde $19/mes, SportMonks, TheSportsDB).
4. **Software**: `penaltyblog` (PyPI) implementa Poisson, Poisson bivariante, Dixon-Coles, modelos bayesianos, decaimiento temporal Dixon-Coles, ratings Elo/Massey/Colley y scrapers. Hay repos abiertos específicos del Mundial 2026 (Elo + Dixon-Coles + Monte Carlo).
5. **Mejores prácticas**: ponderar partidos por antigüedad (decaimiento exponencial), tratar las sedes neutrales y la ventaja de local solo para los tres anfitriones, ajustar por confederación (datos escasos entre confederaciones), y simular el nuevo formato con las 495 combinaciones de terceros mediante Monte Carlo.

## Details

### 1. Calendario completo del torneo

**Datos generales**: 23.ª edición, primera con 48 equipos. 104 partidos (72 de grupos + 32 de eliminatorias), 39 días, 16 estadios. Partido inaugural: México vs Sudáfrica, 11 junio, Estadio Azteca (Ciudad de México). Final: 19 julio, MetLife Stadium ("New York New Jersey Stadium"), 15:00 ET.

**Fase de grupos (11–27 junio)**. Ejemplos de jornadas confirmadas (todas con asignación de sede tras el calendario del 6 dic 2025):
- 11 jun: México–Sudáfrica (Azteca); Corea del Sur–Chequia (Guadalajara/Zapopan, Estadio Akron).
- 12 jun: Canadá–Bosnia (BMO Field, Toronto); EE.UU.–Paraguay (SoFi, Inglewood).
- 13 jun: Qatar–Suiza (grupo B); Haití–Escocia; Brasil–Marruecos.
- 16 jun: Francia–Senegal (East Rutherford); Iraq–Noruega (Foxborough); Argentina–Argelia (Kansas City); Austria–Jordania.
- El partido nº 1.000 de la historia de los Mundiales será Túnez vs Japón el 21 junio en Monterrey (Estadio BBVA).

**Eliminatorias (estructura del bracket)**. El Round of 32 empareja ganadores de grupo contra mejores terceros, y segundos entre sí, de forma que equipos del mismo grupo no se cruzan hasta cuartos. Ejemplos de partidos confirmados (fechas/sedes):
- 28 jun: 2º A vs 2º B (SoFi, Los Ángeles).
- 29 jun: Ganador C vs 2º F (Houston); Ganador E vs 3º A/B/C/D/F (Foxborough); Ganador F vs 2º C (Monterrey).
- 30 jun: 2º E vs 2º I (Dallas); Ganador I vs 3º C/D/F/G/H (East Rutherford); Ganador A vs 3º C/E/F/H/I (Azteca).
- 1 jul: Ganador L vs 3º E/H/I/J/K (Atlanta); Ganador G vs 3º A/E/H/I/J (Seattle); Ganador D vs 3º B/E/F/I/J (Santa Clara).
- 2 jul: Ganador H vs 2º J (Inglewood); 2º K vs 2º L (Toronto); Ganador B vs 3º E/F/G/I/J (Vancouver).
- 3 jul: 2º D vs 2º G (Dallas); Ganador J vs 2º H (Miami); Ganador K vs 3º D/E/I/J/L (Kansas City).
- Octavos: 4–7 julio (Houston, Filadelfia, East Rutherford, Azteca, Dallas, Seattle, Atlanta, Vancouver).
- Cuartos: 9 jul (Foxborough), 10 jul (Inglewood), 11 jul (Kansas City y Miami).
- Semifinales: 14 jul (AT&T Stadium, Arlington) y 15 jul (Mercedes-Benz, Atlanta).
- Tercer puesto: 18 jul (Miami). Final: 19 jul (MetLife).

**Nota técnica para el modelo**: los emparejamientos exactos de los 8 terceros no se conocen hasta terminar la fase de grupos (27 jun). FIFA define 495 escenarios posibles (uno por cada combinación de 8 grupos clasificados entre los 12). En la API de SportMonks el bracket vive en el endpoint `/v3/football/seasons/26618/brackets`.

### 2. Los 48 equipos y el sorteo por grupos

Botes basados en el ranking FIFA del 19 nov 2025. Anfitriones sembrados (México A1, Canadá B1, EE.UU. D1). Para "equilibrio competitivo", España (#1 en ese ranking) y Argentina (#2) se sortearon en mitades opuestas del cuadro, igual que Francia (#3) e Inglaterra (#4); no pueden cruzarse hasta semifinales.

- **Grupo A**: México, Sudáfrica, Corea del Sur, Chequia
- **Grupo B**: Canadá, Bosnia y Herzegovina, Qatar, Suiza
- **Grupo C**: Brasil, Marruecos, Haití, Escocia
- **Grupo D**: Estados Unidos, Paraguay, Australia, Türkiye
- **Grupo E**: Alemania, Curazao, Costa de Marfil, Ecuador
- **Grupo F**: Países Bajos, Japón, Suecia, Túnez
- **Grupo G**: Bélgica, Egipto, Irán, Nueva Zelanda
- **Grupo H**: España, Cabo Verde, Arabia Saudita, Uruguay
- **Grupo I**: Francia, Senegal, Iraq, Noruega
- **Grupo J**: Argentina, Argelia, Austria, Jordania
- **Grupo K**: Portugal, RD Congo, Uzbekistán, Colombia
- **Grupo L**: Inglaterra, Croacia, Ghana, Panamá

Por confederación: **AFC** (Australia, Irán, Japón, Jordania, Corea del Sur, Qatar, Arabia Saudita, Uzbekistán, Iraq); **CAF** (Argelia, Cabo Verde, Costa de Marfil, Egipto, Ghana, Marruecos, Senegal, Sudáfrica, Túnez, RD Congo); **CONCACAF** (EE.UU., Canadá, México, Curazao, Haití, Panamá); **CONMEBOL** (Argentina, Brasil, Colombia, Ecuador, Paraguay, Uruguay); **OFC** (Nueva Zelanda); **UEFA** (Inglaterra, Francia, Croacia, Noruega, Portugal, Alemania, Países Bajos, Austria, Bélgica, Escocia, España, Suiza, Suecia, Türkiye, Bosnia, Chequia).

Últimos 6 cupos (repechajes marzo 2026): UEFA → Bosnia (venció a Italia en penales 4-1), Suecia (3-2 a Polonia), Türkiye (1-0 a Kosovo), Chequia (a Dinamarca en penales). Interconfederación → RD Congo (1-0 a Jamaica) e Iraq (2-1 a Bolivia). El grupo I (Francia, Senegal, Iraq, Noruega) es el "grupo de la muerte".

### 3. Datos de evolución y clasificación de equipos

**Ranking FIFA (1 abril 2026, última actualización oficial antes del torneo; próxima 11 jun 2026)**: 1. Francia, 2. España, 3. Argentina, 4. Inglaterra, 5. Portugal. La diferencia España-Francia era de menos de 1 punto (en abril, España 2.ª por solo 0,92 puntos), el margen más estrecho en años. Nota: el ranking FIFA usa una fórmula tipo Elo desde 2018 pero NO considera diferencia de goles.

**Elo (eloratings.net, cifras exactas a 8 jun 2026 vía espejo footballratings.org; variación diaria entre paréntesis)**:
- #1 España **2.155** (−10)
- #2 Argentina **2.114** (+1)
- #3 Francia **2.062** (−19)
- #4 Inglaterra **2.021** (+1)
- #5 Brasil **1.991**
- #6 Portugal **1.986**
- #7 Colombia **1.982** (¡por delante de Países Bajos y Alemania!)
- #8 Países Bajos ~1.948
- #10 Alemania ~1.932

El sistema Elo se considera más predictivo que el ranking FIFA: Lasek, Szlávik & Bhulai (2013), *"The predictive power of ranking systems in association football"*, Int. J. Applied Pattern Recognition 1(1):27–46 (DOI 10.1504/IJAPR.2013.052339), concluyen que *"The best performing algorithm is a version of the famous Elo rating system... several other methods provide better predictive performance than the official ranking method"* — concretamente el Elo de eloratings.net fue el mejor. Esto se debe a que el Elo de eloratings incorpora diferencia de goles, importancia del partido y ventaja de local (~+100 puntos Elo; regla práctica: ~400 Elo ≈ 1 gol de superioridad).

**Cuotas de casas de apuestas (~10 junio 2026, FanDuel/DraftKings)**: España +450/+475, Francia +475/+500, Inglaterra +650/+700, Portugal +800/+850, Brasil +850/+900, Argentina +900/+1000, Alemania +1300, Países Bajos +1600, Bélgica +2200, Noruega +3300. Anfitriones: EE.UU. +6000, México +6000, Canadá +17500.

**Favoritos**: España (campeona de la Euro 2024, con Lamine Yamal y Pedri; principal duda es la forma física de Yamal tras una lesión de isquiotibiales), Francia (Mbappé; último Mundial de Deschamps), Argentina (campeona vigente, Messi), Inglaterra (Tuchel). **Dark horses** citadas: Noruega (Haaland + Ødegaard), Marruecos, Colombia (Luis Díaz, James), Croacia (Modrić), Uruguay, Senegal.

**Forma reciente útil para el modelo**: amistosos de preparación de junio 2026 (Argentina 2-0 Honduras, Brasil 2-1 Egipto, EE.UU. 1-2 Alemania, España 1-1 Egipto, Escocia 4-0 Bolivia). Para datos de eliminatorias (goles a favor/en contra por equipo) usar el histórico de resultados internacionales.

### 4. Fuentes de datos para el modelo (lo crítico)

**A. Datasets históricos descargables (gratuitos):**
- **Kaggle — "International football results from 1872 to 2026" (Mart Jürisoo)**: según la Data Card de Kaggle, *"This dataset includes 49,393 results of international football matches starting from the very first official match in 1872 up to 2025"*. CSV con columnas date/home_team/away_team/home_score/away_score/tournament/city/country/neutral. Es la base estándar para Dixon-Coles internacional. URL: `https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017`. Repo GitHub espejo (que cita "49,390 results... up to 2024"): `https://github.com/martj42/international_results`. La cifra exacta de filas depende de la fecha de descarga. La columna `neutral` es clave para modelar ventaja de local.
- **Kaggle — "2026 FIFA World Cup — Historical Elo Ratings" (afonsofernandescruz)**: Elo pre-torneo + historia completa de los 48 clasificados, `elo_ratings_wc2026.csv` (4.683 filas, 22 columnas), 1901–2026, con snapshot pre-torneo. URL: `https://www.kaggle.com/datasets/afonsofernandescruz/2026-fifa-world-cup-historical-elo-ratings`. CC BY-SA 4.0. Filtra `snapshot_date == max(snapshot_date)` por equipo para la lectura pre-torneo.
- **Kaggle — "International Football Elo Ratings (1872-2025)" (saifalnimri)**: `eloratings.csv`, 6.679 filas × 4 columnas, hasta 13/12/2025. URL: `https://www.kaggle.com/datasets/saifalnimri/international-football-elo-ratings`.
- **FiveThirtyEight SPI (archivo)**: `https://projects.fivethirtyeight.com/soccer-api/international/spi_matches_intl.csv` y `https://projects.fivethirtyeight.com/soccer-api/international/spi_global_rankings_intl.csv`. Descontinuado (datos hasta ~2023) pero útil como features históricas. Repo: `https://github.com/fivethirtyeight/data/tree/master/soccer-spi`.

**B. Elo en vivo (eloratings.net):** la web es una SPA que carga ficheros TSV estáticos. Se descargan con un simple GET sin autenticación:
- Ranking global actual: `https://www.eloratings.net/World.tsv` (sin cabecera; col 3 = código de país de 2 letras, col 4 = Elo actual).
- Ficheros anuales: `https://www.eloratings.net/<AÑO>.tsv` (p.ej. `https://www.eloratings.net/2026.tsv`).
- En Python: `pd.read_csv("https://www.eloratings.net/World.tsv", sep="\t", header=None)` → `df[2]` = código de equipo, `df[3]` = Elo.
- Para scraping de la página renderizada haría falta navegador headless (PhantomJS, ver repo `https://github.com/demetriodor/Footbal-Elo-Ratings`), pero los TSV evitan eso. Atribución: World Football Elo Ratings (eloratings.net), mantenido por Kirill Bukin y Erik Gebhardt.

**C. Rankings FIFA:** página oficial `https://inside.fifa.com/fifa-world-ranking/men`. Espejo con histórico/calculadora diaria: `https://football-ranking.com/fifa-world-rankings`.

**D. APIs de fútbol (cobertura Mundial 2026, límites y precios):**
- **football-data.org**: plan gratuito 10 req/min, 12 competiciones incluyendo el Mundial (código `WC`); marcadores con retraso, sin estadísticas de jugadores. Planes de pago desde €29/mes; add-ons (livescores €12, deep data €29, statistics €15, odds €15). Docs: `https://docs.football-data.org`. Mejor opción gratuita para prototipos.
- **API-Football (api-sports.io)**: plan gratuito 100 req/día (todos los endpoints y competiciones); planes Pro $19/mes (7.500 req/día), Ultra $29/mes (75.000), Mega $39/mes (150.000). Cubre el Mundial 2026. Docs: `https://www.api-football.com/documentation-v3`.
- **SportMonks**: orientado a producción, planes modulares (€100+/mes); endpoint dedicado de bracket para el Mundial 2026 (`/v3/football/seasons/26618/brackets`).
- **TheSportsDB**: gratuito, datos crowdsourced; bueno para prototipos sencillos.

**E. Paquetes Python para Dixon-Coles:**
- **`penaltyblog`** (`pip install penaltyblog`): la versión v1.9.0 fue subida a PyPI el 28 feb 2026; está mantenida por Martin Eastwood y PyPI la describe como *"a production-ready Python package designed for football (soccer) analytics"*. Implementa `models.DixonColesGoalModel`, `models.dixon_coles_weights(dates, xi)` para decaimiento temporal, Poisson, Poisson bivariante, modelos bayesianos jerárquicos (vía Stan), ratings Elo/Massey/Colley/Pi, y scrapers (football-data.co.uk, FBref, Understat, Club Elo). Docs: `https://penaltyblog.readthedocs.io` y `https://docs.pena.lt/y`. Es la herramienta recomendada. Ejemplo:
  ```python
  import penaltyblog as pb
  clf = pb.models.DixonColesGoalModel(df["goals_home"], df["goals_away"], df["team_home"], df["team_away"])
  clf.fit()
  grid = clf.predict("Spain", "France")
  ```
- Implementaciones de referencia de código abierto: blog de Martin Eastwood (`https://pena.lt/y`), blog de dashee87 (`https://dashee87.github.io`, Dixon-Coles + time-weighting), `https://urazakgul.github.io/datafc-blog` (implementación paso a paso con `dixon_coles_simulate_match`), y repos específicos del Mundial 2026: `https://github.com/Hicruben/world-cup-2026-prediction-model` (Elo + Dixon-Coles + Monte Carlo, backtest walk-forward sobre 920 partidos) y `https://github.com/huffyhenry/dixon-coles-worldcup` (modelo Stan con función `predict(..., neutral=True, aet=True)`).

### 5. Contexto de modelización (mejores prácticas)

- **Decaimiento temporal**: ponderar cada partido con `w = exp(-xi * días_desde_partido)`. Ojo con una imprecisión común: Dixon & Coles (1997) hallaron xi=0.0065 pero **en medias-semanas, no en días**; eso equivale a ~0.00186/día (al dividir por los 3,5 días de media semana). El valor por defecto de `penaltyblog` en `dixon_coles_weights` es **xi=0.0018**; en su tutorial Eastwood obtiene un óptimo "de aproximadamente 0.001" por RPS, mientras que otros análisis (EPL 2010/11–2020/21) llegan hasta ~0.012. **Conclusión**: empieza en xi≈0.0018 y optimiza minimizando el Rank Probability Score (RPS) en validación; un xi=0.0065/día implica una vida media de solo ~107 días (muy agresivo para internacionales, donde los partidos son más espaciados).
- **Ventaja de local / sedes neutrales**: ~90% de los partidos del Mundial son en sede neutral, así que el parámetro de localía solo debe aplicarse a los tres anfitriones (EE.UU., México, Canadá) cuando jueguen en casa. Una referencia (Economics Observatory, modelo Dixon-Coles para el WC2026) usa: la localía reduce ~0,2 goles encajados y suma ~0,1 goles marcados. La columna `neutral` del dataset de Jürisoo permite estimar el parámetro γ correctamente, entrenando con todos los partidos pero activando γ solo cuando `neutral == 0`.
- **Datos escasos entre confederaciones**: el modelo tiene poca información para comparar fuerza entre confederaciones (pocos partidos cruzados), lo que afecta especialmente a la fase de grupos; conviene incorporar Elo como prior o feature para regularizar las fuerzas de ataque/defensa (es lo que hacen los modelos abiertos del WC2026: Elo → goles esperados → Dixon-Coles).
- **Simulación del formato 48 equipos**: (1) ajustar fuerzas de ataque/defensa por equipo; (2) simular los 72 partidos de grupos vía Poisson bivariante con corrección rho de Dixon-Coles; (3) aplicar desempates FIFA en orden (puntos → diferencia de goles → goles marcados → conducta/fair play → ranking FIFA); (4) clasificar los 12 terceros y tomar los 8 mejores (mismos criterios: puntos → dif. de goles → goles → fair play → ranking FIFA); (5) mapear los 8 terceros al escenario correcto del Round of 32 (495 combinaciones predefinidas por FIFA); (6) simular eliminatorias con prórroga/penales (en empate, modelar penales como ~50/50 o ponderado por Elo); (7) repetir 10.000+ veces (Monte Carlo) para obtener probabilidades de avance y de título.
- **Validación**: backtesting walk-forward out-of-sample (predecir solo con datos previos al partido) y medir con RPS o log-loss frente a un baseline solo-Elo.

## Recommendations

1. **Empieza por los datos** (semana 1): descarga el CSV de Jürisoo (histórico de resultados, 49.393 partidos) y `World.tsv` de eloratings.net. Filtra a partidos desde ~2010–2014 para tener relevancia sin perder volumen, y conserva la columna `neutral`.
2. **Instala `penaltyblog`** (v1.9.0) y reproduce primero un Dixon-Coles simple con decaimiento temporal sobre datos de ligas, luego adáptalo a internacionales. Usa `dixon_coles_weights` (parte de xi=0.0018) y optimiza xi por RPS.
3. **Incorpora Elo como prior/feature** para mitigar la escasez de partidos entre confederaciones; valida que las fuerzas estimadas correlacionen con Elo y con las cuotas del mercado.
4. **Modela la localía solo para anfitriones** (EE.UU., México, Canadá) y trata el resto como neutral. Calibra γ con la columna `neutral` (referencia: +0,1 goles marcados / −0,2 encajados).
5. **Construye el simulador Monte Carlo** del formato de 48 (grupos → R32 con la lógica de 8 mejores terceros y las 495 combinaciones → final), 10.000+ iteraciones. Reutiliza la lógica de `Hicruben/world-cup-2026-prediction-model` como referencia.
6. **Para datos en vivo durante el torneo**: usa el plan gratuito de football-data.org (Mundial incluido) o API-Football ($19/mes si necesitas más volumen). Refresca Elo desde `World.tsv` a diario.
7. **Umbrales que cambiarían el enfoque**: si el RPS no mejora respecto a un baseline solo-Elo, simplifica (modelo Elo→Poisson directo). Si necesitas estadísticas de jugadores/xG, sube a API-Football de pago o SportMonks.

## Caveats
- Las cuotas y los números de Elo/ranking cambian a diario; los valores citados son de ~1–10 junio 2026. El ranking FIFA del 11 junio 2026 (día inaugural) será la última actualización oficial pre-torneo. Hay una discrepancia esperada entre fuentes Elo (p.ej. Alemania 1.925 en un snapshot de Kaggle de inicios de junio vs ~1.932 en el TSV vivo): es deriva por fecha de snapshot, no un error.
- Los emparejamientos exactos del Round of 32 no se conocen hasta el 27 junio; el modelo debe manejar las 495 combinaciones de terceros.
- El SPI de FiveThirtyEight está descontinuado (datos hasta ~2023); úsalo solo como features históricas, no como rating actual.
- Algunas fuentes de horarios/sedes provienen de medios (ESPN, NBC, FOX) y pueden tener pequeñas discrepancias de hora local o de qué equipo figura como "local"; verifica contra la web oficial de FIFA (`https://www.fifa.com/.../canadamexicousa2026/scores-fixtures`).
- eloratings.net y los datasets de Kaggle tienen licencias de reuso específicas (CC BY-SA 4.0 en varios casos); cita la fuente si publicas resultados.
- El número exacto de filas del dataset de Jürisoo depende de la fecha de descarga (49.393 "hasta 2025" en Kaggle; el espejo de GitHub cita 49.390 "hasta 2024"). Descárgalo el mismo día que entrenes para tener los amistosos de preparación más recientes.