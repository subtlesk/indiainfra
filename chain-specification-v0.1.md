# Chain Specification
**Phase 0, artifact 0.1 — draft v0.1**
**India Electricity Dashboard**

---

## What this artifact is

The chain is the **structural spine** of the whole dashboard. It is the answer to "capacity and utilisation are two separate lines and the difference must be explained" — generalised.

Every headline number sits at a stage. Every gap between stages has a **name**, a **cause decomposition**, and its **own data source**. Drilling into a gap is therefore mechanical rather than bespoke: the UI reads the chain, it does not hard-code it.

**The honest shape is not a line.** It is a trunk with side inflows, side outflows, and one bypass. Pretending otherwise would reproduce exactly the kind of simplification this project exists to correct.

```
                                    imports ──┐   ┌── exports
                                              ▼   ▼
S0 pipeline → S1 installed → S2 available → S3 dispatched → S4 gross gen
                                                                  │
                                                                  ▼
                                                            S5 net gen
                                                                  │
                                              storage ◄───────────┤
                                             (round-trip loss)    │
                                                                  ▼
                                                     S6 delivered to distribution
                                                                  │
                                                                  ▼
                                                     S7 billed & collected
                                                                  │
                                                                  ▼
                                                     S8 service received

  BYPASS: captive · off-grid · rooftop · open access
          enter at S4/S5 and skip S6–S7 wholly or partly
```

---

## Units: the honest problem

Stages 0–3 are measured in **power (MW)**. Stages 4–8 are measured in **energy (GWh)**. They are not the same quantity, and the transition between them is the single most misunderstood step in the whole sector.

**Rule:** the chain is specified over a **reference period** — the fiscal year — and the bridge from power to energy is explicit at S3→S4. Nothing in the UI may imply MW and GWh are interchangeable. This is design rule 1 from artifact 0.9 (P-24) expressed structurally.

---

## Stage specifications

### S0 — Pipeline

| | |
|---|---|
| **Metric** | `pipeline_capacity_MW` by milestone status |
| **Unit** | MW |
| **Sub-states** | announced → environmental clearance → grid connectivity granted → financial close → under construction → synchronised → commercially operational |
| **Gap to S1** | **Attrition and slippage** |
| **Gap drivers** | clearance refusal · land acquisition failure · financing failure · PPA not signed · promoter insolvency · schedule slippage |
| **Sources** | S3 GEM, PARIVESH, CTU connectivity lists, S1 CEA Broad Status, S6 filings, S9 credit record |
| **Identity** | `commissioned(cohort) = announced(cohort) × Π(stage conversion rates)`; slippage measured as median months between declared and actual COD |
| **Coverage** | A (2015–) · B (2005–2015) · ✗ (pre-2005) |
| **Serves** | G1, G2, G3, G4, B7 |
| **Risks** | P-13 milestone-date shopping · P-21 pipeline inflation · P-07 survivorship |

**Design note:** six dates per project, all stored. The user chooses which one means "built." Never hard-code one.

---

### S1 — Installed capacity

| | |
|---|---|
| **Metric** | `installed_capacity_MW` |
| **Identity** | `IC(t) = Σ commissioned(≤t) − Σ retired(≤t) ± derating(t) + residual(t)` |
| **Gap to S2** | **Unavailability** |
| **Sources** | S1 CEA (authority), S3 GEM (bottom-up reconstruction), S2 MNRE (off-grid extension) |
| **Coverage** | A (1970–) · B (1947–1970, national only) |
| **Serves** | A1, A2, A3, A6, B1, B2, B3, C1–C4, D7, I4 |
| **Risks** | DC-01 hydro reclassification · DC-05 solar AC/DC · DC-07 captive exclusion · P-01, P-03, P-06 |

**The residual is a first-class term.** Named assets ≥25 MW will not sum to the CEA total. The difference — rooftop, captive, small hydro, off-grid, unregistered — is published, itemised, and is the answer to question I4. Do not force it to zero.

**Derating matters and is usually ignored:** old thermal units are progressively derated below nameplate. Nameplate capacity and current rated capacity diverge over a 40-year asset life.

---

### S2 — Available capacity

| | |
|---|---|
| **Metric** | `available_capacity_MW` |
| **Identity** | `AC(t) = IC(t) × (1 − forced_outage − planned_outage − fuel_unavailability − partial_derating)` |
| **Gap name** | **Outage and unavailability** |
| **Gap drivers** | planned maintenance · forced outage · coal stock shortage · gas non-availability · hydrology (seasonal) · transmission constraint at the bus |
| **Sources** | S1 CEA outage reports, S4 Grid-India |
| **Coverage** | A (2010–) · B (1990–2010, fuel-level only) · ✗ (pre-1990) |
| **Serves** | D1 |
| **Risks** | P-24 |

**Seasonality is not noise here.** Hydro availability swings enormously between monsoon and pre-monsoon. Annual averages destroy the story; the stage must support monthly resolution from 2010.

