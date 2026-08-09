# Chain Specification
**Phase 0, artifact 0.1 — draft v0.2**
**India Electricity Dashboard**

> **v0.1 → v0.2 changelog**
> 1. The gap object is generalised to a **`chain_edge`** object with four kinds — `gap`, `bridge`, `feedback`, `side_flow` — because two things v0.1 called first-class (the S3→S4 power-to-energy bridge and the S3↔S7 feedback loop) could not be represented by an additive gap row.
> 2. Source codes are renamed **SRC-n** to end the collision with stage codes S0–S8.
> 3. The diagram is corrected: imports/exports and storage attach between S5 and S6, where the S6 identity actually consumes them. v0.1 drew them near S2–S3.
> 4. S8 gets an explicit composition statement and the bypass flows get a defined re-entry at S8.
> 5. All registry codes this artifact depends on (coverage grades, sources, questions, pitfalls, definition changes) are **defined inline** — minimally — because the registry artifacts are not yet written. These inline definitions are the seed of those artifacts, not a substitute for them.
> 6. Coverage claims are corrected against **verified source availability (checked August 2026)**: S3 online archives begin FY2013-14, not 2011; ESMI is discontinued; UDAY is dead; MERIT has no history.
> 7. Phase 0 tasks 1–5 are folded in: verified auxiliary-consumption and loss figures, the feedback-edge representation, the milestone-date field mapping against real sources, the nine citizen notes, and per-stage resolution decisions.
> 8. Decisions taken 2026-08-09: v1 scope is **national + annual**; MERIT capture is **deferred**; materialisation is **hybrid** (canonical materialised, filtered views derived).

---

## What this artifact is

The chain is the **structural spine** of the whole dashboard. It is the answer to "capacity and utilisation are two separate lines and the difference must be explained" — generalised.

Every headline number sits at a stage. Every edge between stages has a **name**, a **kind**, a **decomposition**, and its **own data source**. Drilling into an edge is therefore mechanical rather than bespoke: the UI reads the chain, it does not hard-code it.

**The honest shape is not a line.** It is a trunk with side inflows, side outflows, one bypass, and one feedback loop. Pretending otherwise would reproduce exactly the kind of simplification this project exists to correct.

```
S0 pipeline → S1 installed → S2 available → S3 dispatched ──[bridge]── S4 gross gen
                                                 ▲                          │
                                                 │ feedback                 ▼
                                                 │ (financial)       S5 net gen
                                                 │                          │
                                                 │       imports ──►┐      │
                                                 │       exports ◄──┤◄─────┤
                                                 │       storage ◄─►┘      │
                                                 │       (round-trip loss) ▼
                                                 │           S6 delivered to distribution
                                                 │                          │
                                                 │                          ▼
                                                 └────────── S7 billed & collected
                                                                            │
                                                                            ▼
                                                             S8 service received
                                                                            ▲
  BYPASS: captive · off-grid · rooftop · open access ───────────────────────┘
          generated at S4/S5 scale, skips S6–S7 wholly or partly,
          re-enters the picture at S8 as service received
```

---

## Units: the honest problem

Stages 0–3 are measured in **power (MW)**. Stages 4–8 are measured in **energy (GWh)**. They are not the same quantity, and the transition between them is the single most misunderstood step in the whole sector.

**Rule:** the chain is specified over a **reference period** — the fiscal year — and the bridge from power to energy is explicit at S3→S4. Nothing in the UI may imply MW and GWh are interchangeable. This is design rule 1 from artifact 0.9 (P-24) expressed structurally.

---

## The edge object

v0.1 specified a `chain_gap` table and immediately demanded two things it could not hold: a multiplicative, unit-changing bridge and a feedback loop with no accounting identity. v0.2 generalises. **Every connection in the diagram is one `chain_edge` row**, and the UI renders each by its kind — still mechanical, still no bespoke code per edge.

