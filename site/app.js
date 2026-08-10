/* Citizen-first render of the chain. The UI reads chain.json — plain language
   leads, numbers second, provenance behind a disclosure. Nothing is hidden;
   it is re-layered. */

const FUEL_COLORS = {
  coal: "var(--series-2)", coal_lignite: "var(--series-2)", lignite: "#a8552e",
  gas: "#d98e2b", diesel: "#8a6a3c", nuclear: "var(--series-4)",
  hydro_large: "var(--series-1)", res: "var(--series-3)", res_incl_small_hydro: "var(--series-3)",
};
const FUEL_LABELS = {
  coal: "Coal", coal_lignite: "Coal & lignite", lignite: "Lignite", gas: "Gas",
  diesel: "Diesel", nuclear: "Nuclear", hydro_large: "Hydro", res: "Renewables",
  res_incl_small_hydro: "Renewables",
};

/* UI copy: plain title + one-sentence story per stage. */
const COPY = {
  S0: { title: "What's promised", story: "Announced projects queue up for land, loans and clearances. Many never make it — and this page will track how many." },
  S1: { title: "What's built", story: "Every power station connected to the grid — coal to rooftop-scale solar — at the end of March 2024." },
  S2: { title: "What's ready to run", story: "Built isn't always available: maintenance, breakdowns and fuel shortages keep part of the fleet offline every day." },
  S3: { title: "What's called on", story: "Ready plants run only when someone buys their power — and buyers who can't pay ask for less than people need." },
  S4: { title: "What was generated", story: "All the electricity India's utility power stations actually produced over the year — measured in 'units', the same units your electricity meter counts (1 unit = 1 kWh; a BU is a billion of them)." },
  S5: { title: "…after plants power themselves", story: "Stations run on their own electricity too — a coal plant uses roughly 6–9% of what it makes before any leaves the gate." },
  S6: { title: "What reached the local grid", story: "Crossing the country costs a few percent more, lost as heat in the wires." },
  S7: { title: "What was billed & paid for", story: "Of the power handed to distribution companies, one unit in six is lost in local wires, never billed, or billed but never paid." },
  S8: { title: "What people actually received", story: "Hours of supply, blackouts, voltage — the lived experience. It's the part India measures least." },
};

const fmtIN = (n, d = 0) => n.toLocaleString("en-IN", { maximumFractionDigits: d });

function headline(s) {
  if (s.id === "S1") return `${fmtIN(s.value / 1000)}<small>GW</small>`;
  if (s.id === "S4") return `${fmtIN(s.value / 1000)}<small>BU</small>`;
  if (s.id === "S7") return `${s.metrics.atc_loss_pct.toFixed(1)}%<small>lost</small>`;
  if (s.id === "S8" && s.metrics) return `${fmtIN(s.metrics.per_capita_kwh)}<small>units/person</small>`;
  return "";
}

function detailsBlock(s) {
  const rows = [];
  rows.push(["Stage", `${s.id} — ${s.name}`]);
  if (s.value !== undefined) rows.push(["As published", `${fmtIN(s.value)} ${s.unit}`]);
  if (s.metrics && s.metrics.atc_loss_pct) rows.push(["Identity", `billing ${s.metrics.billing_efficiency_pct}% × collection ${s.metrics.collection_efficiency_pct}% → AT&C ${s.metrics.atc_loss_pct}%`]);
  if (s.metrics && s.metrics.per_capita_kwh) rows.push(["Measured", `per-capita consumption ${fmtIN(s.metrics.per_capita_kwh)} kWh/yr (utilities + non-utilities basis); supply hours & reliability still unmeasured`]);
  if (s.grade) rows.push(["Coverage grade", s.grade + " (published primary series)"]);
  if (s.as_of) rows.push(["As of", s.as_of]);
  if (s.period) rows.push(["Period", s.period]);
  if (s.source) rows.push(["Source", s.source + (s.hand_verified ? " · hand-verified, parser pending" : "")]);
  if (s.source_file) rows.push(["Archived file", `<code>${s.source_file}</code>`]);
  if (s.note) rows.push(["Status", s.note]);
  return `<details><summary>the fine print</summary>
    <dl class="detail-grid">${rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")}</dl>
  </details>`;
}