---

### S3 — Dispatched

| | |
|---|---|
| **Metric** | `scheduled_capacity_MW`, `dispatched_MW` |
| **Identity** | Not multiplicative. `Dispatch = f(AC, demand, merit order, must-run obligations, offtake willingness, transmission capacity)` |
| **Gap name** | **Under-dispatch** |
| **Gap drivers** | insufficient demand · higher-merit plant available · renewable must-run displacement · **discom unwilling to buy (financial, not physical)** · transmission congestion |
| **Sources** | S4 Grid-India, MERIT portal, S1 |
| **Coverage** | A (2011–) · C (pre-2011, inferred from PLF only) |
| **Serves** | D1, D3, D5, D6 |
| **Risks** | P-06 |

**This is where the chain stops being physics and becomes economics.** A plant that is available and not dispatched is usually a financial fact, not a technical one — it traces forward to S7 and the discom's balance sheet. That link (S3 ↔ S7) is the most important non-adjacent relationship in the model and must be navigable in the UI.

---

### S3 → S4 — The power-to-energy bridge

| | |
|---|---|
| **Identity** | `gross_generation_GWh = Σ_units (capacity_MW × hours_in_period × utilisation_factor) / 1000` |
| **Factor** | PLF for dispatchable plant; CUF for variable renewables |
| **Meaning** | PLF blends *availability*, *dispatch* and *demand*; CUF is dominated by *resource* |
| **Serves** | A1, A6, D2, D3 |
| **Risks** | **P-06 denominator switching lives here** · P-24 |

**This bridge is the answer to question A6.** Coal at ~70% and solar at ~20% is the mechanical reason capacity share and generation share diverge so sharply. The bridge must be a first-class, explorable object — not a formula in a footnote. If one screen in this dashboard teaches a citizen one thing, it is this one.

---

### S4 — Gross generation

| | |
|---|---|
| **Metric** | `gross_generation_GWh` by fuel, owner, state |
| **Identity** | above |
| **Gap to S5** | **Auxiliary consumption** |
| **Sources** | S1 CEA, S4 Grid-India |
| **Coverage** | A (1980–) · B (1947–1980) |
| **Serves** | A1, A2, A6, D2, D3, H2 |
| **Risks** | DC-14 gross/net · DC-11 fiscal vs calendar · P-14 |

---

### S5 — Net generation

| | |
|---|---|
| **Metric** | `net_generation_GWh` |
| **Identity** | `NG = GG × (1 − aux_consumption_rate)` |
| **Gap name** | **Plant's own consumption** |
| **Typical magnitude** | coal ~6–9% · gas ~2–3% · hydro ~0.5–1% · solar ~0.5% *(estimates — to be measured in Phase 3, not assumed)* |
| **Gap drivers** | fuel type · unit size · vintage · cooling technology · pollution-control equipment (FGD raises auxiliary consumption materially) |
| **Sources** | S1 |
| **Coverage** | A (2010–) · B (1980–2010, fuel-level) · C (pre-1980) |
| **Serves** | A1, E1 |
| **Risks** | DC-14 · P-10 |

---

### Side nodes (entering between S5 and S6)

| Node | Direction | Metric | Source | Note |
|---|---|---|---|---|
| **Imports / exports** | Both | `cross_border_GWh` | S4 | Trade with Bhutan, Nepal, Bangladesh. Small but non-zero; omitting it breaks the identity |
| **Storage** | Sink then source | `storage_charge_GWh`, `storage_discharge_GWh`, round-trip efficiency ~80–90% *(estimate)* | S4, S1 | Currently minor, structurally significant and growing fast. Model it now, populate it later |
| **Captive / off-grid / rooftop** | Bypass | `captive_generation_GWh` | S2 MNRE, S1 | **Bypasses S6–S7 entirely.** This is why national totals and consumer-facing totals never reconcile |
| **Open access** | Partial bypass | `open_access_GWh` | S8 (state phase) | Consumer buys direct; uses the wires but not the discom's energy. Erodes discom finances — links to S7 |

---

### S6 — Delivered to distribution

| | |
|---|---|
| **Metric** | `energy_delivered_GWh` |
| **Identity** | `ED = NG + imports − exports − storage_loss − transmission_loss` |
| **Gap name** | **Transmission loss** |
| **Typical magnitude** | inter-state ~3–4% *(estimate)*; intra-state transmission additional |
| **Gap drivers** | distance · voltage level · loading · network age |
| **Sources** | S4 Grid-India, PGCIL |
| **Coverage** | A (2011–) · C (pre-2011) |
| **Serves** | A3, E1 |
| **Risks** | P-10 mismatched bases |

---

### S7 — Billed and collected

