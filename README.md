# AMD Developer Hackathon (ACT II) — Track 1 Agent

A general-purpose AI agent packaged as a **Python CLI batch container**. The grading
harness pulls a public `linux/amd64` image, mounts an input file, injects env vars,
runs the container once, and scores the output.

> **Single source of truth:** [`PRD.md`](PRD.md). This README is a quick orientation.

## I/O contract

- **Read** `/input/tasks.json` — an array of `{ "task_id": str, "prompt": str }`.
- **Write** `/output/results.json` — an array of `{ "task_id": str, "answer": str }`,
  one result per task, answers in English, then **exit 0**.
- Per-task failure fallback answer: `"Unable to determine."` — one bad task never
  sinks the batch.

## Runtime environment (injected by the harness)

| Var | Purpose |
|-----|---------|
| `FIREWORKS_API_KEY` | Fireworks auth. Secret. |
| `FIREWORKS_BASE_URL` | OpenAI-compatible endpoint; **all** model calls go through it. |
| `ALLOWED_MODELS` | Comma-separated allowed model IDs. Read at runtime; never hardcoded. |
| `FIREWORKS_TIMEOUT` | *(optional)* per-request timeout override; defaults to 25 s. |

**Hard rules:** never hardcode API keys or model IDs, never bundle a `.env`, always
read config from the environment, and never return a model absent from `ALLOWED_MODELS`.

## Scoring (why token discipline matters)

1. **Accuracy gate** — a binary LLM-judge threshold. Miss it → excluded.
2. **Token rank** — among passers, ranked ascending by total Fireworks tokens.
   Work solved by deterministic local code costs **zero** tokens.

Grading VM: CPU-only, 4 GB RAM / 2 vCPU, ≤10 GB image, ≤10 min total, <60 s startup,
<30 s/request. (The AMD GPU pod is for dev/fine-tuning only — it does not run the submission.)

## How it works

Each task flows through a single deterministic pipeline (`app/main.py` → `solve`):

```
prompt
  └─ router.classify()      # zero-token keyword/heuristic classifier → 1 of 8 task types
       └─ local_solvers.try_solve()   # deterministic answer if the shape is unambiguous → 0 tokens
            └─ (declines) router.pick_model()   # best model present in ALLOWED_MODELS
                 └─ fireworks_client.complete()  # single call, temp 0, no streaming, 404 model-fallback
```

Token levers applied, in priority order:

1. **Deterministic local solvers** (`app/local_solvers.py`) — precision-first math
   (sum / average / product / percentage-remaining / binary arithmetic) and clear-cut
   sentiment answered with **zero tokens**; ambiguous cases defer to the model.
2. **Short, task-specific system prompts** (`app/prompts.py`) that steer concise English
   output, plus **per-category output-token ceilings**.
3. **One call per task**, `temperature=0`, no chain-of-thought, no runaway retries — the
   only retry is a model fallback when an allowed model returns 404 (not deployed).
4. **Concise-correct model per task type** (`app/router.py`), always filtered against the
   runtime `ALLOWED_MODELS`. Optional launch-day override via `MODEL_OVERRIDE_<TASKTYPE>`.

Supported task types: `math`, `sentiment`, `ner`, `summary`, `code`, `reasoning`,
`factual`, `general`.

## Repository layout

```
app/
  main.py              # batch entrypoint: read → solve each task → write → exit 0
  config.py            # runtime Config loaded from injected env vars
  schema.py            # pydantic Task / Result models (the I/O contract)
  io_utils.py          # read tasks / write results, /input & /output paths
  router.py            # classify() + pick_model() (deterministic, zero-token)
  local_solvers.py     # zero-token math & sentiment solvers
  prompts.py           # short system prompts + per-category output-token caps
  fireworks_client.py  # OpenAI-compatible Fireworks wrapper (temp 0, 404 fallback)
tests/                 # pytest suite (67 passing)
input/                 # sample tasks.json for local runs
output/                # results.json is written here (git-ignored)
practice/              # local practice set + evaluate.py harness + eval notes
PRD.md                 # full product/requirements doc — source of truth
Dockerfile             # graded image — installs requirements-image.txt ONLY
```

## Dependencies (three isolated files)

| File | Used by | Contents |
|------|---------|----------|
| `requirements-image.txt` | **The graded Docker image only** | pinned `openai` + `pydantic` — nothing else |
| `requirements-dev.txt` | Local tests | `-r requirements-image.txt` + `pytest` + `python-dotenv` |
| `requirements.txt` | Streamlit Cloud demo only | `-r requirements-image.txt` + `streamlit` + `python-dotenv` |

> ⛔ **The graded image must install ONLY `requirements-image.txt`.** Adding demo/UI/dev
> deps (streamlit, pandas, …) to the image once broke the `openai` runtime via transitive
> deps, causing every model call to fall back to `"Unable to determine."` → a **0% submission**
> that still built green and exited 0. See [`AGENTS.md`](AGENTS.md) for the full post-mortem
> and the pre-submit guard.

## Local development

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env        # fill in your Fireworks values (never commit .env)
pytest                      # run the test suite (67 passing)
```

Offline accuracy check against the local practice set:

```bash
python -m practice.evaluate   # writes practice/eval_report.json
```

## Docker (graded submission)

```bash
docker build -t amd-track1-agent .
docker run --rm -e FIREWORKS_API_KEY -e FIREWORKS_BASE_URL -e ALLOWED_MODELS \
  -v "$PWD/input:/input" -v "$PWD/output:/output" amd-track1-agent

# Pre-submit guard — MUST pass (no streamlit in image, openai imports cleanly):
docker run --rm amd-track1-agent python -c \
  "import importlib.util as u; assert u.find_spec('streamlit') is None; \
   from openai import OpenAI; print('image clean')"
```

## Demo UI

An optional Streamlit demo (**AstraRoute**, `streamlit_app.py`) visualizes the routing /
solver pipeline. It is deployed via Streamlit Community Cloud (which reads `requirements.txt`)
and is **completely separate from the graded image** — it must never be added to the container.

## Status

Core agent complete and green: full classify → local-solve → route → Fireworks pipeline,
deterministic zero-token math/sentiment solvers, per-category token caps, dependency
isolation, Dockerfile, and **67 passing tests**. Remaining stretch items (fine-tuned
router, local generative model) are optional per PRD §21.