```sql
chain_edge (
  edge_id, kind,                -- 'gap' | 'bridge' | 'feedback' | 'side_flow'
  from_stage, to_stage,
  as_of, period_basis,          -- fiscal year canonical; DC-11 applies
  from_value, from_unit,
  to_value,   to_unit,          -- units may differ only when kind = 'bridge'
  gap_value,  gap_unit,         -- gap and side_flow kinds only
  attributed jsonb,             -- {driver: value}; semantics depend on kind
  unexplained numeric,          -- must be published, never hidden
  factor numeric,               -- bridge only: realised utilisation factor
  indicators jsonb,             -- feedback only: paired series references + lag
  confidence char(1),           -- coverage grade A / B / C
  source_ids text[],            -- SRC-n codes
  definition_change_ids text[], -- DC-nn codes
  citizen_note text             -- one plain sentence
)
```

Per-kind invariants (these become INV-18a–d in artifact 0.7 and fail the build if violated):

| Kind | Invariant | Edges |
|---|---|---|
| `gap` | `Σ attributed + unexplained = gap_value`, exactly; `from_unit = to_unit` | S0→S1, S1→S2, S2→S3, S4→S5, S5→S6, S6→S7, S7→S8 |
| `bridge` | `to_value = Σ_segments (from_value_seg × hours_in_period × factor_seg) / 1000`, exactly; segment decomposition sums to the total, no residual permitted to hide | S3→S4 |
| `side_flow` | signed `gap_value` enters the downstream stage's identity; the S6 identity must balance with side flows included | imports, exports, storage, bypass |
| `feedback` | **no accounting invariant** — instead: both indicator series must exist for the period, with a documented lag; the edge is invalid without them | S7→S3 |

**The feedback edge, resolved (was Phase 0 task 2).** S7→S3 is causal, not arithmetic: discoms that cannot collect cannot pay, so they schedule less, so available plant sits idle. It is representable as a `chain_edge` of kind `feedback` whose `indicators` pair discom payables to gencos (SRC-5, PRAAPTI) against thermal PLF / scheduling shortfall (SRC-1, SRC-4), with the lag documented. It carries a citizen_note and is navigable in the UI exactly like a gap — it just renders as paired trend lines rather than a waterfall. **This closes task 2: yes, representable, as a distinct kind, not as a gap.**

---

## Inline registry definitions

The registry artifacts these codes belong to are not yet written. Until they are, this section is normative. Everything here is extractable later without changing this document's meaning.

### Coverage grades

| Grade | Meaning |
|---|---|
| **A** | Published primary series, consistent definition, machine-readable or reliably parseable |
| **B** | Reconstructable from primary sources with stated assumptions, or partial coverage |
| **C** | Inferred or proxy only |
| **✗** | Not measured in the period |

### Source registry (verified against the live web, August 2026)