function stageCard(s) {
  const c = COPY[s.id] || { title: s.name, story: "" };
  const el = document.createElement("article");
  const populated = s.status === "populated" || s.status === "partial";
  el.className = "stage-card" + (populated ? "" : " pending");
  const right = populated
    ? `<span class="stage-num">${headline(s)}</span>${s.status === "partial" ? `<span class="pending-chip">partly measured</span>` : ""}`
    : `<span class="pending-chip">not yet measured here</span>`;
  el.innerHTML = `
    <div class="stage-top">
      <span class="stage-title">${c.title}</span>
      ${right}
    </div>
    <p class="stage-story">${c.story}</p>`;
  if (s.breakdown) {
    const total = Object.values(s.breakdown).reduce((a, b) => a + b, 0);
    const entries = Object.entries(s.breakdown).filter(([, v]) => v / total > 0.004);
    const bar = `<div class="breakdown">${entries.map(([k, v]) =>
      `<span style="width:${(100 * v / total).toFixed(2)}%;background:${FUEL_COLORS[k] || "#999"}" title="${FUEL_LABELS[k]}: ${fmtIN(v)} ${s.unit}"></span>`).join("")}</div>
      <div class="legend">${entries.map(([k, v]) =>
      `<b><i style="background:${FUEL_COLORS[k] || "#999"}"></i>${FUEL_LABELS[k]} ${Math.round(100 * v / total)}%</b>`).join("")}</div>`;
    el.insertAdjacentHTML("beforeend", bar);
  }
  el.insertAdjacentHTML("beforeend", detailsBlock(s));
  return el;
}

function connector(text) {
  const el = document.createElement("div");
  el.className = "connector";
  if (text) el.innerHTML = `<span class="why">${text}</span>`;
  return el;
}

function tiles(chain, captive) {
  const s1 = chain.stages.find((s) => s.id === "S1");
  const s4 = chain.stages.find((s) => s.id === "S4");
  const s7 = chain.stages.find((s) => s.id === "S7");
  const selfShare = captive.gap_value / (captive.gap_value + s4.value);
  const t = [
    [`${fmtIN(s1.value / 1000)}<small>GW</small>`, "of power stations built — how much India <em>can</em> make at once"],
    [`${fmtIN(s4.value / 1000)}<small>BU</small>`, "billion units made this year — a 'unit' is the kWh your meter counts"],
    [`${s7.metrics.atc_loss_pct.toFixed(1)}<small>%</small>`, "of delivered power is lost, unbilled, or unpaid"],
    [`1 in ${Math.round(1 / selfShare)}<small>units</small>`, "is made off the public grid — factories & rooftops"],
  ];
  document.getElementById("tiles").innerHTML = t.map(([big, cap]) =>
    `<div class="tile"><div class="big">${big}</div><div class="cap">${cap}</div></div>`).join("");
}

function lesson(chain) {
  const s1 = chain.stages.find((s) => s.id === "S1");
  const s4 = chain.stages.find((s) => s.id === "S4");
  const bridge = chain.edges.find((e) => e.kind === "bridge");
  const shares = (breakdown, groups) => {
    const total = Object.values(breakdown).reduce((a, b) => a + b, 0);
    return groups.map(([label, keys, color]) => {
      const v = keys.reduce((a, k) => a + (breakdown[k] || 0), 0);
      return { label, pct: (100 * v) / total, color };
    });
  };
  const capGroups = [
    ["Thermal", ["coal", "lignite", "gas", "diesel"], "var(--series-2)"],
    ["Hydro", ["hydro_large"], "var(--series-1)"],
    ["Renewables", ["res_incl_small_hydro"], "var(--series-3)"],
    ["Nuclear", ["nuclear"], "var(--series-4)"],
  ];
  const genGroups = [
    ["Thermal", ["coal_lignite", "gas", "diesel"], "var(--series-2)"],
    ["Hydro", ["hydro_large"], "var(--series-1)"],
    ["Renewables", ["res"], "var(--series-3)"],
    ["Nuclear", ["nuclear"], "var(--series-4)"],
  ];
  const bar = (list) => `<div class="sharebar">${list.map((x) =>
    `<span style="width:${x.pct.toFixed(1)}%;background:${x.color}" title="${x.label} ${x.pct.toFixed(0)}%">${x.pct >= 9 ? Math.round(x.pct) + "%" : ""}</span>`).join("")}</div>`;
  const cap = shares(s1.breakdown, capGroups);
  const gen = shares(s4.breakdown, genGroups);
  document.getElementById("lesson").innerHTML = `
    <div class="lesson-panel">
      <h3>A megawatt is a <em>promise</em>. A unit of electricity is <em>delivery</em>.</h3>
      <p>The same machines look completely different depending on which one you count.
      A solar farm and a coal plant of the same size produce very different amounts over a
      year — so India's <strong>capacity mix</strong> and its <strong>generation mix</strong> tell two
      different stories. If this page teaches one thing, it's this:</p>
      <div class="sharebars">
        <div><div class="sharebar-label">Share of machines built (capacity)</div>${bar(cap)}</div>
        <div><div class="sharebar-label">Share of electricity made (generation)</div>${bar(gen)}</div>
      </div>
      <div class="legend" style="margin-top:.7rem">${cap.map((x) =>
        `<b><i style="background:${x.color}"></i>${x.label}</b>`).join("")}</div>
      <p style="font-size:.85rem;margin-top:1rem">Across the whole fleet, India's stations ran at the
      equivalent of <strong>${(bridge.factor * 100).toFixed(0)}%</strong> of full blast this year —
      measured against everything built. (Against plants actually asked to run, the figure differs;
      that data is still being wired up.)</p>
    </div>`;
}

/* theme toggle: light is the default; choice persists */
const themeBtn = document.getElementById("themeBtn");
function syncThemeBtn() {
  const dark = document.documentElement.dataset.theme === "dark";
  themeBtn.textContent = dark ? "☀" : "☾";
}
themeBtn.addEventListener("click", () => {
  const dark = document.documentElement.dataset.theme === "dark";
  if (dark) { delete document.documentElement.dataset.theme; localStorage.theme = "light"; }
  else { document.documentElement.dataset.theme = "dark"; localStorage.theme = "dark"; }
  syncThemeBtn();
});
syncThemeBtn();

async function main() {
  const chain = await (await fetch("data/chain.json")).json();
  const root = document.getElementById("chain");
  const captive = chain.edges.find((e) => e.kind === "side_flow");

  tiles(chain, captive);

  const WHY = {
    S0: "…but plans die at clearances, land and financing…",
    S1: "…and what's built isn't available every hour…",
    S2: "…and what's available runs only if someone buys…",
    S3: "…megawatts become units of energy here…",
    S4: "…minus what stations use themselves…",
    S5: "…minus losses crossing the country…",
    S6: "…minus what's never billed or never paid…",
    S7: "…and money trouble upstream becomes blackouts downstream…",
  };

  chain.stages.forEach((s, i) => {
    root.appendChild(stageCard(s));
    if (i < chain.stages.length - 1) root.appendChild(connector(WHY[s.id]));
  });

  if (captive) {
    const el = document.createElement("aside");
    el.className = "bypass";
    el.innerHTML = `
      <div class="stage-top">
        <span class="stage-title">Meanwhile, off the public grid…</span>
        <span class="stage-num">${fmtIN(captive.gap_value / 1000)}<small>BU</small></span>
      </div>
      <p>Factories and rooftops making their own power add ${fmtIN(captive.gap_value / 1000)} billion
      units on top of the grid's ${fmtIN(chain.stages.find((s) => s.id === "S4").value / 1000)} — skipping the
      wires and the bills entirely. It's why national totals and your electricity bill never quite reconcile.</p>
      <details><summary>the fine print</summary>
        <dl class="detail-grid">
          <dt>What</dt><dd>${captive.label}</dd>
          <dt>Status</dt><dd>provisional (CEA's own marking)</dd>
          <dt>Archived file</dt><dd><code>${captive.source_file}</code></dd>
        </dl>
      </details>`;
    root.appendChild(el);
  }

  lesson(chain);

  const prov = document.getElementById("provenance");
  const items = [];
  for (const s of chain.stages) {
    if (s.source_file) items.push(`<li>${COPY[s.id].title} (${s.id}): parsed from <code>${s.source_file}</code></li>`);
    if (s.hand_verified) items.push(`<li>${COPY[s.id].title} (${s.id}): PFC Report on Performance of Power Utilities 2023-24, hand-verified 2026-08-09 — parser pending</li>`);
  }
  for (const e of chain.edges) {
    if (e.source_file) items.push(`<li>${e.label || e.kind}: parsed from <code>${e.source_file}</code></li>`);
  }
  prov.innerHTML = items.join("");
}

main();
