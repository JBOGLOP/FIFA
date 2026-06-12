/* Predictor Mundial FIFA 2026 — dashboard estático */

const PCT = (p) => (p * 100).toFixed(1) + "%";
const flagUrl = (code) => `https://flagcdn.com/32x24/${code}.png`;

function flagImg(code, name) {
  if (!code) return "";
  return `<img class="flag" src="${flagUrl(code)}" alt="${name}" loading="lazy">`;
}

let DATA = null;
let MATCHES = null;

async function init() {
  const res = await fetch("data/predictions.json");
  DATA = await res.json();

  document.getElementById("model-info").textContent = DATA.meta.model;
  document.getElementById("iters").textContent = DATA.meta.n_iterations.toLocaleString("es");

  setupTabs();
  renderRanking();
  renderHeatmap();
  renderGroups();
  renderBracket();

  // Predicciones de partidos (archivo aparte; opcional)
  try {
    const r = await fetch("data/matches.json");
    if (r.ok) { MATCHES = await r.json(); renderMatches(); }
  } catch (e) { /* sin datos de partidos */ }
}

/* ---------- Pestañas ---------- */
function setupTabs() {
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("view-" + btn.dataset.view).classList.add("active");
    });
  });
}

/* ---------- Favoritos ---------- */
function renderRanking() {
  const top = DATA.teams.slice(0, 16);
  new Chart(document.getElementById("champ-chart"), {
    type: "bar",
    data: {
      labels: top.map((t) => t.es),
      datasets: [{
        label: "Prob. de título",
        data: top.map((t) => +(t.champion * 100).toFixed(1)),
        backgroundColor: "#00b894",
        borderRadius: 5,
      }],
    },
    options: {
      indexAxis: "y",
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c) => c.parsed.x + "%" } },
      },
      scales: {
        x: { ticks: { color: "#9aa6b2", callback: (v) => v + "%" }, grid: { color: "#2a313c" } },
        y: { ticks: { color: "#e8edf3" }, grid: { display: false } },
      },
    },
  });

  const rows = DATA.teams.map((t, i) => `
    <tr>
      <td><span class="rank-num">${i + 1}</span></td>
      <td><div class="team-cell">${flagImg(t.flag, t.es)}${t.es}</div></td>
      <td class="mini">${t.group} · ${t.conf}</td>
      <td class="pct">${PCT(t.champion)}</td>
      <td class="pct">${PCT(t.reach_final)}</td>
      <td class="pct">${PCT(t.qualified)}</td>
    </tr>`).join("");
  document.getElementById("ranking-table").innerHTML = `
    <table><thead><tr>
      <th>#</th><th>Selección</th><th>Grupo</th><th>Campeón</th><th>Final</th><th>Clasifica</th>
    </tr></thead><tbody>${rows}</tbody></table>`;
}

