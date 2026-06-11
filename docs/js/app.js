/* Predictor Mundial FIFA 2026 — dashboard estático */

const PCT = (p) => (p * 100).toFixed(1) + "%";
const flagUrl = (code) => `https://flagcdn.com/32x24/${code}.png`;

function flagImg(code, name) {
  if (!code) return "";
  return `<img class="flag" src="${flagUrl(code)}" alt="${name}" loading="lazy">`;
}

let DATA = null;

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
