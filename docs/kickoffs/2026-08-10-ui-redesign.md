# Kickoff: citizen-first UI redesign

**Branch:** `cc/ui-redesign-2026-08-10` · **Date:** 2026-08-10 · **Requested by:** user ("overall feel is complex… UI needs to be new age instead of typical too-technical dashboard; imagine a new-age SaaS platform")

## Problem

The walking-skeleton UI is honest but reads like an engineer's audit: stage IDs, source codes, parser notes, and grades sit at the same visual level as the story. Correctness must not cost comprehension.

## Direction

**Editorial new-age SaaS** — a scroll story, not a control panel.

- **Hierarchy inversion:** plain language first, numbers second, provenance third. Every stage leads with its citizen sentence ("Not everything announced gets built…"); IDs/grades/sources move into a per-card "details" disclosure. Nothing is deleted — it is re-layered.
- **Story structure:** hero question → headline stat tiles → "follow the electricity" chain cards → the one big lesson (MW vs units, 33%/13% divergence) → the long view charts → method footer.
- **Pending stages shrink**: compact "not yet measured" chips inline in the flow, not full grey boxes that dominate the page. Honesty stays visible, stops shouting.
- **Type:** Fraunces (display serif, warm/characterful) + Instrument Sans (body), **self-hosted woff2** — no CDN dependency, per the project's longevity ethos.
- **Look:** warm paper light theme / deep charcoal dark theme, saffron accent, soft gradient glows + grain in the hero, rounded cards, generous whitespace.
- **Motion:** one staggered load reveal; an animated "current" flowing down the chain connectors (the memorable thing). `prefers-reduced-motion` respected.
- **Charts keep the validated dataviz palette and chrome contract** — only fonts/surfaces restyle. No change to pipeline or data files.

## Out of scope

Data/pipeline changes; new chart types; mobile-app shell. Chain semantics unchanged — the UI still reads the chain, never hard-codes it.
