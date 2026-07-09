# Phase 6 kickoff — paste this into a new chat

> ⚠️ **Filename note:** this file is named `phase8_prompt.md` per the user's request, but its
> CONTENTS are the **Phase 6 (Practice Evaluation)** continuation. Phases 6 and 7 are NOT built
> yet, so this is genuinely the next work — not Phase 8. Don't be misled by the filename.

Proceed with **Phase 6 (Practice Evaluation)** for the AMD Track 1 agent. The DESIGN is already
locked (via the brainstorming skill in the prior session); your job is to CONFIRM briefly, then BUILD.

## Before starting — sync memory + MCP
0. **Verify codebase-memory MCP tools are actually loaded THIS session** (try `manage_adr(mode='get')`).
   Known gotcha: the server shows `✔ Connected` at the client level but its tools only bind at
   SESSION START — a compacted/continued session (and, in the prior session, even a fresh Claude Code
   launch) did NOT have them. If missing, tell the user; rely on file-memory (it is current + trustworthy).
1. Load file-memory: `MEMORY.md` + `project-amd-track1.md` + `submission-mechanics-amd-track1.md`.
2. If MCP tools ARE loaded: `index_repository` → **immediately** `manage_adr(mode='update')`
   (⚠️ index WIPES the ADR — known gotcha). Bring the ADR current through **Phases 4 + 5** (it is stale ~Phase 1).

## Current state (end of Phase 5, 2026-07-09)
- **Phases 0–5 COMPLETE. 55 tests passing.**
- **Phase 4 (local solvers) DONE + verified:** `app/local_solvers.py` `try_solve(task_type, prompt)->str|None`,
  Option B = `Decimal` math (percentage-remaining, sum, average, product, binary arithmetic) + strict one-sided
  sentiment (declines on contrast words but/however/although/though/yet/nevertheless + negations). NER SKIPPED.
  Wired LIVE into `main.solve()` seam BEFORE the Fireworks call, returns early when non-None.
- **Phase 5 (Docker/CI/GHCR) DONE + smoke-tested:** image `ghcr.io/aliarif2050/amd-track1-agent:latest`
  (repo github.com/aliarif2050/AMD_Hackathon) is PUBLIC + judge-pullable; runs end-to-end, exits 0,
  one result/task; local solvers proven to run INSIDE the container (math→"144", sentiment→"positive").
  CI = `.github/workflows/docker.yml` builds+pushes linux/amd64 on push to main.
  ⚠️ Windows Git-Bash docker mount gotcha: use a Windows-absolute host path + `MSYS_NO_PATHCONV=1`.
- **Dev env:** git-ignored `.venv` (Windows). Run tests: `.venv/Scripts/python.exe -m pytest -q`.

## USER'S CHOSEN SEQUENCE (important)
1. **User submits the CURRENT image to the lablab leaderboard FIRST** (bank a passing score = floor).
   This is a MANUAL user action — do NOT block Phase 6 on it. Offer submission details if asked
   (see `submission-mechanics-amd-track1.md`).
2. **Then build Phase 6 deterministic harness** (this doc) — free, no API, runs today.
3. **Groq / generative testing DEFERRED** until Fireworks credit arrives or genuinely needed.

## Phase 6 goal (PRD §21)
Build a labeled ~80-task practice set → run the agent's DETERMINISTIC layer → score → find weak spots →
tune `router.py` / `prompts.py` / solver guards to harden the **≥16/19 accuracy gate**. Zero API cost.

## LOCKED DECISIONS (do NOT re-litigate — user approved these in the prior brainstorming session)
- **D-1** Submit image first, then deterministic Phase 6 (leaderboard = only representative oracle).
- **D-2** Deterministic-only testing now; Groq/proxy DEFERRED (no Fireworks credit; proxy accuracy ≠ grading).
- **D-3** **Risk-weighted** task distribution (NOT even). Concentrate on gate-risk categories: math + sentiment
  (local solvers must fire AND decline correctly) and reasoning + code (hardest). Fewer on easy factual/general.
- **D-4** **Gold + accepted-variants + normalization** (lowercase, strip trailing punctuation/whitespace).
  NOT single-string exact match — mirrors the meaning-based LLM judge, avoids false failures.
- **D-5** Harness is STANDALONE under `practice/` — NOT in shipped `app/`. Zero image impact.
- **D-6** **Approach A** = layered scorer, NO API, with a deferred generative *seam* (a stub
  `score_generative(task)` returning "deferred") for later — but do NOT wire Groq/Fireworks now (YAGNI).

## Locked eval-set schema (`practice/eval_set.json` — fresh AUTHORED variants, never the hidden tasks)
Each task object:
```json
{
  "task_id": "eval-math-001",
  "prompt": "A shop had 180 apples. It sold 25% in the morning and 30 more later. How many are left?",
  "expected_type": "math",            // gold for router.classify
  "expect_local": true,               // should a local solver FIRE (true) or DECLINE→model (false)?
  "gold": "105",
  "accepted": ["105", "105 apples"],  // normalized variant-match
  "notes": "percentage-remaining chain; solver must fire"
}
```
- `expected_type` → scores the classifier.
- `expect_local` → scores solver targeting: catches BOTH a solver that stays silent when it should fire AND
  (the dangerous one) a solver that FIRES when it should DECLINE.
- `gold`+`accepted` → answer correctness via normalized variant-match, for tasks the solver handles.
- Keep `gold`/`accepted` on `expect_local:false` (model-routed) tasks too, so the deferred generative layer
  can score them LATER — but TODAY mark those "deferred", NOT failed.
- **Non-negotiable:** never the hidden tasks, never hardcoded into `app/`.

## Still OPEN (resolve early with the user, then build)
- Exact per-category counts for the ~80 tasks under the risk-weighted split (propose a table, get a nod).
- Normalization rules edge cases (numbers/units, case, punctuation) — propose defaults.

## Deliverables
- `practice/eval_set.json` — ~80 labeled tasks, risk-weighted, fresh authored variants.
- `practice/evaluate.py` — standalone, no-API scorer: for each task run `router.classify` (vs `expected_type`)
  + `local_solvers.try_solve` (vs `expect_local` + variant-match on gold). Emit a PER-CATEGORY report
  (classification accuracy; solver fire/decline correctness; answer-match) + a list of misses.
  Model-routed tasks → `score_generative()` stub returns "deferred" (NOT failed). Never calls Fireworks.
- Optional: `tests/test_evaluate.py` for the harness's own scoring logic (keep eval OUT of the shipped suite).
- Run it, review misses, and TUNE `router.py` / `prompts.py` / solver guards; re-run to confirm no regression.
- Full existing suite stays green (`.venv/Scripts/python.exe -m pytest -q`). Then STOP + report. Don't auto-start Phase 7.

## Workflow reminders
- One phase at a time, STOP + report at the end. Brainstorm strategic calls first (2–3 options + rec).
- Minimize tokens: targeted reads/edits, no broad scans. Never store secrets. **Never hardcode or cache answers
  or model IDs** (evaluation uses unseen variants — a memorized agent fails them and risks DQ).
- User runs installs/Docker/submission themselves — emit MANUAL SETUP blocks; don't auto-install.
