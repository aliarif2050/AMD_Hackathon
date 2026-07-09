# Phase 4 kickoff — paste this into a new chat

Proceed with **Phase 4 (Local Solvers)** for the AMD Track 1 agent.

## Before starting — sync memory
0. **FIRST verify the codebase-memory tools are actually loaded in THIS session** (e.g. try `manage_adr(mode='get')` or list your codebase-memory tools). The server shows `✔ Connected` at the client level, but MCP tools only load into a session at its start — a compacted/continued session may not have them. If they're missing, tell the user to start a fresh chat (or `/mcp` reconnect); do NOT assume file-memory alone is enough for the graph.
1. Load context: read file-memory `MEMORY.md` + `project-amd-track1.md` + `submission-mechanics-amd-track1.md`, and pull the codebase-memory ADR via `manage_adr(mode='get')`.
2. **The codebase-memory MCP is STALE** (last indexed ~Phase 1). If the tools are loaded, re-index the repo, then **immediately re-run `manage_adr(mode='update')`** to restore the ADR — ⚠️ `index_repository` WIPES the stored ADR (known gotcha). Bring the ADR up to date through Phase 3 + GHCR-done + submission-mechanics. If the tools are NOT loaded, say so and rely on file-memory.

## Current state (as of end of Phase 3, 2026-07-09)
- **Phases 0–3 complete, 47 tests passing.** Pipeline: read tasks → `router.classify` → `router.pick_model` → `fireworks_client.complete` → write results (per-task fallback "Unable to determine.", exit 0).
- Files: `app/{schema,io_utils,config,fireworks_client,router,prompts,main}.py`, `tests/test_{schema,io_utils,config,fireworks_client,router,main}.py`, `practice/tasks.json` (official 8 seeded).
- `main.solve(task, config)` has an **explicit commented Phase-4 seam** for local solvers, placed BEFORE the Fireworks call.
- Docker + **GHCR public image DONE** (judge-pullable). No live Fireworks call yet (credits pending; grading uses organizer key so not blocking). User wants to FINISH building, then push + submit.
- Dev env: git-ignored `.venv` (Windows); run tests with `.venv/Scripts/python.exe -m pytest -q`.

## Phase 4 goal (PRD §14.6, FR-009, Phase 4 in §21)
Zero-token deterministic **local solvers** that answer only OBVIOUS tasks, plugged into the `solve()` seam, running BEFORE any API call. Token-lever #1.

**Golden rule — be CONSERVATIVE.** Accuracy gate needs ≥16/19. A missed save (fall back to API) is cheap; a confident WRONG local answer can cost the gate. Solver returns an answer only when highly confident, else returns `None` → Fireworks fallback. **Never hardcode or cache practice/hidden answers** (evaluation uses unseen variants).

## Required first step: BRAINSTORM before coding (per workflow)
Present 2–3 options for solver scope + confidence gates with pros/cons + a recommendation, then STOP for approval. Cover at least:
- **Math**: simple arithmetic / percentage-remaining patterns via `Decimal`; decline on multi-hop/ambiguous.
- **Sentiment**: only unambiguous positive/negative; decline on mixed/subtle (note practice-03 is deliberately MIXED → must correctly DECLINE and hit the model).
- **NER**: PRD says optional/only-if-reliable → recommend whether to skip in Phase 4 (lean skip — incomplete-entity risk).
- How aggressive overall (math-only vs math+sentiment) and how tight the confidence checks are.

## Deliverables
- `app/local_solvers.py` (`try_solve(task_type, prompt) -> str | None`), wired into the `main.solve()` seam.
- `tests/test_local_solvers.py` covering BOTH answer and decline/None paths + the fallthrough-to-model path.
- Full suite green. Then STOP and report (do not auto-start Phase 5).

## Workflow reminders
- One phase at a time, STOP + report at the end. Brainstorm strategic calls first.
- Minimize tokens: targeted reads/edits, no broad scans. Never store secrets. Never hardcode answers or model IDs.
- User will run installs/Docker themselves — emit MANUAL SETUP blocks if needed; don't auto-install.

## DECISION ALREADY MADE — Option B (user-approved 2026-07-09, prior session)
The brainstorm was already run in a prior (compacted) session and the **user approved Option B**.
Do NOT re-deliberate scope from scratch; you may briefly confirm the plan, then build.

**Option B = math solver + strictly-guarded one-sided sentiment solver; SKIP NER.**
Golden rule = precision ≫ recall: a decline (return `None` → Fireworks) is cheap; a confident
WRONG local answer can cost the ≥16/19 accuracy gate. Return an answer ONLY when highly confident.

- **Math** — exact arithmetic via `Decimal` only. Fire on: explicit arithmetic ("what is 12 × 45",
  "sum of 3, 8, 20") and percentage-of-then-subtract chains (the practice-02 shape:
  "240 items, sells 15%, then 60 more, how many remain" = 240 − 240·0.15 − 60 = 144).
  Decline (`None`) on any leftover/unmodeled clause, ambiguous units, or multi-hop word problems.
- **Sentiment** — answer ONLY on cleanly one-sided text: positive cues with ZERO negative cues
  (or vice-versa), NO contrast conjunctions ("but/however/although/though"), no negation flips.
  ⚠️ practice-03 is deliberately MIXED ("battery great, BUT screen scratches") → MUST decline (`None`)
  → hits the model. This decline is the key test proving the gate is protected.
- **Everything else** (ner, summary, code, reasoning, factual, general) → always `None`.
- **Rationale for skipping NER:** judge grades entity completeness + typing; a regex that misses/mislabels
  one entity ("Fireworks AI" org vs "Berlin" location) = confident-wrong = the exact gate risk. Skip it.

Deliverables unchanged (see above): `app/local_solvers.py` + `tests/test_local_solvers.py`
(answer paths, decline/None paths, AND fallthrough-to-model), full suite green, then STOP + report.
