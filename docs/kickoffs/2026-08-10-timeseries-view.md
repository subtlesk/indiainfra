# Kickoff: time-series view

**Branch:** `cc/timeseries-view-2026-08-10` · **Date:** 2026-08-10 · **Requested by:** user ("shouldn't this be through line graphs?")

## What

Add historical line charts to the dashboard, complementing (not replacing) the chain diagram:

1. **Installed capacity by mode, 1947–2024 (MW)** — Growth Book Table 2
2. **Gross generation by mode, 1947–2024 (GWh)** — Growth Book Table 3

Both parsed from the already-archived `data/raw/SRC-1/growth-book/Growth_Book_2024.pdf`. No new fetches.

## Decisions

- **Chain diagram stays the structural spine** (spec: the UI reads the chain). Line charts answer "how did each stage's headline move over time"; the chain answers "what connects to what and where the gaps are".
- **Four series per chart: Thermal, Hydro, Nuclear, RES** — the finest grouping common to both tables. Fuel-level detail stays in the chain view's breakdown bars.
- **True time x-scale.** Pre-1992 rows are plan-end years (1947, 1950, 1956, 1961, …) — irregular spacing. Points plot at actual years with visible data-point dots, so sampling density is honest; index spacing would distort the early decades.
- **Colors** from the validated dataviz reference palette, first four categorical slots, entity-stable across charts: hydro=blue, thermal=orange, RES=aqua, nuclear=yellow. Palette re-validated with the skill's checker in both modes. Aqua/yellow are sub-3:1 on light surface → relief rule: direct end-labels + a data-table view ship with each chart.
- **One y-axis per chart, linear.** Capacity (MW) and generation (GWh) are separate charts, never dual-axis.
- **Pipeline emits `site/data/series.json`** with a per-row invariant: thermal + hydro + nuclear + res = total (source rounding tolerance). Violation fails the build.

## Out of scope

Per-capita / T&D chart series (Growth Book charts are label-soup to parse — separate task), state-level series, monthly resolution.
