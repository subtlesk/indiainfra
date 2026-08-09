/* Renders site/data/chain.json. The UI reads the chain; it does not hard-code it. */

const FUEL_COLORS = {
  coal: "#4b5563", coal_lignite: "#4b5563", lignite: "#6b7280", gas: "#b45309",
  diesel: "#92400e", nuclear: "#7c3aed", hydro_large: "#2563eb",
  res: "#16a34a", res_incl_small_hydro: "#16a34a",
};

const fmt = (n) => n.toLocaleString("en-IN", { maximumFractionDigits: 0 });

function stageBox(s) {
  const el = document.createElement("div");
  el.className = "stage" + (s.status === "populated" ? "" : " pending");
  let value = "";
  if (s.value !== undefined) {
    value = `<span class="stage-value">${fmt(s.value)} <small>${s.unit}</small></span>`;
  } else if (s.metrics) {
    value = `<span class="stage-value">${s.metrics.atc_loss_pct}% <small>AT&amp;C loss</small></span>`;
  } else {
    value = `<span class="stage-value"><small>not yet populated</small></span>`;
  }
  const grade = s.grade ? `<span class="grade" title="coverage grade">${s.grade}</span>` : "";
  el.innerHTML = `
    <div class="stage-head">
      <span><span class="stage-id">${s.id}</span> <span class="stage-name">${s.name}</span>${grade}</span>
      ${value}
    </div>`;
  if (s.breakdown) {
    const total = Object.values(s.breakdown).reduce((a, b) => a + b, 0);
    const bar = document.createElement("div");
    bar.className = "breakdown";
    const legend = document.createElement("div");
    legend.className = "legend";
    for (const [k, v] of Object.entries(s.breakdown)) {
      const seg = document.createElement("span");
      seg.style.width = (100 * v / total) + "%";
      seg.style.background = FUEL_COLORS[k] || "#999";
      seg.title = `${k}: ${fmt(v)} ${s.unit}`;
      bar.appendChild(seg);
      legend.innerHTML += `<b><i style="background:${FUEL_COLORS[k] || "#999"}"></i>${k.replace(/_/g, " ")} ${fmt(v)}</b>`;
    }
    el.appendChild(bar);
    el.appendChild(legend);
  }
  if (s.metrics) {
    el.innerHTML += `<p class="stage-note">billing efficiency ${s.metrics.billing_efficiency_pct}% × collection efficiency ${s.metrics.collection_efficiency_pct}% → AT&amp;C ${s.metrics.atc_loss_pct}% (identity checked in CI)</p>`;
  }
  if (s.note) el.innerHTML += `<p class="stage-note">${s.note}</p>`;
  return el;
}

function connector(edge) {
  const el = document.createElement("div");
  if (edge && edge.kind === "bridge") {
    el.className = "connector bridge";
    el.innerHTML = `
      <div class="edge-label">⚡ <strong>The power→energy bridge.</strong>
        Implied fleet utilisation FY2023-24: <strong>${(edge.factor * 100).toFixed(1)}%</strong></div>
      <div class="citizen">${edge.citizen_note}</div>
      <div class="citizen">${edge.factor_label}</div>`;
  } else {
    el.className = "connector";
    el.innerHTML = `<div class="arrow">↓</div>` +
      (edge && edge.citizen_note ? `<div class="citizen">${edge.citizen_note}</div>` : "");
  }
  return el;
}

async function main() {
  const chain = await (await fetch("data/chain.json")).json();
  document.getElementById("period").textContent =
    `${chain.period} · ${chain.scope} · ${chain.period_basis}`;
  const root = document.getElementById("chain");
  const edgeFor = (a, b) =>
    chain.edges.find((e) => e.from === a && e.to === b);

  const order = chain.stages.map((s) => s.id);
  chain.stages.forEach((s, i) => {
    root.appendChild(stageBox(s));
    if (i < chain.stages.length - 1) {
      // bridge S1→S4 stands in visually until S3 is populated
      const direct = edgeFor(s.id, order[i + 1]) ||
        (s.id === "S3" ? edgeFor("S1", "S4") : null) ||
        (s.id === "S6" ? edgeFor("S6", "S7") : null);
      root.appendChild(connector(direct));
    }
  });

  const bypass = chain.edges.find((e) => e.kind === "side_flow");
  if (bypass) {
    const el = document.createElement("div");
    el.className = "sideflow";
    el.innerHTML = `<strong>${bypass.label}</strong>
      <span class="stage-value"> ${fmt(bypass.gap_value)} <small>${bypass.gap_unit}${bypass.provisional ? " · provisional" : ""}</small></span>
      <div class="citizen">${bypass.citizen_note}</div>`;
    root.appendChild(el);
  }

  const prov = document.getElementById("provenance");
  const items = [];
  for (const s of chain.stages) {
    if (s.source_file) items.push(`<li>${s.id} ${s.name}: parsed from <code>${s.source_file}</code> (${s.source})</li>`);
    if (s.hand_verified) items.push(`<li>${s.id} ${s.name}: PFC Report on Performance of Power Utilities 2023-24 (${s.source}), hand-verified 2026-08-09 — parser pending</li>`);
  }
  for (const e of chain.edges) {
    if (e.source_file) items.push(`<li>${e.label || e.kind}: parsed from <code>${e.source_file}</code> (${e.source})</li>`);
  }
  prov.innerHTML = items.join("");
}

main();
