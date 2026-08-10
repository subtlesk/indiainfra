# indiainfra

**India Electricity Dashboard** — from what gets announced to what gets delivered: every stage, every gap, honestly.

India's electricity system is usually reported as single headline numbers (installed capacity, generation) that hide the chain between them: capacity that was announced but never built, built but not available, available but not dispatched, generated but lost, delivered but never paid for, billed but not received as reliable service. This project models that chain explicitly and publishes it as a citizen-readable dashboard.

## The chain

`S0 pipeline → S1 installed → S2 available → S3 dispatched →(bridge)→ S4 gross generation → S5 net → S6 delivered → S7 billed & collected → S8 service received`, plus side flows (imports/exports, storage), a bypass (captive/rooftop/open access), and the S7→S3 financial feedback loop.

The full model is in **[chain-specification-v0.2.md](chain-specification-v0.2.md)** (v0.1 kept for history).

## Architecture

Fully static, no server:

- **`pipeline/`** — Python. Archive-first fetchers (`fetch.py`: every raw file is stored verbatim before parsing, because this ecosystem's sources demonstrably die), parsers for archived primary sources, and `build.py`, which assembles `site/data/chain.json` and enforces the chain invariants — a violation fails the build.
- **`data/raw/SRC-n/`** — the raw archive, one directory per registered source (see the source registry in the spec). Will move to a separate data repo when it outgrows this one.
- **`data/verified/`** — hand-verified figures with provenance, used until the corresponding parser exists.
- **`site/`** — dependency-free static dashboard, deployed to GitHub Pages by `.github/workflows/build-deploy.yml`.

## Build locally

```
pip install openpyxl pdfplumber
python -m pipeline.fetch   # only needed to (re)populate the raw archive
python -m pipeline.build   # writes site/data/chain.json, runs invariants
```

Then open `site/index.html` via any static server.

## Status

Walking skeleton: FY2023-24, national, annual. Stages S1, S4, S7 and the captive bypass are populated from parsed primary sources; the rest are shown greyed as "not yet populated" — by design, the dashboard shows what isn't measured instead of hiding it.

Plus **the long view**: mode-wise installed capacity, gross generation, sector-wise consumption ("who uses it"), and per-capita consumption, 1947→2024, as line charts parsed from CEA's Growth Book historical tables (with CEA's own non-summing early totals published as residuals rather than hidden). S8 is partially populated (per-capita); light theme is default with a visible dark-mode toggle.
