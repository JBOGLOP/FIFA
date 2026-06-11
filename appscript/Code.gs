/**
 * BD_fifa — API de Apps Script para el predictor Mundial 2026.
 *
 * Expone la hoja como API bidireccional:
 *   - doGet  (GET):  devuelve en JSON las filas de una pestaña (?sheet=Resultados).
 *   - doPost (POST): escribe filas en una pestaña (requiere token compartido).
 *
 * DESPLIEGUE (una vez):
 *   1. Pega este archivo en el editor de Apps Script de la hoja BD_fifa.
 *   2. Cambia TOKEN por un secreto propio (el mismo que pondrás en Python).
 *   3. Ejecuta la función setup() una vez (crea las pestañas con cabeceras).
 *   4. Implementar > Nueva implementación > Tipo: Aplicación web.
 *        - Ejecutar como: Yo (tu cuenta).
 *        - Quién tiene acceso: Cualquier persona.
 *   5. Copia la URL /exec y ponla en config/settings.yaml (gsheet.endpoint).
 *   Si actualizas el código: Implementar > Gestionar implementaciones > Editar
 *   > Nueva versión (así la URL /exec no cambia).
 */

const TOKEN = 'CAMBIA_ESTE_TOKEN';  // <-- secreto compartido con Python

const RESULTS_HEADERS = ['date', 'home_team', 'away_team', 'home_score', 'away_score', 'neutral'];

function doGet(e) {
  const sheetName = (e && e.parameter && e.parameter.sheet) || 'Resultados';
  return json_(readSheet_(sheetName));
}

function doPost(e) {
  let body;
  try {
    body = JSON.parse((e && e.postData && e.postData.contents) || '{}');
  } catch (err) {
    return json_({ error: 'json invalido' });
  }
  if (body.token !== TOKEN) {
    return json_({ error: 'no autorizado' });
  }
  const sheetName = body.sheet || 'Predicciones';
  const rows = body.rows || [];
  writeSheet_(sheetName, rows);
  return json_({ ok: true, sheet: sheetName, written: rows.length });
}

/** Crea las pestañas base. Ejecutar manualmente una vez. */
function setup() {
  const ss = SpreadsheetApp.getActive();
  const res = ss.getSheetByName('Resultados') || ss.insertSheet('Resultados');
  if (res.getLastRow() === 0) res.appendRow(RESULTS_HEADERS);
  if (!ss.getSheetByName('Predicciones')) ss.insertSheet('Predicciones');
}

function readSheet_(name) {
  const sh = SpreadsheetApp.getActive().getSheetByName(name);
  if (!sh) return { sheet: name, headers: [], rows: [] };
  const values = sh.getDataRange().getValues();
  if (values.length === 0) return { sheet: name, headers: [], rows: [] };
  const headers = values.shift().map(String);
  const rows = values
    .filter(r => r.some(c => c !== '' && c !== null))
    .map(r => {
      const o = {};
      headers.forEach((h, i) => { o[h] = r[i]; });
      return o;
    });
  return { sheet: name, headers: headers, rows: rows };
}

function writeSheet_(name, rows) {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(name);
  if (!sh) sh = ss.insertSheet(name);
  sh.clearContents();
  if (!rows.length) return;
  const headers = Object.keys(rows[0]);
  const out = [headers].concat(rows.map(r => headers.map(h => r[h])));
  sh.getRange(1, 1, out.length, headers.length).setValues(out);
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
