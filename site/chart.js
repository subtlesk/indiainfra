/* Time-series line charts from site/data/series.json.
   Palette: dataviz reference categorical slots 1-4, entity-stable across charts.
   Light-mode aqua/yellow are sub-3:1 on the surface -> relief rule: direct
   end-labels + data table (both shipped here). */

const SERIES = [
  { key: "thermal", label: "Thermal", slot: 2 },
  { key: "hydro",   label: "Hydro",   slot: 1 },
  { key: "res",     label: "RES",     slot: 3 },
  { key: "nuclear", label: "Nuclear", slot: 4 },
];

const fmtNum = (n, d = 0) => n.toLocaleString("en-IN", { maximumFractionDigits: d });

function lineChart(host, rows, { title, subtitle, unit, divisor, rawUnit }) {
  const W = 860, H = 392, M = { t: 30, r: 96, b: 34, l: 56 };
  const pw = W - M.l - M.r, ph = H - M.t - M.b;
  const years = rows.map((r) => r.year);
  const x0 = years[0], x1 = years[years.length - 1];
  const yMax = Math.max(...rows.map((r) => r.total)) / divisor;
  const yStep = niceStep(yMax / 4.5);
  const yTop = Math.ceil(yMax / yStep) * yStep;
  const X = (yr) => M.l + (pw * (yr - x0)) / (x1 - x0);
  const Y = (v) => M.t + ph - (ph * v) / yTop;

  const fig = document.createElement("figure");
  fig.className = "viz-root";
  fig.innerHTML = `<figcaption><strong>${title}</strong><span class="viz-sub">${subtitle}</span></figcaption>
    <div class="viz-legend" role="list">${SERIES.map((s) =>
      `<span role="listitem"><i style="background:var(--series-${s.slot})"></i>${s.label}</span>`).join("")}
    </div>`;

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `${title}, line chart, 1947 to 2024`);
  let g = "";

  for (let v = 0; v <= yTop; v += yStep) {
    g += `<line class="grid" x1="${M.l}" y1="${Y(v)}" x2="${W - M.r}" y2="${Y(v)}"/>` +
         `<text class="tick ynum" x="${M.l - 8}" y="${Y(v) + 4}" text-anchor="end">${fmtNum(v)}</text>`;
  }
  for (let yr = 1950; yr <= 2020; yr += 10) {
    g += `<text class="tick" x="${X(yr)}" y="${H - M.b + 18}" text-anchor="middle">${yr}</text>`;
  }
  g += `<line class="axis" x1="${M.l}" y1="${Y(0)}" x2="${W - M.r}" y2="${Y(0)}"/>`;
  g += `<text class="tick" x="${M.l - 8}" y="14" text-anchor="end">${unit}</text>`;

  for (const s of SERIES) {
    const pts = rows.map((r) => `${X(r.year)},${Y(r[s.key] / divisor)}`).join(" ");
    g += `<polyline class="series" points="${pts}" style="stroke:var(--series-${s.slot})"/>`;
    g += rows.map((r) =>
      `<circle class="dot" cx="${X(r.year)}" cy="${Y(r[s.key] / divisor)}" r="2.2" style="fill:var(--series-${s.slot})"/>`).join("");
  }

  // direct end-labels, nudged apart (relief for low-contrast slots)
  const ends = SERIES.map((s) => ({ s, y: Y(rows[rows.length - 1][s.key] / divisor) }))
    .sort((a, b) => a.y - b.y);
  for (let i = 1; i < ends.length; i++) {
    if (ends[i].y - ends[i - 1].y < 15) ends[i].y = ends[i - 1].y + 15;
  }
  for (const e of ends) {
    g += `<text class="endlabel" x="${W - M.r + 8}" y="${e.y + 4}">${e.s.label}</text>`;
  }

  g += `<line class="cross" x1="0" y1="${M.t}" x2="0" y2="${H - M.b}" style="display:none"/>`;
  svg.innerHTML = g;
  fig.appendChild(svg);

  const tip = document.createElement("div");
  tip.className = "viz-tip";
  tip.style.display = "none";
  fig.appendChild(tip);

  const cross = svg.querySelector(".cross");
  svg.addEventListener("mousemove", (ev) => {
    const pt = svg.createSVGPoint();
    pt.x = ev.clientX; pt.y = ev.clientY;
    const { x } = pt.matrixTransform(svg.getScreenCTM().inverse());
    const yr = x0 + ((x - M.l) / pw) * (x1 - x0);
    const row = rows.reduce((a, b) => (Math.abs(b.year - yr) < Math.abs(a.year - yr) ? b : a));
    cross.setAttribute("x1", X(row.year)); cross.setAttribute("x2", X(row.year));
    cross.style.display = "";
    tip.style.display = "";
    tip.innerHTML = `<strong>${row.year}</strong>` +
      SERIES.map((s) => `<div><i style="background:var(--series-${s.slot})"></i>${s.label} <b>${fmtNum(row[s.key] / divisor, 1)}</b></div>`).join("") +
      `<div class="tot">Total <b>${fmtNum(row.total / divisor, 1)}</b> ${unit}</div>` +
      (row.residual ? `<div class="resid">residual ${fmtNum(row.residual / divisor, 1)} (source total excl. gas/diesel)</div>` : "");
    const r = fig.getBoundingClientRect();
    const left = ((X(row.year) / W) * r.width);
    tip.style.left = Math.min(left + 12, r.width - 170) + "px";
  });
  svg.addEventListener("mouseleave", () => { cross.style.display = "none"; tip.style.display = "none"; });

  // data table (relief + accessibility)
  const det = document.createElement("details");
  det.innerHTML = `<summary>Data table (${rawUnit}, as printed by CEA)</summary>
    <div class="viz-tablewrap"><table>
      <thead><tr><th>Year</th>${SERIES.map((s) => `<th>${s.label}</th>`).join("")}<th>Total</th><th>Residual</th></tr></thead>
      <tbody>${rows.map((r) =>
        `<tr><td>${r.year}</td>${SERIES.map((s) => `<td>${fmtNum(r[s.key])}</td>`).join("")}<td>${fmtNum(r.total)}</td><td>${r.residual ? fmtNum(r.residual) : ""}</td></tr>`).join("")}
      </tbody></table></div>`;
  fig.appendChild(det);
  host.appendChild(fig);
}