/* ---------- Heatmap ---------- */
function heatCell(p) {
  const txt = p > 0.45 ? "#05231a" : "#e8edf3";
  return `<td class="heat" style="background:rgba(0,184,148,${p.toFixed(3)});color:${txt}">${PCT(p)}</td>`;
}
function renderHeatmap() {
  const cols = [
    ["Clasifica", "qualified"], ["Octavos", "reach_R16"], ["Cuartos", "reach_QF"],
    ["Semis", "reach_SF"], ["Final", "reach_final"], ["Campeón", "champion"],
  ];
  const head = `<th>Selección</th>` + cols.map((c) => `<th>${c[0]}</th>`).join("");
  const body = DATA.teams.map((t) => `
    <tr>
      <td><div class="team-cell">${flagImg(t.flag, t.es)}${t.es}</div></td>
      ${cols.map((c) => heatCell(t[c[1]])).join("")}
    </tr>`).join("");
  document.getElementById("heatmap").innerHTML =
    `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

/* ---------- Grupos ---------- */
function renderGroups() {
  const grid = document.getElementById("groups-grid");
  grid.innerHTML = Object.keys(DATA.groups).sort().map((g) => {
    const rows = DATA.groups[g].map((t) => `
      <div class="group-row">
        <div>
          <div class="team-cell">${flagImg(t.flag, t.es)}${t.es}</div>
          <div class="bar"><span style="width:${(t.group_win * 100).toFixed(0)}%"></span></div>
        </div>
        <div style="text-align:right">
          <div class="pct">${PCT(t.group_win)}</div>
          <div class="mini">clasifica ${PCT(t.qualified)}</div>
        </div>
      </div>`).join("");
    return `<div class="group-card"><h3>Grupo ${g}</h3>${rows}</div>`;
  }).join("");
}

/* ---------- Partidos ---------- */
function matchCard(m) {
  const probs = `
    <div class="mc-probs" title="1 / X / 2">
      <div class="mc-1" style="flex:${m.p1}">${Math.round(m.p1)}</div>
      <div class="mc-x" style="flex:${m.px}">${Math.round(m.px)}</div>
      <div class="mc-2" style="flex:${m.p2}">${Math.round(m.p2)}</div>
    </div>`;
  return `
    <div class="match-card ${m.today ? "is-today" : ""}">
      <div class="mc-teams">
        <span>${m.home_es}</span>
        <span class="mc-score">${m.score}</span>
        <span>${m.away_es}</span>
      </div>
      <div class="mc-meta">
        xG ${m.xg_home}–${m.xg_away} · ${m.venue} · J${m.matchday} · favorito: <b>${m.fav}</b>
        ${m.today ? '<span class="mc-tag">HOY</span>' : ""}
      </div>
      ${probs}
      <div class="mc-meta">${m.top.map((t) => `${t.s} (${t.p}%)`).join(" · ")}</div>
    </div>`;
}

function renderMatches() {
  const today = MATCHES.matches.filter((m) => m.today);
  document.getElementById("today-block").innerHTML = today.length
    ? `<div class="today-banner"><h3>⚽ Hoy — ${today[0].date}</h3>
        <div class="matches-grid">${today.map(matchCard).join("")}</div></div>`
    : "";

  // Rellena los desplegables una vez
  const groups = [...new Set(MATCHES.matches.map((m) => m.group))].sort();
  document.getElementById("f-group").insertAdjacentHTML("beforeend",
    groups.map((g) => `<option value="${g}">Grupo ${g}</option>`).join(""));
  const teams = [...new Set(MATCHES.matches.flatMap((m) => [m.home_es, m.away_es]))]
    .sort((a, b) => a.localeCompare(b, "es"));
  document.getElementById("f-team").insertAdjacentHTML("beforeend",
    teams.map((t) => `<option value="${t}">${t}</option>`).join(""));

  ["f-matchday", "f-group", "f-team"].forEach((id) =>
    document.getElementById(id).addEventListener("change", applyMatchFilters));
  document.getElementById("f-reset").addEventListener("click", () => {
    ["f-matchday", "f-group", "f-team"].forEach((id) => (document.getElementById(id).value = ""));
    applyMatchFilters();
  });

  applyMatchFilters();
}

function applyMatchFilters() {
  const md = document.getElementById("f-matchday").value;
  const grp = document.getElementById("f-group").value;
  const team = document.getElementById("f-team").value;

  const list = MATCHES.matches.filter((m) => {
    if (grp && m.group !== grp) return false;
    if (team && m.home_es !== team && m.away_es !== team) return false;
    if (md === "hoy" && !m.today) return false;
    if (md && md !== "hoy" && String(m.matchday) !== md) return false;
    return true;
  });

  document.getElementById("f-count").textContent =
    `${list.length} partido${list.length === 1 ? "" : "s"}`;

  const byGroup = {};
  list.forEach((m) => (byGroup[m.group] ||= []).push(m));
  const html = Object.keys(byGroup).sort().map((g) =>
    `<div class="group-block"><h3>Grupo ${g}</h3>
      <div class="matches-grid">${byGroup[g].map(matchCard).join("")}</div></div>`).join("");
  document.getElementById("matches-block").innerHTML =
    list.length ? html : '<p class="hint">No hay partidos con esos filtros.</p>';
}

/* ---------- Bracket ---------- */
function resolveSlot(token) {
  if (typeof token === "number") return { label: "Ganador " + token, flag: "" };
  if (token.startsWith("T:")) return { label: "3º (" + token.slice(2).split("").join("/") + ")", flag: "" };
  if (token.startsWith("R")) return { label: "2º Grupo " + token.slice(1), flag: "" };
  if (token.startsWith("W")) {
    const fav = DATA.group_favorite[token.slice(1)];
    return fav ? { label: fav.es, flag: fav.flag, fav: fav.group_win } : { label: token, flag: "" };
  }
  return { label: String(token), flag: "" };
}
function matchBox(m) {
  const h = resolveSlot(m.home), a = resolveSlot(m.away);
  const slot = (s) => `<div class="slot">${flagImg(s.flag, s.label)}<span>${s.label}</span>${
    s.fav ? `<span class="mini">${PCT(s.fav)}</span>` : ""}</div>`;
  return `<div class="match"><div class="mnum">Partido ${m.id}</div>${slot(h)}${slot(a)}</div>`;
}
function renderBracket() {
  const ko = DATA.bracket.knockout_rounds;
  const inRange = (lo, hi) => ko.filter((m) => m.id >= lo && m.id <= hi);
  const columns = [
    ["Dieciseisavos", DATA.bracket.round_of_32],
    ["Octavos", inRange(89, 96)],
    ["Cuartos", inRange(97, 100)],
    ["Semifinales", inRange(101, 102)],
    ["Final", inRange(104, 104)],
  ];
  document.getElementById("bracket").innerHTML =
    `<div class="bracket">${columns.map(([title, matches]) =>
      `<div class="round"><div class="round-title">${title}</div>${
        matches.map(matchBox).join("")}</div>`).join("")}</div>`;
}

init();