| | |
|---|---|
| **Metrics** | `energy_billed_GWh`, `revenue_collected`, `AT&C_loss_%` |
| **Identity** | `AT&C = 1 − (billing_efficiency × collection_efficiency)` |
| **Gap name** | **Aggregate technical and commercial loss** |
| **Gap drivers** | distribution technical loss · unmetered supply (notably agricultural) · theft · under-billing · billed-but-uncollected |
| **Typical magnitude** | ~15–16% nationally in recent years, down from roughly 38% in the early 2000s; state range from single digits to over 40% *(estimates — verify in Phase 3)* |
| **Sources** | S5 PFC, S8 state returns |
| **Coverage** | A (2001–) · ✗ (pre-2001 as AT&C; T&D only, non-comparable) |
| **Serves** | E1, E2, F1, F3, F4 |
| **Risks** | **DC-04 the T&D→AT&C break** · P-10 · P-25 national average masking |

**S7 feeds back to S3.** A discom that cannot collect cannot pay gencos, so it schedules less power, so available plant sits idle, so PLF falls. **This feedback loop is the central mechanism of the Indian power sector** and the chain must represent it as an explicit edge, not leave it to prose.

---

### S8 — Service received

| | |
|---|---|
| **Metrics** | `per_capita_consumption_kWh`, `supply_hours`, `interruption_frequency`, `energy_not_served` |
| **Gap name** | **Reliability gap** |
| **Gap drivers** | load shedding (financial) · feeder faults · local network capacity · unmetered/unconnected households |
| **Sources** | S1, Prayas ESMI, S8 |
| **Coverage** | B (2015–) · C (2000–2015) · ✗ (pre-2000) |
| **Serves** | A4, B5, B6, E3, E4, H1, H3 |
| **Risks** | P-22 input-for-outcome · P-23 stock without flow · P-25 |

---

## The gap object

Every gap is one row, queryable, and drives the UI without bespoke code:

```sql
chain_gap (
  gap_id, from_stage, to_stage, as_of, period_basis,
  from_value, to_value, gap_value, gap_unit,
  attributed jsonb,        -- {driver: value} for named drivers
  unexplained numeric,     -- must be published, never hidden
  confidence char(1),      -- A / B / C
  source_ids text[],
  definition_change_ids text[],
  citizen_note text        -- one plain sentence
)
```

**Invariant:** `Σ attributed + unexplained = gap_value`, exactly. This becomes invariant INV-18 in artifact 0.7 and fails the build if violated.

---

## Coverage degradation by era

The chain is not equally deep across time. This must be visible, not apologised for.

| Era | Stages available | Effective chain depth |
|---|---|---|
| 1947–1970 | S1, S4 | 2 |
| 1970–1990 | S1, S4, S5 | 3 |
| 1990–2001 | S0(weak), S1, S4, S5 | 4 |
| 2001–2011 | S0, S1, S2(partial), S4, S5, S7 | 6 |
| 2011– | S0–S8 all | 9 |

**UI treatment:** the chain diagram physically shortens as the user moves the time slider backwards. Stages that do not exist for the selected year are greyed with "not measured in this period." This is one of the more honest things the dashboard can do — and it directly answers question I3.

---

## Cross-sector generalisation

The chain abstraction is the reusable asset. Every infrastructure sector has the same shape:

| Sector | Built | Available | Used | Delivered | Paid for | Service received |
|---|---|---|---|---|---|---|
| Electricity | MW installed | MW available | MW dispatched | GWh delivered | Revenue collected | Hours of supply |
| Roads | km built | km motorable | traffic volume | freight/pax moved | tolls collected | travel time, safety |
| Railways | route-km | serviceable | trains run | tonne-km, pax-km | fares collected | punctuality |
| Water | connections | functional | supplied | litres delivered | tariff collected | hours, quality |

**If the chain schema survives contact with a second sector without modification, the abstraction is correct.** That is the exit test for Phase 5.

---

## Phase 0 tasks arising

| # | Task | Effort (est.) |
|---|---|---|
| 1 | Verify auxiliary consumption rates by fuel against CEA primary data (replace estimates) | 2–3 hrs |
| 2 | Confirm the S3↔S7 feedback edge is representable in the schema | 1 hr |
| 3 | Specify the six pipeline milestone dates against actual GEM and PARIVESH field availability | 2 hrs |
| 4 | Write the nine `citizen_note` strings for stage gaps | 1–2 hrs |
| 5 | Define monthly vs annual resolution per stage (S2 and S3 need monthly; S1 does not) | 1 hr |
| **Total** | | **7–9 hrs** |

---

## Open design question for the next artifact

The schema DDL (0.6) must decide whether `chain_gap` rows are **materialised** (computed at build time, stored) or **derived** (computed in the browser from stage values). Materialised is simpler to validate in CI and lets the gap carry its own `citizen_note` and attribution. Derived is more flexible for user-selected periods and filters.

**Leaning: materialised for the canonical annual national series, derived for user-filtered views.** Hybrid, with the identity invariant enforced on the materialised set. To be resolved in 0.6.