| Code | Source | What it gives the chain | Format & access | Depth | Status notes |
|---|---|---|---|---|---|
| **SRC-1** | CEA (cea.nic.in) | Installed capacity (monthly), thermal Broad Status (pipeline), generation, outage, aux consumption (annual) | PDF + **Excel** for installed capacity; Broad Status **PDF only, thermal only**; no API | Monthly archive to ~2006 online; annual series much deeper | Authority for S1, S4; net generation is **not** a routine series — derive it |
| **SRC-2** | MNRE (mnre.gov.in) | Rooftop (23.2 GW as of Nov-2025), off-grid/distributed solar, state splits | Web tables + monthly PDF; no API | Monthly cumulative snapshots, scattered pre-archive | Cumulative capacity only, not project-level; MNRE and CEA totals differ — reconcile, don't average |
| **SRC-3** | Global Energy Monitor trackers | Project-level pipeline: coal (≥30 MW, proposals since 2010), solar (operating ≥1 MW, prospective ≥20 MW), wind (≥10 MW); status + status-year | **Excel download** (registration form); genuinely machine-readable | Coal history to 2010; solar/wind trackers only exist since 2022 | Bi-annual releases (Jan/Jul); year-granularity milestones, **not a dated event log**; rooftop and sub-20 MW solar out of scope |
| **SRC-4** | Grid-India / POSOCO / NLDC | Daily PSP: demand met, generation by source, cross-border exchange; monthly reports; **applicable ISTS losses** (monthly, per CERC Sharing Regulations 2020) | PDF; XLS recent years; scriptable URL patterns, no API | Daily PSP archive **FY2013-14 onward** | grid-india.in TLS broken, posoco.in intermittent 502s — pipeline needs cert tolerance + retries |
| **SRC-5** | PFC — Report on Performance of Power Utilities | AT&C loss, billing/collection efficiency, discom financials, utility level | **PDF only** (hundreds of pages; parseable but painful); use pfcindia.co.in (pfcindia.com cert broken) | Annual from **2002-03**; 12–18 month lag | The authoritative S7 source; UDAY dashboard is dead; RDSS public dashboard is thin |
| **SRC-6** | Regulatory & company filings (SERC tariff orders, annual reports, rating rationales) | Financial close, PPA status, promoter health | PDF, unstructured | Patchy | C-grade by construction |
| **SRC-7** | PARIVESH (parivesh.nic.in) | Environmental clearance per proposal | Portal has **no bulk download**; use the **data.gov.in extract** ("Environmental Clearance Granted – Parivesh 2.0", CSV/JSON with API key) | Post-2014 strong; older via archives | **No common project ID with CEA/GEM** — fuzzy name+capacity+state matching is unavoidable |
| **SRC-8** | State returns / SERC filings | State-phase S7/S8 detail | PDF | Varies by state | Deferred with state scope |
| **SRC-9** | Credit records (CRISIL/ICRA/CARE rationales, PRAAPTI payables) | Promoter insolvency, discom payables (feedback edge indicator) | Web/PDF | PRAAPTI from 2018 | |
| **SRC-10** | NPP (npp.gov.in) | Daily Generation Report (~1,750 units ≥25 MW), daily outage reports, coal stock | **PDF at predictable URLs**; dashboard JSON endpoints exist but are undocumented; no public API despite appearances | Daily DGR ongoing | The workhorse for S2 unit-level outage/generation — at the cost of PDF parsing at scale |
| **SRC-11** | Prayas ESMI (watchyourpower.org, Harvard Dataverse) | Minute-wise supply quality, ~200 locations, 18 states | Machine-readable archive | **2015 to ~early-2020s, then discontinued** | Historical layer only — there is no live public supply-quality feed |
| **SRC-12** | PIB / parliamentary answers | Supply hours (e.g., rural avg 22.36 hrs/day FY2025-26), scheme totals | Prose/PDF | Annual statements | The only current S8 supply-hours source; Saubhagya portal frozen at March 2022 |
| **SRC-13** | CTUIL connectivity / LTA lists | Grid connectivity granted (pipeline milestone) | PDF lists | Recent years | |
| **SRC-14** | MERIT (meritindia.in) | Real-time merit-order snapshot: state-wise procurement cost, generation mix | Live page; **no history, no download, no API** | Snapshot only | **Decision 2026-08-09: deferred.** Not needed for national+annual. If a dispatch-economics view is ever wanted, capture must start then — history is unrecoverable |
| **SRC-15** | data.gov.in | Structured extracts of PARIVESH, some NPP/CEA datasets | CSV/JSON/XML, API keys | Varies | Check freshness per catalog — extracts lag their sources |

### Question glosses *(provisional — the question registry does not exist yet; these are inferred from usage in v0.1 and must be confirmed when the registry is authored)*

| Family | Reading |
|---|---|
| **A** | National headline series: capacity, generation, losses, per-capita consumption over time. A6 specifically: *why do capacity share and generation share diverge so sharply?* |
| **B** | Historical narrative: eras, states, plans; B5/B6 electrification and access |
| **C** | Fuel/technology composition |
| **D** | Utilisation: D1 *why is available plant not running?*; D2/D3 PLF/CUF trends; D5/D6 dispatch economics |
| **E** | Losses and efficiency end-to-end (E1 *where does generated energy go?*), E3/E4 service quality |
| **F** | Discom finances: F1 AT&C, F3/F4 the money chain |
| **G** | Pipeline: G1–G4 what is coming, what dies, what slips |
| **H** | Consumption side: H1 per-capita, H2 by sector, H3 reliability experienced |
| **I** | Meta-questions about the data itself: I3 *why does data depth vary by era?*, I4 *why don't named assets sum to the official total?* |

### Pitfall glosses *(cited codes only; same provisional status)*