function niceStep(raw) {
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  for (const m of [1, 2, 5, 10]) if (raw <= m * mag) return m * mag;
  return 10 * mag;
}

async function charts() {
  const s = await (await fetch("data/series.json")).json();
  const host = document.getElementById("longview");
  lineChart(host, s.capacity_MW, {
    title: "Installed capacity by mode, 1947–2024",
    subtitle: "GW · utilities · points are CEA's published years (plan-ends before 1992)",
    unit: "GW", divisor: 1000, rawUnit: "MW",
  });
  lineChart(host, s.generation_GWh, {
    title: "Gross generation by mode, 1947 – FY 2023-24",
    subtitle: "billion units (1 BU = 1 TWh = 1,000 GWh) · utilities · fiscal years from 1955-56",
    unit: "BU", divisor: 1000, rawUnit: "GWh",
  });
  const p = document.createElement("p");
  p.className = "fine";
  p.innerHTML = `Same four modes, two very different pictures: in FY2023-24 renewables were
    <strong>${(100 * s.capacity_MW.at(-1).res / s.capacity_MW.at(-1).total).toFixed(0)}%</strong> of capacity but
    <strong>${(100 * s.generation_GWh.at(-1).res / s.generation_GWh.at(-1).total).toFixed(0)}%</strong> of generation,
    while thermal was <strong>${(100 * s.capacity_MW.at(-1).thermal / s.capacity_MW.at(-1).total).toFixed(0)}%</strong> of capacity and
    <strong>${(100 * s.generation_GWh.at(-1).thermal / s.generation_GWh.at(-1).total).toFixed(0)}%</strong> of generation.
    That divergence is the power→energy bridge in the chain above — utilisation differs by mode.
    Source: CEA Growth Book 2024 (archived); residuals in the data tables are CEA's own totals not summing, published rather than hidden.`;
  host.appendChild(p);
}

charts();
