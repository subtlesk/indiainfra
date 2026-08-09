# CLAUDE.md — India Infrastructure Dashboard

## What This Project Is

An honest, drill-down dashboard of India's infrastructure, starting with electricity. The structural spine is the **chain specification** ([chain-specification-v0.2.md](chain-specification-v0.2.md), v0.1 kept for history): every headline number sits at a stage, every edge between stages has a name, a kind, a decomposition, and its own data source. The UI reads the chain; it does not hard-code it.

Status: **walking skeleton** — FY2023-24 national annual chain, stages S1/S4/S7 + captive bypass populated from parsed primary sources, remaining stages honestly greyed.

Repository map:
- `pipeline/` — Python: archive-first fetchers, parsers for archived primary sources, `build.py` (assembles `site/data/chain.json`, enforces invariants; violation fails CI)
- `data/raw/SRC-n/` — raw archive, one directory per source in the spec's registry; fetched files are stored verbatim before parsing and never deleted
- `data/verified/` — hand-verified figures with provenance, used until a parser replaces them
- `site/` — dependency-free static dashboard; deployed to GitHub Pages by `.github/workflows/build-deploy.yml`
- `docs/kickoffs/` — per-branch kickoff/spec files (first commit of every feature branch, per Branch Workflow below)

Locked decisions (2026-08-09): v1 scope national+annual · fully static site on GitHub Pages, no server · hybrid materialisation (canonical materialised + CI-checked, filtered views derived) · MERIT capture deferred · raw archive moves to a separate data repo when it outgrows this one.

---

## Core Philosophy

**Root-cause first.** Always prefer a root-cause solution over a patch. Do not propose a patch unless the user explicitly asks for one or the blast radius of waiting for a proper fix is unacceptable. If a patch is used, label it clearly in the commit message or code comment and include the root-cause fix immediately after — never leave a patch behind without a follow-up. Think long-term scalability, not short-term convenience.

**Simple solution first.** Complex problems often have simple solutions. Before designing a sophisticated system, ask: can this be solved with a SQL query, a static file, or a conditional? Only reach for complexity when simplicity provably fails.

**Optimize for low cost.** Every architectural decision weighs cost vs performance vs quality. Affordable + good enough beats expensive + perfect. Design for realistic scale from day one, but don't pay for 10× that until you need it.

**Honesty over simplification.** The project exists to correct misleading simplifications (e.g. treating capacity and generation as interchangeable). Never flatten a distinction the data actually carries — if the honest shape is a trunk with side flows, don't draw a line.

---

## Decision Defaults

**Separate concerns at the boundary.**
- Schema/data-model migration + behavioral/wiring change = always separate PRs (different review surface, different rollback unit). Separate sessions too, unless the migration is trivially additive and already merged — then same session, still separate commit/PR.
- "It went smoothly" is when you're most likely to be wrong — the pull to continue right after a clean step is exactly what the boundary guards against.
- A completed, verified unit is a legitimate stopping point, not an unfinished session.

**Specs are ground truth until code exists; then repo + schema are ground truth.** A planning doc is a map into the repo — it can never out-authorise live code. When docs and code disagree, fix the doc drift.

---

## Decision-Making Principles

When designing or building anything in this codebase, reason through these dimensions yourself — don't wait to be told:

- **Scalability:** Will this hold at realistic load? Check query patterns, pagination, cache TTLs, unbounded results.
- **Edge cases:** What breaks at boundaries — missing data, unit mismatches, external source failure, revision of published figures?
- **Cost vs performance:** Is there a cheaper option that's good enough? Prefer it. Upgrade only when data justifies it.
- **Feature tradeoffs:** Does this add complexity to the core path? Is there a simpler solution?
- **Past decisions:** Before overriding a load-bearing inline comment ("don't do X" / "we tried Y"), read the commit that added it (`git log -S '<phrase>' -- <file>`). The constraint is usually still valid, and the rationale often disqualifies the override.

---

## Document Conventions

- When making a change that affects a documented area, update the corresponding document in the same commit or session — don't batch doc updates separately.
- Run `git grep -i "<concept>"` across the repo to find current authority on a topic. Multiple matches usually indicate one canonical source + several references.
- If you find conflicting info across docs, the most recent date or highest version number wins; update the older ones to reference the new canonical.
- If you can't tell which is canonical, STOP and ask. Don't pick silently.

---

## Branch Workflow

**`main` is the canonical line. All work branches off `main` and squash-merges back to `main`.**

- Name work branches `cc/<slug>-<date>` (or `feat/…`, `fix/…`) off the current `main` tip; open a PR back to `main`.
- **Spec-first branch discipline.** Every feature branch's first commit is its spec/kickoff file, committed before any implementation. Post-sign-off corrections fold into that same file. The spec is versioned alongside the code it governs; the branch is self-documenting from commit #1.
- Batched multi-PR releases staged on an integration branch land on `main` with `git merge --no-ff` (preserves per-PR revert granularity); individual PRs still squash-merge.

---

## Session Hygiene

**Parallel sessions/agents must use separate git worktrees.** Never run two Claude/CC/Cursor sessions in the same checkout: branch switches, rebases, and file writes in a shared tree silently clobber each other's uncommitted work. Second session → `git worktree add ../indiainfra-<purpose> <branch>`; tear down with `git worktree remove` when done.

Before ending any work session, run `git status` and `git diff`. Classify each entry; don't carry drift into the next session.

**Untracked files (`??` lines):**
- Commit if: source-of-truth doc, code change, or anything other contexts reference
- Add to `.gitignore` if: build artifact, local-only scratch, session log
- Acceptable as WIP only if: scoped to a current sprint that hasn't shipped yet (commit during that sprint's close, not this session's)

**Modified tracked files (` M` lines):**
- Inspect `git diff <file>` — intentional change?
- Commit if yes; stash or revert if accidental drift from a prior session

**Currently-ignored files (`git status --ignored`):**
- Sample audit periodically — anything here that *should* be tracked? `.gitignore` can be correct at the time but wrong after the project evolves.

**Tooling:**
- `git check-ignore -v <path>` — which `.gitignore` rule matches a given file
- `git ls-files -i --exclude-standard` — tracked files matching ignore patterns (indicates a `.gitignore` change that needs `git rm --cached` follow-up)
- `git status --ignored` — what's currently being ignored

---

## Keeping This Doc Alive

**At the end of every conversation, decide whether CLAUDE.md / README.md / planning docs need an update.** When you ship a non-trivial change — a new module, a shifted architectural rule, a new decision, a dropped pattern — that change has to show up in the docs. Rules of thumb:

- Added a new top-level directory or module → mention it here.
- Made a decision that constrains future work → record it (and why).
- Retired a pattern you replaced → add a "don't do X anymore" note pointing at the replacement.
- Introduced configuration that affects behavior → name it here.

Do this in the same PR as the change. Stale docs actively mislead.