| Code | Gloss |
|---|---|
| P-06 | Denominator switching: PLF computed against installed vs available vs contracted capacity gives different answers; fix the denominator per view and label it |
| P-07 | Survivorship: pipelines measured only on surviving projects overstate conversion |
| P-10 | Mismatched bases: subtracting series with different coverage/period bases manufactures phantom gaps |
| P-13 | Milestone-date shopping: choosing whichever project date flatters the narrative |
| P-14 | Calendar/fiscal blending in generation series |
| P-21 | Pipeline inflation: announced MW treated as real MW |
| P-22 | Input-for-outcome: connections counted as if they were supply |
| P-23 | Stock without flow: cumulative counts hiding current rates |
| P-24 | Unit conflation: implying MW and GWh are interchangeable |
| P-25 | National averages masking state dispersion |
| DC-01 | Hydro reclassification (large vs small/renewable) breaks capacity series |
| DC-04 | The T&D→AT&C definitional break at ~2001 — the two loss series must never be joined |
| DC-05 | Solar AC vs DC nameplate convention |
| DC-07 | Captive in/out of official totals across eras |
| DC-11 | Fiscal vs calendar year basis |
| DC-14 | Gross vs net generation reporting basis |

---

## Stage specifications

### S0 — Pipeline

| | |
|---|---|
| **Metric** | `pipeline_capacity_MW` by milestone status |
| **Unit** | MW |
| **Milestones** | announced → environmental clearance → grid connectivity granted → financial close → construction start → synchronised → commercially operational *(seven dated milestones; v0.1 said "six dates" against a seven-state list — corrected)* |
| **Edge to S1** | `gap` — **Attrition and slippage** |
| **Gap drivers** | clearance refusal · land acquisition failure · financing failure · PPA not signed · promoter insolvency · schedule slippage |
| **Sources** | SRC-3, SRC-7, SRC-13, SRC-1 (Broad Status), SRC-6, SRC-9 |
| **Identity** | `commissioned(cohort) = announced(cohort) × Π(stage conversion rates)`; slippage measured as median months between declared and actual COD |
| **Coverage** | A (2015–) · B (2005–2015) · ✗ (pre-2005) |
| **Serves** | G1, G2, G3, G4, B7 |
| **Risks** | P-13 · P-21 · P-07 |

**Milestone dates vs reality (was Phase 0 task 3).** All seven dates are stored where obtainable; the user chooses which one means "built" — never hard-code one. But the sources do not supply seven clean dates:

| Milestone | Real source & grade |
|---|---|
| announced | SRC-3 status-year; press — **B** (year granularity) |
| environmental clearance | SRC-7 via SRC-15 extract, dated — **A** post-2014, B before |
| grid connectivity | SRC-13 PDF lists — **B** |
| financial close | SRC-6/SRC-9 only, unsystematic — **C** |
| construction start | SRC-3 status-year — **B** |
| synchronised | SRC-1 (thermal Broad Status; monthly reports) — **A** thermal, B others |
| commercial operation | SRC-1 installed capacity reports — **A** |

Two structural consequences: **(1)** there is no shared project ID across SRC-1/SRC-3/SRC-7 — the build must maintain its own project master with fuzzy matching (name + capacity + state), and match confidence is itself a published field; **(2)** GEM's solar prospective floor (≥20 MW) means the distributed pipeline is invisible at S0 — it surfaces only on commissioning, inside the S1 residual.

---

### S1 — Installed capacity

| | |
|---|---|
| **Metric** | `installed_capacity_MW` |
| **Identity** | `IC(t) = Σ commissioned(≤t) − Σ retired(≤t) ± derating(t) + residual(t)` |
| **Edge to S2** | `gap` — **Unavailability** |
| **Sources** | SRC-1 (authority), SRC-3 (bottom-up reconstruction), SRC-2 (off-grid extension) |
| **Coverage** | A (1970–) · B (1947–1970, national only) |
| **Serves** | A1, A2, A3, A6, B1, B2, B3, C1–C4, D7, I4 |
| **Risks** | DC-01 · DC-05 · DC-07 · P-01, P-03, P-06 |

**The residual is a first-class term.** Named assets ≥25 MW will not sum to the CEA total. The difference — rooftop, captive, small hydro, off-grid, unregistered — is published, itemised, and is the answer to question I4. Do not force it to zero.

**Derating matters and is usually ignored:** old thermal units are progressively derated below nameplate. Nameplate capacity and current rated capacity diverge over a 40-year asset life.

---

### S2 — Available capacity

