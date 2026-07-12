# AGENTS.md — AMD Hackathon Track 1 Agent

Guidance for Codex working in this repo. **`PRD.md` is the single source of truth;**
this file is the short operational summary. Read only the PRD sections you need.

## What this is

A general-purpose AI agent shipped as a **Python CLI batch container** (NOT a web app/server).
The judge pulls a public `linux/amd64` image, mounts input, injects env, runs it once, scores output.

## I/O contract (do not break)

- Read `/input/tasks.json`: array of `{task_id, prompt}`.
- Write `/output/results.json`: array of `{task_id, answer}` — one per task, English, then **exit 0**.
- Per-task failure fallback answer: `"Unable to determine."`

## Runtime env (harness-injected — read at runtime, never hardcode)

- `FIREWORKS_API_KEY`, `FIREWORKS_BASE_URL`, `ALLOWED_MODELS`.
- All Fireworks calls go through `FIREWORKS_BASE_URL`. Never hardcode keys/model IDs.
  Never commit a `.env` or bundle it into the image. Always filter chosen models against
  the runtime `ALLOWED_MODELS` — never return an unlisted model.

## Scoring model (drives every decision)

1. Accuracy gate (binary LLM-judge) — miss it → excluded.
2. Token rank — ascending total Fireworks tokens among passers. Local-solver work = 0 tokens.

Token levers, in priority order: (1) deterministic solvers, (2) short prompts + concise
output, (3) single call / temp 0 / no CoT / no runaway retries, (4) concise-correct model
per category, (5) *stretch* fine-tuned router, (6) *stretch* local generative model.

## Constraints

CPU-only grading VM: 4 GB RAM / 2 vCPU, `linux/amd64`, ≤10 GB image, ≤10 min total,
<60 s startup, <30 s/request, 10 submissions/hr/team. **Deadline: 18:00 CET, 11 Jul 2026.**

## Stack (keep minimal)

Python CLI batch only. Runtime deps: `openai`, `pydantic`. Dev: `pytest`, `python-dotenv`.
No FastAPI/Flask/Streamlit/LangChain/torch/transformers in the MVP.

## ⛔ IMAGE DEPENDENCY ISOLATION (hard rule — caused a 0% submission)

**The graded image MUST install ONLY `requirements-image.txt` (pinned `openai` + `pydantic`).
NEVER add demo/UI/dev deps (streamlit, pandas, dotenv, pytest, …) to the image.**

- `requirements-image.txt` → graded image ONLY (Dockerfile installs THIS). Pinned versions = the
  ones the passing test suite validates, so image runtime == tested runtime.
- `requirements.txt` → Streamlit-Cloud **demo** only (`-r requirements-image.txt` + streamlit + dotenv).
  Streamlit Cloud auto-reads this file; the image must NOT.
- `requirements-dev.txt` → local tests (`-r requirements-image.txt` + pytest).
- **Why:** the AstraRoute demo merge put `streamlit>=1.35` in `requirements.txt`; the Dockerfile
  installed it into the image; streamlit's transitive deps broke the `openai` runtime → every model
  call threw → every task fell back to `"Unable to determine."` → **`ACCURACY_GATE_FAILED`, 0/19 (0.0%)**.
  The image still built green and exited 0 — a silent runtime break, invisible to local tests (dev venv
  had no streamlit). Most of the 16/19 came from the MODEL path, so breaking it collapses the score.
- **Guard before every submission:** `docker run --rm <img> python -c "import importlib.util as u; assert u.find_spec('streamlit') is None; from openai import OpenAI"` must pass.

## Layout

`app/` (main, schema, io_utils, config, router, local_solvers, prompts, fireworks_client, errors),
`tests/`, `input/`, `output/` (generated), `practice/`. Full map: PRD §13.3.

## Commands

```bash
pip install -r requirements-dev.txt   # tests: -r requirements-image.txt + pytest
pytest
# Docker (Phase 5+) — Dockerfile installs requirements-image.txt (openai+pydantic ONLY):
# docker build -t amd-track1-agent .
# docker run --rm -e FIREWORKS_API_KEY -e FIREWORKS_BASE_URL -e ALLOWED_MODELS \
#   -v "$PWD/input:/input" -v "$PWD/output:/output" amd-track1-agent
# Pre-submit guard (must pass — no streamlit in image, openai imports):
# docker run --rm amd-track1-agent python -c "import importlib.util as u; \
#   assert u.find_spec('streamlit') is None; from openai import OpenAI; print('image clean')"
```

## How we work (see PRD §24 + Prompt.txt)

- Build in **strict phases 0–9**. Do ONE phase, run its tests, then **STOP and report**.
  Do not jump ahead without explicit approval.
- For decisions touching architecture, scoring, Docker reliability, tokens, model routing,
  dependencies, or error policy: **brainstorm 2–3 options** (pros/cons + recommendation)
  before implementing. Obvious low-risk calls: proceed and note them.
- When a step needs the user's machine/accounts/credentials, STOP and emit a
  **MANUAL SETUP REQUIRED** block (what / why / steps / how to verify).
- Minimize tokens: targeted reads, small focused edits, no broad scans or file re-dumps.
- Never store secrets in code/memory. Never hardcode or cache answers or model IDs.

## Status

**Phase 0 (repository setup) complete.** Next: Phase 1 — batch skeleton (schema, IO,
dummy answers, local Docker run). Application `app/*.py` modules do not exist yet.
