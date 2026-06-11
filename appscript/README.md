# Apps Script — API de la hoja BD_fifa

Conecta el pipeline de Python con la Google Sheet `BD_fifa` de forma bidireccional,
sin credenciales de Google en Python (todo pasa por el web app de Apps Script).

## Despliegue (una vez)

1. Abre la hoja **BD_fifa** → menú **Extensiones → Apps Script**.
2. Pega el contenido de [`Code.gs`](Code.gs) en el editor (reemplaza lo que haya).
3. Cambia la constante `TOKEN` por un secreto propio (una cadena larga al azar).
   Usa **ese mismo valor** en Python (variable de entorno `FIFA_SHEET_TOKEN`).
4. Ejecuta la función **`setup`** una vez (botón ▶). Autoriza los permisos.
   Crea las pestañas `Resultados` (con cabeceras) y `Predicciones`.
5. **Implementar → Nueva implementación → Aplicación web**:
   - *Ejecutar como*: **Yo**
   - *Quién tiene acceso*: **Cualquier persona**
6. Copia la URL que termina en `/exec` y ponla en `config/settings.yaml` →
   `gsheet.endpoint`.

> Si más adelante editas `Code.gs`: **Implementar → Gestionar implementaciones →
> Editar (lápiz) → Versión: Nueva** para que la URL `/exec` no cambie.

## Endpoints

| Método | Uso | Ejemplo |
|---|---|---|
| `GET ?sheet=Resultados` | Lee una pestaña → JSON `{headers, rows}` | leer resultados reales |
| `POST {token, sheet, rows}` | Escribe filas en una pestaña | publicar predicciones |

## Pestañas

- **Resultados** (entrada): tú metes los resultados reales del Mundial.
  Columnas: `date, home_team, away_team, home_score, away_score, neutral`.
  Usa los nombres de equipo del dataset (inglés, p. ej. `Spain`, `Czech Republic`).
- **Predicciones** (salida): la rellena Python con la última simulación.

## Seguridad

El web app es público (necesario para llamarlo sin OAuth). El `doPost` exige el
`TOKEN`, así que nadie puede escribir sin él. El `doGet` es de solo lectura.
No subas el token al repo: en Python va por variable de entorno.