| | |
|---|---|
| **Metric** | `available_capacity_MW` |
| **Identity** | `AC(t) = IC(t) × (1 − forced_outage − planned_outage − fuel_unavailability − partial_derating)` |
| **Edge name** | `gap` — **Outage and unavailability** |
| **Gap drivers** | planned maintenance · forced outage · coal stock shortage · gas non-availability · hydrology (seasonal) · transmission constraint at the bus |
| **Sources** | SRC-1 outage reports, SRC-10 daily outage reports, SRC-4 |
| **Coverage** | A (2010–) *(unit-level daily via SRC-10 — PDF parsing at scale; exact archive depth to be confirmed during ingestion)* · B (1990–2010, fuel-level only) · ✗ (pre-1990) |
| **Serves** | D1 |
| **Risks** | P-24 |

**Seasonality is not noise here.** Hydro availability swings enormously between monsoon and pre-monsoon. Annual averages destroy the story; the stage must support monthly resolution (see resolution table) even though the v1 canonical series is annual.

---

### S3 — Dispatched

| | |
|---|---|
| **Metric** | `scheduled_capacity_MW`, `dispatched_MW` |
| **Identity** | Not multiplicative. `Dispatch = f(AC, demand, merit order, must-run obligations, offtake willingness, transmission capacity)` |
| **Edge name** | `gap` — **Under-dispatch** |
| **Gap drivers** | insufficient demand · higher-merit plant available · renewable must-run displacement · **discom unwilling to buy (financial, not physical)** · transmission congestion |
| **Sources** | SRC-4 (daily PSP archive), SRC-1. SRC-14 is snapshot-only — see registry |
| **Coverage** | A (**2013-14–**, online PSP archive; v0.1's "2011–" is not obtainable online) · C (before, inferred from PLF only) |
| **Serves** | D1, D3, D5, D6 |
| **Risks** | P-06 |

**This is where the chain stops being physics and becomes economics.** A plant that is available and not dispatched is usually a financial fact, not a technical one — it traces forward to S7 and the discom's balance sheet. That link is now the explicit `feedback` edge S7→S3 (see the edge object), not prose.

---

### S3 → S4 — The power-to-energy bridge (`bridge` edge)

| | |
|---|---|
| **Identity** | `gross_generation_GWh = Σ_segments (capacity_MW × hours_in_period × utilisation_factor) / 1000` |
| **Factor** | PLF for dispatchable plant; CUF for variable renewables |
| **Meaning** | PLF blends *availability*, *dispatch* and *demand*; CUF is dominated by *resource* |
| **Invariant** | Segment decomposition sums to the total exactly (INV-18b); no additive gap — this edge has no `gap_value` |
| **Serves** | A1, A6, D2, D3 |
| **Risks** | **P-06 denominator switching lives here** · P-24 |

**This bridge is the answer to question A6.** Coal at ~70% and solar at ~20% is the mechanical reason capacity share and generation share diverge so sharply. The bridge is a first-class, explorable `chain_edge` — not a formula in a footnote. If one screen in this dashboard teaches a citizen one thing, it is this one.

---

### S4 — Gross generation

| | |
|---|---|
| **Metric** | `gross_generation_GWh` by fuel, owner, state |
| **Identity** | above |
| **Edge to S5** | `gap` — **Auxiliary consumption** |
| **Sources** | SRC-1, SRC-4, SRC-10 |
| **Coverage** | A (1980–) · B (1947–1980) |
| **Serves** | A1, A2, A6, D2, D3, H2 |
| **Risks** | DC-14 · DC-11 · P-14 |

---

### S5 — Net generation

| | |
|---|---|
| **Metric** | `net_generation_GWh` — **derived, not published**: no routine net-generation series exists; NG is computed as `GG × (1 − aux_rate)` with aux from annual SRC-1 publications and CERC norms |
| **Identity** | `NG = GG × (1 − aux_consumption_rate)` |
| **Edge name** | `gap` — **Plant's own consumption** |
| **Verified magnitude** *(was Phase 0 task 1)* | coal: CERC tariff norms ~5.25% (large supercritical) to ~8.5%+ (200 MW series); fleet actuals run ~8%, rising 2–4 pp at low loading · gas ~2–3% · large hydro ~0.7–1.2% (norm), small hydro 1.0% · solar ~0.5%. Verified against CERC Tariff Regulations 2019 and CEA operation-norms recommendations, Aug 2026. Grade **B** until CEA per-fuel actuals are parsed from the annual General Review during ingestion — then A |
| **Gap drivers** | fuel type · unit size · vintage · cooling technology · pollution-control equipment (FGD raises auxiliary consumption materially) |
| **Sources** | SRC-1; CERC norms |
| **Coverage** | A (2010–) · B (1980–2010, fuel-level) · C (pre-1980) |
| **Serves** | A1, E1 |
| **Risks** | DC-14 · P-10 |

---

### Side nodes (`side_flow` edges, entering between S5 and S6)

| Node | Direction | Metric | Source | Note |
|---|---|---|---|---|
| **Imports / exports** | Both | `cross_border_GWh` | SRC-4 (daily PSP; PDF tables) | Trade with Bhutan, Nepal, Bangladesh. Small but non-zero; omitting it breaks the S6 identity |
| **Storage** | Sink then source | `storage_charge_GWh`, `storage_discharge_GWh`, round-trip efficiency ~80–90% *(estimate)* | SRC-4, SRC-1 | Currently minor, structurally significant and growing fast. Model it now, populate it later |
| **Captive / off-grid / rooftop** | Bypass | `captive_generation_GWh` | SRC-2, SRC-1 | **Bypasses S6–S7 entirely, re-enters at S8.** This is why national totals and consumer-facing totals never reconcile |
| **Open access** | Partial bypass | `open_access_GWh` | SRC-8 (state phase) | Consumer buys direct; uses the wires but not the discom's energy. Erodes discom finances — links to the S7→S3 feedback edge |

---

### S6 — Delivered to distribution

| | |
|---|---|
| **Metric** | `energy_delivered_GWh` |
| **Identity** | `ED = NG + imports − exports − storage_loss − transmission_loss` |
| **Edge name** | `gap` — **Transmission loss** |
| **Verified magnitude** | applicable ISTS loss ~3% national average, 3–4% on RE-rich corridors (NLDC monthly under CERC Sharing Regulations 2020). **Caveat: this is the commercial settlement loss, not a physical delivered-vs-dispatched measurement**, and it excludes intra-state transmission — the identity must state which basis it uses (P-10) |
| **Gap drivers** | distance · voltage level · loading · network age |
| **Sources** | SRC-4 (applicable ISTS losses, monthly), PGCIL |
| **Coverage** | A (2013-14–, aligned with SRC-4 archives) · C (before) |
| **Serves** | A3, E1 |
| **Risks** | P-10 mismatched bases |

---

### S7 — Billed and collected

| | |
|---|---|
| **Metrics** | `energy_billed_GWh`, `revenue_collected`, `AT&C_loss_%` |
| **Identity** | `AT&C = 1 − (billing_efficiency × collection_efficiency)` |
| **Edge name** | `gap` — **Aggregate technical and commercial loss** |
| **Verified magnitude** | FY23: 15.11% · FY24: **16.12% — it rose**; billing efficiency 86.91%, collection 96.51% (PFC 2023-24). Early-2000s baseline ~36.6–38.9%. The long arc is downward but **not monotonic — never phrase it as steadily improving** |
| **Gap drivers** | distribution technical loss · unmetered supply (notably agricultural) · theft · under-billing · billed-but-uncollected |
| **Sources** | SRC-5 (annual PDF, 12–18 month lag, utility-level), SRC-8 |
| **Coverage** | A (2002-03–, the PFC series start) · ✗ (pre-2001 as AT&C; T&D only, non-comparable — DC-04) |
| **Serves** | E1, E2, F1, F3, F4 |
| **Risks** | **DC-04** · P-10 · P-25 |

**S7 feeds back to S3.** A discom that cannot collect cannot pay gencos, so it schedules less power, so available plant sits idle, so PLF falls. **This feedback loop is the central mechanism of the Indian power sector**, and it is now the explicit `feedback` edge S7→S3, with paired indicators (SRC-9 PRAAPTI payables vs SRC-1/SRC-4 PLF and scheduling) — not prose.

---

### S8 — Service received

| | |
|---|---|
| **Metrics** | `per_capita_consumption_kWh`, `supply_hours`, `interruption_frequency`, `energy_not_served` |
| **Composition** *(new in v0.2 — S8 had no identity)* | `service_received = grid supply via S7 + bypass re-entry (captive + rooftop self-consumption + open access)`. S8 is where the bypass rejoins: per-capita consumption computed from grid sales alone understates what people actually receive. Reliability metrics apply to grid supply only; bypass supply carries its own (unmeasured) reliability |
| **Edge name** | `gap` — **Reliability gap** (between energy billed and service actually experienced) |
| **Gap drivers** | load shedding (financial) · feeder faults · local network capacity · unmetered/unconnected households |
| **Sources** | SRC-11 (**archival only** — ESMI discontinued; minute-wise data 2015–~early-2020s on Harvard Dataverse), SRC-12 (annual supply-hours statements; e.g., rural avg 22.36 hrs/day FY2025-26), SRC-1, SRC-8. Saubhagya portal frozen at March 2022 — historical snapshot only |
| **Coverage** | B (2015–, and degrading since ESMI stopped) · C (2000–2015) · ✗ (pre-2000). **There is no live public supply-quality feed; this is the weakest stage in the chain and the spec must say so, not imply a feed exists** |
| **Serves** | A4, B5, B6, E3, E4, H1, H3 |
| **Risks** | P-22 · P-23 · P-25 |

---

## Citizen notes (was Phase 0 task 4)

One plain sentence per edge, stored in `citizen_note`, shown on drill-in. Drafts:

| Edge | citizen_note |
|---|---|
| S0→S1 attrition | Not everything announced gets built — projects die at clearances, land, financing, or contracts, and the survivors usually arrive late. |
| S1→S2 unavailability | A power plant is not available every hour — maintenance, breakdowns, missing coal, and dry reservoirs all take capacity off the table. |
| S2→S3 under-dispatch | Plants that could run are not always asked to run — often because the buyer cannot afford the power, not because anything is broken. |
| S3→S4 bridge | Megawatts measure what could be produced at any instant; units of electricity measure what actually was — a solar farm and a coal plant of the same size produce very different amounts over a year. |
| S4→S5 auxiliary | Power stations use some of their own electricity — a coal plant consumes roughly 6–9% of what it generates before anything leaves the gate. |
| S5→S6 transmission | Moving electricity across the country loses a few percent of it as heat in the wires. |
| S6→S7 AT&C | Of the electricity handed to distribution companies, a share is lost in local wires, never billed, or billed but never paid for. |
| S7→S8 reliability | Even paying customers do not always get power all day — supply hours, voltage, and interruptions are the gap between being connected and being served. |
| S7→S3 feedback | When distribution companies cannot collect what they bill, they cannot pay power plants — so they buy less, and plants that could run sit idle. |
| Bypass | A large slice of India's electricity never touches the public grid's books — factories generating for themselves, rooftop solar, direct purchases — which is why national totals and your electricity bill never quite reconcile. |

*(Ten notes, not nine: generalising to edges added the feedback note.)*

---

## Resolution per stage (was Phase 0 task 5)

v1 canonical series: **national, annual (fiscal year)** — decision 2026-08-09. The schema stores the finest resolution the source supports; the canonical build materialises annual.

| Stage | v1 canonical | Finest supported | From | Why |
|---|---|---|---|---|
| S0 | annual snapshots | event-dated milestones | 2010 (coal), 2022 (solar/wind trackers) | Pipeline is inherently event-based |
| S1 | annual | monthly | ~2006 (online monthly archive) | Capacity moves slowly; annual suffices for v1 |
| S2 | annual | **monthly required at schema level** | ~2010 | Hydro/coal-stock seasonality destroyed by annual averages |
| S3 | annual | **monthly required at schema level** | FY2013-14 | Same; also feedback-edge indicator needs monthly eventually |
| S4 | annual | monthly | ~2006 | |
| S5 | annual | annual | — | Aux rates are annual publications; monthly NG would be false precision |
| S6 | annual | monthly (ISTS loss series) | FY2013-14 | |
| S7 | annual | annual | 2002-03 | PFC is annual with 12–18 month lag |
| S8 | annual | annual (archival ESMI is minute-wise but frozen) | 2015 | |

---

## Coverage degradation by era

The chain is not equally deep across time. This must be visible, not apologised for.

| Era | Stages available | Effective chain depth |
|---|---|---|
| 1947–1970 | S1, S4 | 2 |
| 1970–1990 | S1, S4, S5 | 3 |
| 1990–2002 | S0(weak), S1, S4, S5 | 4 |
| 2002–2013 | S0, S1, S2(partial), S4, S5, S7 | 6 |
| 2013– | S0–S8 all *(S8 grade B, degrading since ESMI stopped)* | 9 |

*(Boundaries corrected from v0.1: the AT&C series starts 2002-03, not 2001; full-chain depth starts FY2013-14 with the online dispatch archive, not 2011.)*

**UI treatment:** the chain diagram physically shortens as the user moves the time slider backwards. Stages that do not exist for the selected year are greyed with "not measured in this period." This is one of the more honest things the dashboard can do — and it directly answers question I3.

---

## Data access reality (new in v0.2)

Findings from source verification, August 2026, with build consequences:

1. **There are no public APIs anywhere in the chain.** The ecosystem is PDF-first; Excel exists only for CEA installed capacity and recent Grid-India PSP reports; JSON only via data.gov.in extracts and undocumented dashboard endpoints. **Consequence: the ingestion layer is primarily a PDF-parsing layer, and parser test fixtures are part of the repo.**
2. **Sources die.** ESMI discontinued, UDAY dead, Saubhagya frozen, MERIT unarchived. **Consequence: archive-first ingestion — every fetched raw file is stored verbatim and versioned before parsing. The raw archive is a project asset, possibly the project asset.**
3. **Infrastructure is fragile.** Broken TLS on grid-india.in and pfcindia.com (use pfcindia.co.in), intermittent 502s on posoco.in. **Consequence: fetchers need cert tolerance, retries, and mirrors; a failed fetch must not fail the build if the raw archive already holds the file.**
4. **No shared project identity.** CEA, GEM, and PARIVESH have no common ID. **Consequence: the project master with fuzzy matching is a first-class build component, and match confidence is published data, not plumbing.**

---

## Cross-sector generalisation

The chain abstraction is the reusable asset. Every infrastructure sector has the same shape:

| Sector | Built | Available | Used | Delivered | Paid for | Service received |
|---|---|---|---|---|---|---|
| Electricity | MW installed | MW available | MW dispatched | GWh delivered | Revenue collected | Hours of supply |
| Roads | km built | km motorable | traffic volume | freight/pax moved | tolls collected | travel time, safety |
| Railways | route-km | serviceable | trains run | tonne-km, pax-km | fares collected | punctuality |
| Water | connections | functional | supplied | litres delivered | tariff collected | hours, quality |

**If the chain schema survives contact with a second sector without modification, the abstraction is correct.** That is the exit test for Phase 5. The v0.2 edge kinds generalise cleanly: every sector has gaps; roads' "bridge" is capacity→throughput; water has the same bypass (borewells) and the same feedback (unpaid tariffs → reduced supply).

---

## Materialisation (open question in v0.1, resolved in principle)

**Hybrid, decided 2026-08-09:** the canonical annual national series is **materialised** at build time — it carries citizen notes and attributions, and the per-kind invariants (INV-18a–d) are enforced on it in CI, failing the build on violation. User-filtered views are **derived** client-side from stage-level data. Artifact 0.6 owes the DDL, not the decision.

---

## Tasks arising (supersedes the v0.1 Phase 0 task table)

Tasks 1–5 from v0.1 are closed by this revision (task 1 at grade B pending CEA actuals). New/remaining:

| # | Task | Effort (est.) |
|---|---|---|
| 1 | Author artifact 0.6: schema DDL for `chain_stage` + `chain_edge`, invariants INV-18a–d as executable checks | 3–4 hrs |
| 2 | Extract the inline registries into their own artifacts (sources SRC-n; confirm/replace the provisional question and pitfall glosses) | 2–3 hrs |
| 3 | Parse CEA per-fuel auxiliary-consumption actuals from the annual General Review → upgrade S4→S5 gap to grade A | 2 hrs |
| 4 | Prototype the project master: fuzzy-match GEM ↔ CEA Broad Status ↔ PARIVESH extract on one cohort (e.g., coal announced 2015–2020) to measure match rates before committing to the S0 design | 3–4 hrs |
| 5 | First ingestion spike: one CEA installed-capacity Excel + one Grid-India PSP report + one PFC AT&C table → populate S1, S3/S4, S7 for one fiscal year and compute the first real chain | 4–6 hrs |
