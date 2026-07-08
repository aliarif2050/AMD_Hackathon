# AMD Developer Hackathon (ACT II) — Track 1 Agent

A general-purpose AI agent packaged as a **Python CLI batch container**. The grading
harness pulls a public `linux/amd64` image, mounts an input file, injects env vars,
runs the container once, and scores the output.

> **Single source of truth:** [`PRD.md`](PRD.md). This README is a quick orientation.

## I/O contract

- **Read** `/input/tasks.json` — an array of `{ "task_id": str, "prompt": str }`.
- **Write** `/output/results.json` — an array of `{ "task_id": str, "answer": str }`,
  one result per task, answers in English, then **exit 0**.
- Per-task failure fallback answer: `"Unable to determine."`

## Runtime environment (injected by the harness)

| Var | Purpose |
|-----|---------|
| `FIREWORKS_API_KEY` | Fireworks auth. Secret. |
| `FIREWORKS_BASE_URL` | OpenAI-compatible endpoint; **all** model calls go through it. |
| `ALLOWED_MODELS` | Comma-separated allowed model IDs. Read at runtime; never hardcoded. |

**Hard rules:** never hardcode API keys or model IDs, never bundle a `.env`, always
read config from the environment.

## Scoring (why token discipline matters)

1. **Accuracy gate** — a binary LLM-judge threshold. Miss it → excluded.
2. **Token rank** — among passers, ranked ascending by total Fireworks tokens.
   Work solved by deterministic local code costs **zero** tokens.

Grading VM: CPU-only, 4 GB RAM / 2 vCPU, ≤10 GB image, ≤10 min total, <60 s startup,
<30 s/request. (The AMD GPU pod is for dev/fine-tuning only — it does not run the submission.)

## Repository layout

```
app/         # application package (built out in Phases 1–4)
tests/       # pytest suite
input/       # sample tasks.json for local runs
output/      # results.json is written here (git-ignored)
practice/    # local practice set + evaluation notes (Day 2)
PRD.md       # full product/requirements doc — source of truth
```

## Local development

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env        # fill in your Fireworks values
pytest                      # run the test suite
```

Docker build/run and CI-to-GHCR arrive in Phase 5 (see PRD §15–16).

## Status

**Phase 0 complete** — repository scaffolding in place. Application logic begins in
Phase 1 (batch skeleton). See PRD §21 for the phased roadmap.
