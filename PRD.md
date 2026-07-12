# Product Requirements Document (PRD)

# AMD Developer Hackathon — Track 1 General-Purpose AI Agent

**Document status:** Final implementation-ready PRD  
**Document type:** Industrial Product Requirements + Technical Execution Specification  
**Track:** Track 1 — General-Purpose AI Agent  
**Project codename:** `amd-track1-agent`  
**Primary team:** Chintu + Brother  
**Target submission artifact:** Public `linux/amd64` Docker image  
**Primary runtime:** Python CLI batch-processing container  
**Last updated:** 2026-07-09 (reconciled with official Participant Guide, ACT II)  

---

## 0. Reconciliation With Official Participant Guide (ACT II)

This PRD has been reconciled against the official **AMD Developer Hackathon Participant Submission Guide (ACT II), Track 1**. Where this document previously diverged from the official guide, **the guide wins**. This section records the authoritative facts and the reconciliation Decision Log.

### 0.1 Authoritative Facts From the Official Guide

- Submission artifact: a Docker image on a **public registry** — GitHub Container Registry **or Docker Hub** are both acceptable.
- Input `/input/tasks.json`: array of `{task_id, prompt}`. Output `/output/results.json`: array of `{task_id, answer}`.
- Env vars injected by the harness at runtime: `FIREWORKS_API_KEY`, `FIREWORKS_BASE_URL`, `ALLOWED_MODELS` (comma-separated exact model IDs). **For Track 1 the list is confirmed** (§10.1: `minimax-m3, kimi-k2p7-code, gemma-4-31b-it, gemma-4-26b-a4b-it, gemma-4-31b-it-nvfp4`) — but the agent must still read it from the env var at runtime and never hardcode/force a model ID.
- All Fireworks calls **must** go through `FIREWORKS_BASE_URL`; calls that bypass it are **not recorded** and score **zero tokens** for that call.
- **Local model inference inside the container is explicitly permitted and encouraged.** Local models and locally-used tokens **count as zero toward the token score** but **do count toward accuracy**. A `ZERO_API_CALLS` marker (a local-only agent) is **not** a failure — it is a valid, potentially winning strategy.
- Grading VM: **4 GB RAM, 2 vCPU**, `linux/amd64`. If bundling a local model: **2B–3B 4-bit quantized is safe; 7B 4-bit fills the entire RAM budget**, leaving no room for agent code.
- Rules: exit `0` on success / non-zero on failure; **max runtime 10 minutes**; only `ALLOWED_MODELS` may be called (others invalidate the submission); malformed `results.json` scores zero; image compressed size **≤ 10 GB**; **submissions rate-limited to 10 per hour per team**.
- General (all tracks): container ready **within 60 s**; per-request response **< 30 s**; all responses **in English**; no hardcoded/cached answers (evaluation uses unseen variants).
- Scoring: (1) **Accuracy gate** — an LLM-Judge scores each answer against expected intent; below threshold → excluded from the leaderboard. (2) **Token efficiency** — passing submissions are ranked **ascending by total tokens** recorded by the judging proxy. Fewer tokens = higher rank.
- Token-counting nuance: task prompts are identical for every team; only **your system prompt** (verbosity/formatting) and **your model's response length** affect your token count. Guide advice: **get routing and local-model choice right first; tune output length later.**

### 0.2 Decision Log (reconciliation)

| # | Decision | Options considered | Chosen | Rationale |
|---|---|---|---|---|
| D-01 | Local-model strategy | (A) API-only + deterministic solvers; (B) fine-tuned local **router** + deterministic solvers, API solves hard tasks; (C) local-first generative solving (`ZERO_API_CALLS`) | **B — staged on top of A (team-approved 2026-07-08)** | The AMD GPU pod is **dev/fine-tuning only** — grading still runs CPU-only (4 GB/2 vCPU), so a bundled *generative* solver stays latency-risky. But a **fine-tuned router** (official "Fine-Tune a Query Router" tutorial) runs cheaply on CPU (classification, not generation), costs zero tokens, and is the officially-encouraged lever. Plan: ship A first (guaranteed submission), then add a learned router while keeping API for the hard categories to bank the gate. A small local *generative* model for easy categories is a stretch goal gated on CPU-latency evidence. Reject C (gate-exclusion + `TIMEOUT` risk on a 3-day clock). |
| D-02 | Routing / model selection | (A) capability heuristic only; (B) explicit preference tuned to confirmed models; (C) explicit preference **first**, heuristic **fallback** | **C** | The Track 1 models are confirmed (§10.1), so lead with an explicit ranking tuned to them for best per-category accuracy, but keep the capability heuristic as a fallback so a renamed/reordered launch-day list still routes sanely. Always filtered against runtime `ALLOWED_MODELS`; never hardcode/force a model. |
| D-03 | Edit scope for this reconciliation | (A) correct + strategically revise; (B) surgical fact-correction only | **A** | Produces a coherent, launch-ready PRD rather than a patchwork with residual internal tension. |

> **On D-01 (APPROVED by team, 2026-07-08):** grading is CPU-only (the ~48 GB AMD GPU is a *development* pod, not the grading VM), and the submission deadline is **18:00 CET, 11 Jul 2026** (~3 days). Sequence accordingly: A (guaranteed submission) → fine-tuned router (Phase 7a) → optional local generative tier for easy categories (Phase 7b, evidence-gated). All-local (C) is rejected. The time-boxed execution plan is §21.0.

### 0.3 Development Environment & Official Guidance (from the FAQ)

- **The AMD GPU pod is for development/fine-tuning only.** Teams get a Jupyter cloud instance (~48 GB GPU, 25 GB persistent store at `/workspace`, time-boxed *N-hours-per-24h* compute) via `https://notebooks.amd.com/hackathon`. **This is NOT the grading environment** — the judge pulls the Docker image and runs it on the **CPU-only 4 GB / 2 vCPU `linux/amd64` VM** (FAQ Q21: no live endpoint is maintained for judging). Any bundled model therefore runs on **CPU** at grade time.
- **Officially-encouraged strategy = a smart router, ideally fine-tuned** (the "Fine-Tune a Query Router" tutorial). FAQ, on the zero-token rule: *"run as many local models as you need, including the smart router, so you make as few external Fireworks calls as possible."* A router only *classifies* (cheap on CPU), so it is far lower-risk than bundling a generative solver.
- **Submission deadline: 18:00 CET, 11 July 2026.** Tracks 1 & 2 have live leaderboards. This tight clock prioritizes a reliable A-baseline before any optimization.
- Fireworks model families in play (FAQ Q11): **MiniMax** (M3 — coding/agentic frontier, 1M context) and **Kimi K** (Moonshot, MoE, agentic/coding). Confirmed `ALLOWED_MODELS` in §10.1.
- **Open question (token accounting):** the guide ranks by *"total tokens recorded by the proxy,"* but the router tutorial says *"cheapest model that can handle it."* It is unconfirmed whether tokens are **model-weighted** (then which Fireworks model matters) or a **flat count** (then only *local-vs-API* and *output length* matter). Design the router to prefer, in order: **local solve → fewest-token Fireworks path that clears the gate.**

---

## 1. Executive Summary

The product is a Dockerized general-purpose AI batch agent for AMD Developer Hackathon Track 1. The judging harness will execute the submitted container against hidden tasks. The agent must read a JSON task list from `/input/tasks.json`, solve each natural-language task, write a valid JSON results file to `/output/results.json`, and exit successfully.

This is not a chatbot, web application, API server, Streamlit demo, or frontend product. It is an evaluation-facing command-line container whose success depends on three dimensions:

1. **Submission reliability** — the image must pull, run, read input, write valid output, and exit correctly.
2. **Answer quality** — the agent must pass the accuracy gate across all eight capability categories.
3. **Token efficiency** — after passing the accuracy gate, the agent should reduce recorded Fireworks token usage through routing, short prompts, local deterministic solvers, and concise output.

The core product strategy is:

```text
Make it run → Make it correct → Make it efficient
```

This single document is the source of truth for both product requirements and implementation guidance. It replaces the need to separately use a PRD and a master build guide.

---

## 2. Context and Problem Definition

### 2.1 Hackathon Context

Track 1 asks teams to build an AI agent that can handle a wide range of natural-language tasks while using Fireworks AI models efficiently. The challenge simulates an enterprise model-routing problem: not every task needs the same model, and unnecessary premium model usage increases cost.

The agent must therefore behave like a production-grade AI router:

- Understand the task type.
- Solve simple tasks locally where safe.
- Route harder tasks to the most appropriate allowed Fireworks model.
- Avoid unsupported or disallowed model calls.
- Produce concise, accurate answers.
- Never hardcode hidden-task answers.
- Never rely on practice prompts being repeated.

### 2.2 Product Problem

The judging environment is strict. A high-quality answer engine can still fail if the container:

- Cannot be pulled.
- Does not support `linux/amd64`.
- Crashes at runtime.
- Does not write `/output/results.json`.
- Writes malformed JSON.
- Uses a model outside `ALLOWED_MODELS`.
- Bypasses `FIREWORKS_BASE_URL`.
- Runs too long.
- Includes unnecessary heavy dependencies.

Therefore, this project must be treated as a **production batch inference system**, not a quick prototype.

### 2.3 Product Thesis

The winning version will likely not be the fanciest agent. It will be the one that combines:

- Correct Docker packaging.
- Strict input/output compliance.
- Safe model routing.
- Strong enough accuracy.
- Low unnecessary token usage.
- Robust behavior on unseen prompts.

---

## 3. Goals, Non-Goals, and Success Metrics

### 3.1 Primary Goals

| ID | Goal | Description | Priority |
|---|---|---|---|
| G-001 | Valid Docker submission | Publish a public Docker image that the judge can pull and run | P0 |
| G-002 | Correct input handling | Read `/input/tasks.json` exactly as mounted by the harness | P0 |
| G-003 | Correct output handling | Write `/output/results.json` with valid schema before exit | P0 |
| G-004 | Runtime env compliance | Use only injected `FIREWORKS_API_KEY`, `FIREWORKS_BASE_URL`, and `ALLOWED_MODELS` | P0 |
| G-005 | Model compliance | Never call models outside runtime `ALLOWED_MODELS` | P0 |
| G-006 | Accuracy gate | Produce answers good enough to pass LLM-judge quality threshold | P0 |
| G-007 | Token efficiency | Reduce Fireworks tokens after accuracy is stable | P1 |
| G-008 | Hidden-prompt robustness | Generalize beyond practice tasks and sample prompts | P0 |
| G-009 | Team maintainability | Keep code understandable for both team members | P1 |

### 3.2 Non-Goals

The product must not include:

| ID | Non-Goal | Reason |
|---|---|---|
| NG-001 | Web UI | The judge runs a container, not a website |
| NG-002 | FastAPI/Flask/Express server | No long-running server required |
| NG-003 | Streamlit dashboard | Irrelevant to Track 1 submission |
| NG-004 | Database | Hidden tasks are read from JSON; no persistence needed |
| NG-005 | Browser automation | Not part of Track 1 |
| NG-006 | User auth | No user-facing app |
| NG-007 | Bundled local LLM **in the MVP** (deferred, not banned) | Local model inference is permitted and encouraged by the guide, but 4GB RAM / 2 vCPU / 60s startup / ≤10GB image make it risky under time pressure. Ship the API-only MVP first, then pursue a 2B–3B 4-bit local tier as a token-score optimization (see §10.5, Phase 7b) |
| NG-008 | LangChain/LlamaIndex by default | Adds complexity and image bloat without clear benefit |
| NG-009 | Hardcoded sample answers | Violates generalization requirement |
| NG-010 | Bundled `.env` | Secrets must come from runtime env |

### 3.3 Success Metrics

#### P0 Submission Metrics

| Metric | Target |
|---|---:|
| Docker image pulls publicly | 100% |
| Image platform | `linux/amd64` |
| Container startup | Under 60 seconds |
| Total runtime | Under 10 minutes |
| Output JSON validity | 100% |
| Output object schema | `{task_id, answer}` for every task |
| Model calls outside `ALLOWED_MODELS` | 0 |
| Hardcoded API keys | 0 |

#### P1 Competitive Metrics

| Metric | Target |
|---|---:|
| Practice-set category coverage | All 8 categories |
| Fireworks calls for obvious math/sentiment | Reduced where safe |
| Average answer verbosity | Concise, task-appropriate |
| Retried model calls | Minimal |
| Long system prompts | Avoided |

---

## 4. Stakeholders and Responsibilities

### 4.1 External Stakeholder

| Stakeholder | Role | Product Expectation |
|---|---|---|
| Hackathon judging harness | Primary evaluator | Pulls image, injects env vars, mounts input/output, runs container, scores output |

### 4.2 Internal Team

| Person | Primary Role | Responsibilities |
|---|---|---|
| Chintu | Agent owner | Task routing, prompting, answer quality, local solvers, model strategy, practice evaluation |
| Brother | Platform owner | Docker, GitHub Actions, GHCR, public image, `linux/amd64`, local run validation, final submission checks |

### 4.3 RACI Matrix

| Workstream | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Product requirements | Chintu | Chintu | Brother | Both |
| Python batch skeleton | Chintu | Chintu | Brother | Both |
| Fireworks integration | Chintu | Chintu | Brother | Both |
| Dockerfile | Brother | Brother | Chintu | Both |
| GitHub Actions/GHCR | Brother | Brother | Chintu | Both |
| Router/model strategy | Chintu | Chintu | Brother | Both |
| Tests | Both | Chintu | Brother | Both |
| Final submission | Brother | Both | Chintu | Both |

---

## 5. Scope

### 5.1 In Scope

The final repository must include:

- Python CLI batch application.
- Strict input/output JSON contracts.
- Runtime environment variable loader.
- Fireworks client configured through injected env vars.
- Runtime allowed-model parser.
- Model-selection layer.
- Prompt classifier/router.
- Conservative local solvers.
- Short task-specific prompt templates.
- Dockerfile.
- `.dockerignore`.
- `.gitignore`.
- GitHub Actions workflow for `linux/amd64` image publishing.
- README.
- Tests.
- Practice input examples.
- Final submission checklist.

### 5.2 Out of Scope for MVP

- Local quantized LLMs **in the MVP** (deferred to a post-MVP token-optimization phase — permitted and encouraged by the guide; see §10.5 and Phase 7b).
- RAG/vector search.
- Persistent logs in output.
- Full telemetry stack.
- Model fine-tuning.
- Multi-agent orchestration frameworks.
- Large dependencies such as `torch`, `transformers`, or `opencv` unless a later strategic reason appears.

---

## 6. Track 1 Capability Requirements

The agent must be capable across eight task categories.

| Category ID | Category | Expected Input Style | Expected Output Style | Initial Strategy |
|---|---|---|---|---|
| C1 | Factual knowledge | Definitions, concepts, “what/how/why” prompts | Direct concise answer | Fireworks model |
| C2 | Mathematical reasoning | Arithmetic, percentages, projections, word problems | Final answer, short reasoning if needed | Local solver first for simple patterns; model fallback |
| C3 | Sentiment classification | Reviews or statements asking sentiment | Label + short reason | Local rules for obvious cases; model fallback |
| C4 | Text summarization | Passage + length/format constraint | Follow requested format exactly | Fireworks with strict concise prompt |
| C5 | Named entity recognition | Extract entities from sentence/passage | Entity/type pairs | Model fallback; local only if confident |
| C6 | Code debugging | Buggy code + requested fix | Corrected code or concise bug explanation | Code model |
| C7 | Logical/deductive reasoning | Constraint puzzles | Final answer + brief justification | Reasoning model |
| C8 | Code generation | Function/spec request | Correct code | Code model |

---

## 7. Input Contract

### 7.1 Input Path

The application must read:

```text
/input/tasks.json
```

### 7.2 Input Shape

```json
[
  {
    "task_id": "t1",
    "prompt": "Summarise the following text in one sentence: ..."
  },
  {
    "task_id": "t2",
    "prompt": "..."
  }
]
```

### 7.3 Input Field Specification

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `task_id` | string | Yes | Non-empty | Unique identifier to preserve in output |
| `prompt` | string | Yes | Non-empty | Natural-language task instruction |

### 7.4 Input Validation Rules

The app must validate:

- File exists at `/input/tasks.json`.
- File is valid UTF-8 JSON.
- Root object is a list.
- Every item is an object.
- Every item has `task_id` and `prompt`.
- `task_id` and `prompt` are non-empty strings.

### 7.5 Input Failure Behavior

| Failure | Required Behavior |
|---|---|
| Missing input file | Log clear error to stderr; exit non-zero |
| Malformed JSON | Log clear error to stderr; exit non-zero |
| Invalid task schema | Log clear error to stderr; exit non-zero |
| Empty list | Write empty results array and exit 0, unless hackathon clarifies otherwise |

---

## 8. Output Contract

### 8.1 Output Path

The application must write:

```text
/output/results.json
```

### 8.2 Output Shape

```json
[
  {
    "task_id": "t1",
    "answer": "..."
  },
  {
    "task_id": "t2",
    "answer": "..."
  }
]
```

### 8.3 Output Field Specification

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `task_id` | string | Yes | Must match input task ID | Preserves task identity |
| `answer` | string | Yes | Non-empty preferred | Final answer in English |

### 8.4 Output Rules

- Always create `/output` directory if missing.
- Always write `/output/results.json` on successful run.
- JSON must be valid.
- Root must be an array.
- Every input task must have exactly one output result.
- Preserve input order unless there is a strong reason not to.
- Avoid extra fields to minimize schema risk.
- Answers must be in English.
- Answers should be concise unless the prompt requests detail.

### 8.5 Per-Task Failure Policy

If a single task fails during processing, the application should not crash the entire batch. Return:

```json
{
  "task_id": "original-task-id",
  "answer": "Unable to determine."
}
```

This fallback should be rare. Use it to protect the full run from one task-level failure.

---

## 9. Runtime Environment Contract

### 9.1 Required Environment Variables

| Variable | Required | Source | Usage |
|---|---:|---|---|
| `FIREWORKS_API_KEY` | Yes | Hackathon harness | API authentication |
| `FIREWORKS_BASE_URL` | Yes | Hackathon harness | Base URL for all Fireworks calls |
| `ALLOWED_MODELS` | Yes | Hackathon harness | Comma-separated allowed model IDs |

### 9.2 Runtime Rules

The submitted container must:

- Read all three variables from the environment.
- Never use a personal Fireworks key in submitted runtime.
- Never bundle `.env` in the Docker image.
- Route all Fireworks calls through `FIREWORKS_BASE_URL`.
- Select only models found in runtime `ALLOWED_MODELS`.
- Fail clearly if model calls are needed but required env vars are unavailable.

### 9.3 Local Development Env Example

For local testing only:

```bash
export FIREWORKS_API_KEY="your_local_key"
export FIREWORKS_BASE_URL="https://api.fireworks.ai/inference/v1"
export ALLOWED_MODELS="minimax-m3,kimi-k2p7-code,gemma-4-31b-it,gemma-4-26b-a4b-it,gemma-4-31b-it-nvfp4"
```

`.env` may be used locally but must be excluded from Git and Docker.

---

## 10. Allowed Models and Model Strategy

### 10.1 Allowed Models (confirmed for Track 1)

The Track 1 `ALLOWED_MODELS` list is **confirmed**:

```text
minimax-m3
kimi-k2p7-code
gemma-4-31b-it
gemma-4-26b-a4b-it
gemma-4-31b-it-nvfp4
```

These are **remote Fireworks model IDs**, not models to download into the Docker image.

**Compliance rule (still binding):** per the official guide, the agent must **read `ALLOWED_MODELS` from the environment at runtime and never hardcode or force a model ID.** The confirmed list above is used only to *tune the preference ranking* (§10.4); the picker always filters its choice against the runtime `ALLOWED_MODELS` value and never returns a model absent from it. A **capability heuristic** (§10.3) remains as a fallback in case the launch-day list is renamed or reordered.

### 10.2 Runtime Model Flow

```text
Container
  ↓
OpenAI-compatible client
  ↓
FIREWORKS_BASE_URL
  ↓
Selected model from ALLOWED_MODELS
  ↓
Model answer
  ↓
/output/results.json
```

### 10.3 Model Picker Requirements

The models are confirmed (§10.1), so the picker leads with an **explicit preference ranking tuned to those models**, then falls back to a **capability heuristic** for robustness if the launch-day list differs.

The model picker must, in order:

1. Read the parsed runtime `ALLOWED_MODELS` list (raise a clear error if empty and a model call is required).
2. Honor an **optional override** (`MODEL_OVERRIDE_<TASKTYPE>=<model_id>`) if set and present in `ALLOWED_MODELS`.
3. Return the first model from the task type's **explicit preference list** (§10.4) that is present in `ALLOWED_MODELS`.
4. If none match, use the **capability heuristic** — infer tags from each ID string (`code`/`coder`/`kimi` → code; `instruct`/`-it`/`chat`/`gemma`/`minimax` → general-instruct; a parameter-size digit ≥ 30 → large) — to pick the best available model.
5. Fall back to the first runtime allowed model if no signal matches.

The picker must **never** return a model absent from runtime `ALLOWED_MODELS`.

### 10.4 Preference Matrix (confirmed models)

Explicit ranking tuned to the confirmed Track 1 models. The picker filters these against runtime `ALLOWED_MODELS` and falls back to the §10.3 heuristic if the launch-day list differs.

| Task Type | Primary | Secondary | Tertiary | Notes |
|---|---|---|---|---|
| `code` | `kimi-k2p7-code` | `gemma-4-31b-it` | `minimax-m3` | Code specialist first |
| `reasoning` | `minimax-m3` | `gemma-4-31b-it` | `kimi-k2p7-code` | Prefer strongest general model |
| `factual` | `minimax-m3` | `gemma-4-31b-it` | `gemma-4-26b-a4b-it` | Prefer accuracy |
| `summary` | `gemma-4-26b-a4b-it` | `gemma-4-31b-it-nvfp4` | `gemma-4-31b-it` | Cheaper/efficient model ok |
| `sentiment` | local first → `gemma-4-26b-a4b-it` | `gemma-4-31b-it-nvfp4` | `minimax-m3` | Avoid call if obvious |
| `ner` | local if confident → `gemma-4-31b-it` | `gemma-4-26b-a4b-it` | `minimax-m3` | Format-sensitive |
| `math` | local first → `minimax-m3` | `gemma-4-31b-it` | `kimi-k2p7-code` | Exact computation when safe |
| `general` | `minimax-m3` | `gemma-4-31b-it` | `gemma-4-26b-a4b-it` | Safe default |

Note: model choice mainly affects **accuracy** and **answer conciseness**, not raw token accounting (input task prompts are identical across teams). The biggest token savings come from **not calling the API at all** (local solvers/models), not from picking a smaller model.

### 10.5 Model Strategy Phases

| Phase | Strategy | Purpose |
|---|---|---|
| V1 | Fireworks for almost all tasks | Verify integration and accuracy |
| V2 | Router-based model selection | Improve quality per category |
| V3 | Local solvers for obvious tasks | Reduce token usage |
| V4 | Prompt/output compression | Improve leaderboard efficiency |
| V5 | Practice benchmarking | Tune category-specific routes |

---

## 11. Functional Requirements

### FR-001 — CLI Application Startup

**Requirement:** The product must run as a command-line batch process.

**Acceptance Criteria:**

- `python -m app.main` starts the application.
- Docker `CMD` runs the same entrypoint.
- The process does not wait for manual input.
- The process exits after writing output.

---

### FR-002 — Task File Reading

**Requirement:** The product must read `/input/tasks.json` on startup.

**Acceptance Criteria:**

- Reads exact mounted path by default.
- Supports valid JSON arrays.
- Validates each task.
- Fails clearly on missing or invalid input.

---

### FR-003 — Results File Writing

**Requirement:** The product must write `/output/results.json` before successful exit.

**Acceptance Criteria:**

- Creates `/output` if missing.
- Writes valid JSON.
- Output root is a list.
- Each result has `task_id` and `answer`.
- Every input task is represented exactly once.

---

### FR-004 — Schema Validation

**Requirement:** The product must validate input and output contracts.

**Acceptance Criteria:**

- Task schema rejects missing or empty `task_id`.
- Task schema rejects missing or empty `prompt`.
- Result schema requires `task_id` and `answer`.
- Tests cover valid and invalid cases.

---

### FR-005 — Runtime Configuration Loader

**Requirement:** The product must load runtime configuration from environment variables.

**Acceptance Criteria:**

- Reads `FIREWORKS_API_KEY`.
- Reads `FIREWORKS_BASE_URL`.
- Reads and parses `ALLOWED_MODELS`.
- Trims whitespace around model IDs.
- Does not require `.env` in submitted runtime.

---

### FR-006 — Fireworks API Client

**Requirement:** The product must call Fireworks through the injected base URL.

**Acceptance Criteria:**

- Client uses `FIREWORKS_API_KEY` as API key.
- Client uses `FIREWORKS_BASE_URL` as base URL.
- Client never calls unsupported base URLs in submitted runtime.
- Client applies request timeout.
- Client handles API errors gracefully.

---

### FR-007 — Model Selection

**Requirement:** The product must select the best available allowed model per task type.

**Acceptance Criteria:**

- Model picker never returns a model absent from `ALLOWED_MODELS`.
- Code tasks prefer `kimi-k2p7-code` when present.
- Reasoning/general hard tasks prefer `minimax-m3` when present.
- Simpler tasks may use Gemma models.
- Unit tests cover missing preferred models and fallback behavior.

---

### FR-008 — Task Classification Router

**Requirement:** The product must classify prompts into task types.

Supported task types:

```text
math
sentiment
ner
summary
code
reasoning
factual
general
```

**Acceptance Criteria:**

- Debugging and generation prompts route to `code`.
- Summary prompts route to `summary`.
- Sentiment prompts route to `sentiment`.
- Entity extraction prompts route to `ner`.
- Numeric word problems route to `math`.
- Constraint puzzles route to `reasoning`.
- Definition/explanation prompts route to `factual`.
- Unknown prompts route to `general`.

---

### FR-009 — Local Solver Layer

**Requirement:** The product must attempt no-token local solving for low-risk tasks.

Initial supported local solvers:

- Simple arithmetic/percentage remaining patterns.
- Obvious sentiment classification.
- Optional simple NER only when confidence is high.

**Acceptance Criteria:**

- Local solver returns an answer only when confident.
- Local solver returns `None` when uncertain.
- Fireworks fallback is used when local solver returns `None`.
- No hidden or practice answers are hardcoded.
- Tests cover both answer and fallback paths.

---

### FR-010 — Prompt Templates

**Requirement:** The product must use short, task-specific prompts.

**Acceptance Criteria:**

- Prompts are concise.
- Prompts request English output.
- Prompts avoid unnecessary reasoning traces.
- Prompts do not include the full PRD or hackathon guide.
- Prompts ask for exact summary constraints when needed.
- Code prompts ask for corrected code or concise fix.

---

### FR-011 — Answer Cleaning

**Requirement:** The product must clean model outputs before writing results.

**Acceptance Criteria:**

- Trims whitespace.
- Prevents empty answer strings.
- Preserves code blocks when useful.
- Avoids excessive verbosity when possible.
- Does not remove important content.

---

### FR-012 — Task-Level Error Handling

**Requirement:** The product must isolate task-level errors.

**Acceptance Criteria:**

- One failed task does not crash the whole batch.
- Failed task returns `Unable to determine.` fallback.
- Fatal input/output errors still exit non-zero.
- Logs do not expose API keys.

---

### FR-013 — Docker Packaging

**Requirement:** The product must be packaged as a Docker image.

**Acceptance Criteria:**

- Uses lightweight Python base image.
- Installs minimal dependencies.
- Copies only necessary runtime files.
- Does not include `.env`.
- Does not include heavy or irrelevant directories.
- Runs `python -m app.main` as default command.

---

### FR-014 — GitHub Actions / GHCR Publishing

**Requirement:** The repo must provide CI to build and publish a public image.

**Acceptance Criteria:**

- Workflow builds on push to `main`.
- Uses Docker Buildx.
- Builds `linux/amd64` platform.
- Pushes to GitHub Container Registry.
- Final image name follows `ghcr.io/<owner>/amd-track1-agent:latest`.
- Package visibility is set to public before submission.

---

### FR-015 — Test Suite

**Requirement:** The product must include automated tests for core correctness.

**Acceptance Criteria:**

Tests cover:

- Valid input parsing.
- Invalid input handling.
- Output schema.
- Router classification.
- Model picker constraints.
- Local math solver.
- Local sentiment solver.
- Main run with mocked Fireworks client.
- No real API required for unit tests.

---

## 12. Non-Functional Requirements

### NFR-001 — Reliability

- No infinite loops.
- No long-running server.
- No manual steps inside container.
- No reliance on current working directory for input/output paths.
- No unbounded retries.

### NFR-002 — Performance

| Constraint | Requirement |
|---|---:|
| Startup readiness | Under 60 seconds |
| Total runtime | Under 10 minutes |
| Expected per task/model call | Under 30 seconds where feasible |
| Grading memory | 4GB RAM |
| Grading CPU | 2 vCPU |
| Compressed image size | Under 10GB |

### NFR-003 — Security

- No secrets in code.
- No `.env` in image.
- No API keys in logs.
- Minimal dependencies.
- Environment-variable based configuration.

### NFR-004 — Portability

- Must run on Linux.
- Must support `linux/amd64`.
- Must run locally with mounted `/input` and `/output` volumes.
- Must be pullable publicly.

### NFR-005 — Maintainability

- Modular Python files.
- Clear separation of concerns.
- Deterministic router and model picker.
- No unnecessary frameworks.
- Simple enough for both team members to debug under time pressure.

### NFR-006 — Token Efficiency

Per the official guide, only **your system prompt** and **your model's response length** affect your recorded token count (task prompts are identical across teams). Optimization ordering (guide advice): **get routing and local-model selection right first; tune output length later.**

- Prefer local deterministic solvers — and, in a later phase, permitted local LLMs — when safe. Local tokens count as **zero** toward the score.
- Route every recorded call through `FIREWORKS_BASE_URL`; calls that bypass it are not recorded and score zero tokens for that call.
- Use short system prompts.
- Avoid multi-call chains by default.
- Avoid verbose answers (later-stage optimization — do not over-tune early).
- Avoid sending repeated static context.
- Avoid asking for chain-of-thought.

---

## 13. System Architecture

### 13.1 High-Level Runtime Flow

```text
Container starts
  ↓
Load env vars
  ↓
Read /input/tasks.json
  ↓
Validate tasks
  ↓
For each task:
    classify prompt
    try local solver
    if local solver confident:
        use local answer
    else:
        select allowed Fireworks model
        call model through FIREWORKS_BASE_URL
        clean answer
    create result object
  ↓
Validate results
  ↓
Write /output/results.json
  ↓
Exit 0
```

### 13.2 Component Architecture

| Component | File | Responsibility |
|---|---|---|
| Entrypoint | `app/main.py` | Orchestrates read → solve → write |
| Schemas | `app/schema.py` | Defines `Task` and `Result` models |
| I/O | `app/io_utils.py` | Reads input and writes output |
| Config | `app/config.py` | Loads env vars and allowed models |
| Router | `app/router.py` | Classifies task category |
| Local solvers | `app/local_solvers.py` | Handles low-risk no-token tasks |
| Prompts | `app/prompts.py` | Stores short task prompts |
| Fireworks client | `app/fireworks_client.py` | Calls Fireworks and selects model |
| Errors/logging | `app/errors.py` or inline | Safe error handling |
| Tests | `tests/` | Validates core behavior |

### 13.3 Recommended Repository Structure

```text
amd-track1-agent/
  app/
    __init__.py
    main.py
    schema.py
    io_utils.py
    config.py
    router.py
    local_solvers.py
    prompts.py
    fireworks_client.py
    errors.py
  tests/
    test_schema.py
    test_io_utils.py
    test_router.py
    test_local_solvers.py
    test_model_selection.py
    test_main.py
  input/
    tasks.json
  output/
    .gitkeep
  practice/
    tasks.json
    evaluation_notes.md
  .github/
    workflows/
      docker.yml
  Dockerfile
  requirements.txt
  .dockerignore
  .gitignore
  README.md
  CLAUDE.md
  PRD.md
```

---

## 14. Implementation Blueprint

### 14.1 Suggested Dependencies

> ⛔ **IMAGE DEPENDENCY ISOLATION (hard rule — a violation caused a 0% submission).**
> Requirements are split into THREE files so demo/dev deps can NEVER enter the graded image:
> - **`requirements-image.txt`** — the GRADED image ONLY. The Dockerfile installs this and nothing
>   else. Pinned to the exact versions the passing test suite validates (image runtime == tested runtime).
> - **`requirements.txt`** — the Streamlit-Cloud DEMO only (`-r requirements-image.txt` + streamlit +
>   python-dotenv). Streamlit Cloud auto-reads this file; the image must not.
> - **`requirements-dev.txt`** — local tests (`-r requirements-image.txt` + pytest).
>
> **Incident:** the demo merge added `streamlit>=1.35` to `requirements.txt`, which the Dockerfile then
> installed into the image. Streamlit's transitive deps broke the `openai` runtime → every model call
> threw → every task fell back to `"Unable to determine."` → `ACCURACY_GATE_FAILED` 0/19. The image still
> built green and exited 0 (silent runtime break, invisible to local tests). NEVER add demo/UI/dev deps
> to `requirements-image.txt`.

#### Runtime (graded image — `requirements-image.txt`, pinned)

```text
openai==2.44.0
pydantic==2.13.4
```

#### Development (`requirements-dev.txt`)

```text
-r requirements-image.txt
pytest
python-dotenv
```

#### Demo only (`requirements.txt` — Streamlit Cloud, NOT the image)

```text
-r requirements-image.txt
streamlit
python-dotenv
```

#### Never in the graded image (`requirements-image.txt`)

```text
langchain
llama-index
transformers
torch
tensorflow
opencv
fastapi
streamlit
flask
python-dotenv
pytest
```

### 14.2 Schema Design

```python
from pydantic import BaseModel, Field

class Task(BaseModel):
    task_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)

class Result(BaseModel):
    task_id: str = Field(min_length=1)
    answer: str
```

### 14.3 Model Picker Logic

```python
import os
import re

# 1) Explicit preference tuned to the CONFIRMED Track 1 models (§10.4).
#    Used only to RANK; always filtered against runtime ALLOWED_MODELS.
_PREFERENCES = {
    "code":      ["kimi-k2p7-code", "gemma-4-31b-it", "minimax-m3"],
    "reasoning": ["minimax-m3", "gemma-4-31b-it", "kimi-k2p7-code"],
    "factual":   ["minimax-m3", "gemma-4-31b-it", "gemma-4-26b-a4b-it"],
    "summary":   ["gemma-4-26b-a4b-it", "gemma-4-31b-it-nvfp4", "gemma-4-31b-it"],
    "sentiment": ["gemma-4-26b-a4b-it", "gemma-4-31b-it-nvfp4", "minimax-m3"],
    "ner":       ["gemma-4-31b-it", "gemma-4-26b-a4b-it", "minimax-m3"],
    "math":      ["minimax-m3", "gemma-4-31b-it", "kimi-k2p7-code"],
    "general":   ["minimax-m3", "gemma-4-31b-it", "gemma-4-26b-a4b-it"],
}

# 2) Capability heuristic — fallback if the launch-day list is renamed/reordered.
def _tags(model_id: str) -> set[str]:
    m = model_id.lower()
    tags: set[str] = set()
    if any(k in m for k in ("code", "coder", "kimi")):
        tags.add("code")
    if any(k in m for k in ("instruct", "-it", "chat", "gemma", "minimax")):
        tags.add("instruct")
    sizes = [int(n) for n in re.findall(r"(\d+)\s*b", m)]
    tags.add("large" if (max(sizes) if sizes else 0) >= 30 else "small")
    return tags

_TAG_PREFS = {
    "code":      [("code",), ("instruct", "large"), ("instruct",)],
    "reasoning": [("instruct", "large"), ("code",), ("instruct",)],
    "factual":   [("instruct", "large"), ("instruct",)],
    "summary":   [("instruct",)],
    "sentiment": [("instruct",)],
    "ner":       [("instruct",)],
    "math":      [("instruct", "large"), ("instruct",)],
    "general":   [("instruct", "large"), ("instruct",)],
}

def pick_model(task_type: str, allowed: list[str]) -> str:
    if not allowed:
        raise RuntimeError("No allowed models available")

    # Optional launch-day override: MODEL_OVERRIDE_<TASKTYPE>=<model_id>
    override = os.environ.get(f"MODEL_OVERRIDE_{task_type.upper()}")
    if override and override in allowed:
        return override

    # Primary: explicit preference tuned to confirmed models.
    for candidate in _PREFERENCES.get(task_type, _PREFERENCES["general"]):
        if candidate in allowed:
            return candidate

    # Fallback: capability heuristic over whatever names are present.
    scored = [(m, _tags(m)) for m in allowed]
    for wanted in _TAG_PREFS.get(task_type, _TAG_PREFS["general"]):
        want = set(wanted)
        for model_id, tags in scored:
            if want.issubset(tags):
                return model_id

    return allowed[0]  # final fallback — never call an unlisted model
```

### 14.4 Prompt Policy

Use compact system prompts. Examples:

| Task Type | System Prompt |
|---|---|
| `general` | `Answer accurately and concisely in English.` |
| `math` | `Solve accurately. Return only the final answer unless a brief reason is necessary.` |
| `sentiment` | `Classify as positive, negative, neutral, or mixed. Include one short reason.` |
| `summary` | `Follow the requested summary format exactly. Be concise.` |
| `ner` | `Extract named entities with labels. Use concise entity - type format.` |
| `code` | `Return correct code or a concise fix. Avoid unnecessary commentary.` |
| `reasoning` | `Solve carefully. Return the final answer with a brief justification.` |

### 14.5 Fireworks Client Policy

- Use OpenAI-compatible client.
- Configure with `api_key=FIREWORKS_API_KEY`.
- Configure with `base_url=FIREWORKS_BASE_URL`.
- Set `temperature=0`.
- Use task-appropriate `max_tokens`.
- Apply timeout.
- Avoid streaming unless necessary.
- Avoid retries that can cause timeout.

### 14.6 Local Solver Policy

Local solvers are not meant to replace the model. They are meant to save tokens when confidence is high.

| Local Solver | Allowed Behavior | Forbidden Behavior |
|---|---|---|
| Math | Solve simple arithmetic/percentage patterns | Guess complex word problems incorrectly |
| Sentiment | Obvious positive/negative/mixed cases | Force label when ambiguous |
| NER | Very simple pattern extraction if reliable | Produce incomplete entity lists confidently |

---

## 15. Docker Specification

### 15.1 Dockerfile

> ⛔ Installs `requirements-image.txt` (openai + pydantic ONLY) — NOT `requirements.txt` (which carries
> the streamlit demo deps). See §14.1 for why: a `requirements.txt` install once broke the openai runtime
> and scored 0/19. Keep this line as `requirements-image.txt`.

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements-image.txt .
RUN pip install --no-cache-dir -r requirements-image.txt

COPY app ./app

CMD ["python", "-m", "app.main"]
```

### 15.2 `.dockerignore`

```text
.git
.github
.venv
__pycache__
.pytest_cache
.mypy_cache
.env
.env.*
tests
input
output
practice
*.pyc
*.md
```

### 15.3 Local Docker Build

```bash
docker build -t amd-track1-agent .
```

### 15.4 Local Docker Run

```bash
docker run --rm \
  -e FIREWORKS_API_KEY="$FIREWORKS_API_KEY" \
  -e FIREWORKS_BASE_URL="$FIREWORKS_BASE_URL" \
  -e ALLOWED_MODELS="$ALLOWED_MODELS" \
  -v "$PWD/input:/input" \
  -v "$PWD/output:/output" \
  amd-track1-agent
```

### 15.5 Output Validation

```bash
cat output/results.json
python -m json.tool output/results.json
```

---

## 16. GitHub Actions / GHCR Specification

> The official guide accepts **any public registry** (GHCR **or** Docker Hub). This PRD standardizes on **GHCR** via GitHub Actions for reproducible `linux/amd64` builds; Docker Hub is an acceptable alternative if the team prefers it.

### 16.1 Workflow Path

```text
.github/workflows/docker.yml
```

### 16.2 Workflow

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: ["main"]

permissions:
  contents: read
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push linux/amd64 image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          platforms: linux/amd64
          tags: ghcr.io/${{ github.repository_owner }}/amd-track1-agent:latest
```

### 16.3 GHCR Public Image Requirement

Before submission:

1. Open GitHub profile/org packages.
2. Open package `amd-track1-agent`.
3. Go to package settings.
4. Set visibility to **Public**.
5. Test public pull without login.

```bash
docker pull ghcr.io/YOUR_USERNAME/amd-track1-agent:latest
```

---

## 17. Testing Strategy

### 17.1 Unit Tests

| Test File | Coverage |
|---|---|
| `test_schema.py` | Valid/invalid Task and Result schemas |
| `test_io_utils.py` | Read/write JSON behavior |
| `test_router.py` | Classification for all eight categories |
| `test_local_solvers.py` | Math and sentiment local solvers |
| `test_model_selection.py` | Model picker respects allowed models |
| `test_main.py` | End-to-end run with mocked Fireworks |

### 17.2 Integration Tests

| Test | Purpose |
|---|---|
| Local Python run | Verify app flow outside Docker |
| Local Docker run | Verify mounted `/input` and `/output` paths |
| Fireworks smoke test | Verify one real model call locally |
| GHCR pull test | Verify public image availability |

### 17.3 Practice Evaluation Set

#### 17.3.1 Official practice tasks (from the guide — illustrative only, not the real grading set)

Seed `practice/tasks.json` with the eight official examples, then expand. These validate I/O handling; they are **not** the hidden evaluation set and must not be memorized or hardcoded.

```json
[
  { "task_id": "practice-01", "prompt": "What is the capital of Australia, and what body of water is it near?" },
  { "task_id": "practice-02", "prompt": "A store has 240 items. It sells 15% on Monday and 60 more on Tuesday. How many items remain?" },
  { "task_id": "practice-03", "prompt": "Classify the sentiment of this review: The battery life is great, but the screen scratches too easily." },
  { "task_id": "practice-04", "prompt": "Summarize the following in exactly one sentence: [your own sample paragraph here]." },
  { "task_id": "practice-05", "prompt": "Extract all named entities and their types from: Maria Sanchez joined Fireworks AI in Berlin last March." },
  { "task_id": "practice-06", "prompt": "This function should return the max of a list but has a bug: def get_max(nums): return nums[0]. Find and fix it." },
  { "task_id": "practice-07", "prompt": "Three friends, Sam, Jo, and Lee, each own a different pet: cat, dog, bird. Sam does not own the bird. Jo owns the dog. Who owns the cat?" },
  { "task_id": "practice-08", "prompt": "Write a Python function that returns the second-largest number in a list, handling duplicates correctly." }
]
```

#### 17.3.2 Expanded practice set

Create at least 80 practice tasks:

| Category | Minimum Count |
|---|---:|
| Factual knowledge | 10 |
| Math | 10 |
| Sentiment | 10 |
| Summarization | 10 |
| NER | 10 |
| Code debugging | 10 |
| Logical reasoning | 10 |
| Code generation | 10 |

Practice set rules:

- Do not hardcode answers.
- Include variations beyond sample prompts.
- Track wrong answers by category.
- Tune router and prompts based on failures.
- Do not overfit to fixed wording.

### 17.4 Required Pre-Submission Test Commands

```bash
pytest -q

docker build -t amd-track1-agent .

docker run --rm \
  -e FIREWORKS_API_KEY="$FIREWORKS_API_KEY" \
  -e FIREWORKS_BASE_URL="$FIREWORKS_BASE_URL" \
  -e ALLOWED_MODELS="$ALLOWED_MODELS" \
  -v "$PWD/input:/input" \
  -v "$PWD/output:/output" \
  amd-track1-agent

python -m json.tool output/results.json
```

---

## 18. Observability and Logging

### 18.1 Logging Requirements

Logs should be useful for debugging but safe for submission.

Allowed logs:

- App startup message.
- Number of tasks loaded.
- Task-level category classification.
- Whether local solver or model was used.
- Fatal errors.

Forbidden logs:

- API keys.
- Full secrets.
- Excessive model response dumps.
- Large prompt dumps that clutter logs.

### 18.2 Optional Debug Mode

A local `DEBUG` env variable may be used during development, but the submitted app must not require it.

---

## 19. Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---:|---:|---|
| R-001 | Image not publicly pullable | Medium | Critical | Use GHCR public package; test public pull |
| R-002 | Wrong architecture | Medium | Critical | GitHub Actions builds `linux/amd64` |
| R-003 | Missing output file | Medium | Critical | End-to-end Docker test with mounted output |
| R-004 | Invalid JSON schema | Medium | Critical | Schema tests and `json.tool` validation |
| R-005 | Model violation | Medium | Critical | Model picker tests against `ALLOWED_MODELS` |
| R-006 | Bypassing Fireworks base URL | Low | Critical | Centralized client only |
| R-007 | Timeout from retries | Medium | High | Short timeout, limited retries |
| R-008 | Accuracy gate failure | Medium | High | Practice set and routing improvements |
| R-009 | Token overuse | Medium | Medium | Optimize after accuracy |
| R-010 | Overengineering | High | Medium | Avoid frameworks and heavy deps |
| R-011 | Local solver wrong answer | Medium | Medium | Conservative confidence; fallback to model |
| R-012 | `.env` leaked | Low | High | `.gitignore` and `.dockerignore` |

---

## 20. Known Hackathon Failure Modes and Prevention

| Failure Status | Meaning | Prevention |
|---|---|---|
| `PULL_ERROR` | Judge cannot pull image | Public GHCR image, public pull test, `linux/amd64` manifest |
| `RUNTIME_ERROR` | Container crashed | Local Docker run test, exception handling |
| `TIMEOUT` | Did not finish within limit | API timeouts, no infinite loops, limited retries |
| `OUTPUT_MISSING` | No `/output/results.json` | End-to-end output test |
| `INVALID_RESULTS_SCHEMA` | Wrong JSON shape | Strict result schema and validation |
| `MODEL_VIOLATION` | Called disallowed model | Runtime `ALLOWED_MODELS` enforcement |
| `IMAGE_TOO_LARGE` | Image over 10GB | Slim base image, minimal deps, no local LLM initially |
| `ACCURACY_GATE_FAILED` | Answer quality too low | Practice tasks, route tuning, prompt tuning |
| `ZERO_API_CALLS` marker | No Fireworks proxy calls | Not automatically failure; acceptable only if accuracy works |

---

## 21. Implementation Roadmap

### 21.0 Time-Boxed Execution Plan (to 18:00 CET, 11 Jul 2026)

Guiding rule: **a submission that scores today beats a perfect one that misses the deadline.** The live leaderboard is the real oracle (the practice set is only a proxy), so submit early and iterate. Accuracy gate first, token rank second.

| Window | Goal | Work | Gate |
|---|---|---|---|
| **Day 1** (8 Jul eve → 9 Jul) | Get on the leaderboard | Build the API-only agent end-to-end (Phases 0–5): schema/IO, config, Fireworks client, static router, deterministic math+sentiment solvers, prompts, main, tests → Docker → GHCR public → **submit v0.1** | Image pulls, runs, writes valid results, **passes accuracy gate** |
| **Day 2** (9–10 Jul) | Harden accuracy + first token pass | 80+ practice set (seed with the official 8), fix per-category weaknesses, expand deterministic solvers, shorten prompts/output, re-submit v0.2/0.3 | Comfortable accuracy on all 8; tokens trending down |
| **Day 3** (10–11 Jul AM) | Optional stretch + finalize | *If ahead:* fine-tuned router (Phase 7a) or more local coverage — adopt only if it cuts tokens with no accuracy loss. Final tests, freeze, **submit final** with buffer before 18:00 CET | `pytest` + docker build/run + public pull clean; final image URL recorded |

**Token levers, in priority order** (do the safe ones first): (1) deterministic solvers, (2) short prompts + concise output, (3) single call / temp 0 / no CoT / no runaway retries, (4) concise-correct model per category, (5) *stretch* fine-tuned router, (6) *stretch* small local generative model. With 8 categories and 5 models on a 3-day clock, levers 1–4 capture most achievable savings at near-zero risk; treat 5–6 as bonuses, not dependencies.

### Phase 0 — Repository Setup

**Owner:** Brother  
**Exit Criteria:** Repo exists with base structure.

Tasks:

- Create GitHub repo.
- Add base folders.
- Add `.gitignore` and `.dockerignore`.
- Add this PRD as `PRD.md`.
- Create branch protection if useful.

### Phase 1 — Batch Skeleton

**Owner:** Chintu + Brother  
**Exit Criteria:** Dummy container reads input and writes valid output.

Tasks:

- Implement schemas.
- Implement input reader.
- Implement output writer.
- Return dummy answer per task.
- Build Docker locally.
- Run Docker with mounted input/output.

### Phase 2 — Fireworks Integration

**Owner:** Chintu  
**Exit Criteria:** One factual practice task receives real Fireworks answer.

Tasks:

- Implement config loader.
- Implement Fireworks client.
- Parse allowed models.
- Pick allowed model.
- Add timeout/error handling.

### Phase 3 — Router and Model Picker

**Owner:** Chintu  
**Exit Criteria:** All eight categories classified and model picker tested.

Tasks:

- Implement classifier.
- Implement task-type constants.
- Add model preference matrix.
- Add tests.

### Phase 4 — Local Solvers

**Owner:** Chintu  
**Exit Criteria:** Simple math and obvious sentiment avoid model calls.

Tasks:

- Add conservative math solver.
- Add conservative sentiment solver.
- Add optional NER helper if reliable.
- Add fallback behavior.
- Add tests.

### Phase 5 — Docker and CI

**Owner:** Brother  
**Exit Criteria:** Public `linux/amd64` GHCR image pulls successfully.

Tasks:

- Finalize Dockerfile.
- Add GitHub Actions workflow.
- Push to GHCR.
- Make package public.
- Test public pull.

### Phase 6 — Practice Evaluation

**Owner:** Both  
**Exit Criteria:** Practice set reviewed and weak categories improved.

Tasks:

- Create 80-task practice set.
- Run agent.
- Review wrong answers.
- Tune router/prompts/model choices.

### Phase 7 — Token Optimization

**Owner:** Chintu  
**Exit Criteria:** Token usage reduced without clear accuracy loss.

Per the guide, prioritize routing and local-model coverage **before** output-length tuning.

Tasks:

- Improve routing coverage so fewer tasks need a Fireworks call.
- Expand conservative local solvers.
- Avoid unnecessary fallback calls.
- Shorten system prompts.
- Reduce output verbosity (later-stage; do not over-tune early).

### Phase 7a — Fine-Tuned Query Router (primary optimization)

**Owner:** Chintu (fine-tuning on the AMD GPU pod) + Brother (CPU packaging)  
**Exit Criteria:** A small router artifact runs on the grading CPU well under the per-task budget, costs zero Fireworks tokens, and reduces total tokens vs the static router with no accuracy-gate regression.

The officially-encouraged lever (FAQ + the "Fine-Tune a Query Router" tutorial). The router only *classifies* — it never generates answers — so it is CPU-cheap and low-risk.

Tasks:

- Start from the static heuristic router (Phase 3) as the baseline and permanent fallback.
- Fine-tune a **small classifier** (e.g. a compact encoder) on the GPU pod to predict: task category + whether a local/deterministic solver suffices + the fewest-token Fireworks path that clears the gate.
- Export a **CPU-runnable** artifact; keep it small enough for < 60 s startup and a ≤ 10 GB image.
- Always fall back to the static router if the artifact fails to load — never let the router crash the batch.
- Measure token-score and accuracy deltas on the practice set before adopting.

### Phase 7b — Optional Local LLM Tier (stretch goal, evidence-gated)

**Owner:** Chintu + Brother  
**Exit Criteria:** A small local model handles a measurable share of tasks with no accuracy-gate regression, and the image still fits 4 GB RAM / 2 vCPU / ≤10 GB.

The official guide permits and encourages local inference (local tokens = zero score, still count toward accuracy). Only pursue after the API-only path clears the accuracy gate.

Tasks:

- Select a **2B–3B 4-bit quantized** model (7B 4-bit fills the entire RAM budget — avoid).
- Verify container readiness < 60 s and per-task < 30 s on 2 vCPU.
- Route only high-confidence categories to local; keep Fireworks fallback.
- Measure token-score delta and accuracy delta on the practice set before adopting.

### Phase 8 — Final Submission

**Owner:** Brother + Chintu  
**Exit Criteria:** Submitted image URL verified and recorded.

Tasks:

- Run final local tests.
- Run final Docker test.
- Run public pull test.
- Verify no `.env` in image.
- Submit image.
- Save image URL and timestamp.

--

---

## 24. Agentic Implementation Governance and `CLAUDE.md` Project Rules

The repository must include a root-level `CLAUDE.md` file. This file is not optional. It acts as the operating contract for Claude Code and any future coding-agent session.

The purpose of `CLAUDE.md` is to prevent repeated context loading, unnecessary token burn, wrong assumptions, unsafe automation, and implementation drift from this PRD.

### 24.1 Required `CLAUDE.md` Behavior

Claude Code must follow these operating rules:

1. Use `PRD.md` as the single source of truth.
2. Use `codebase-memory-mcp` to minimize repeated context and token usage.
3. Prefer reading concise project memory before re-reading large files.
4. Update codebase memory after major architectural, Docker, CI, routing, or model-selection changes.
5. Do not repeatedly summarize the whole PRD unless the user asks.
6. Do not scan the whole codebase when a targeted file read is enough.
7. When manual setup is required, stop and clearly tell the user instead of trying to continue blindly.
8. When a strategic decision is required, use a short brainstorming/options analysis before implementing.
9. Do not make irreversible or scoring-sensitive decisions silently.
10. Keep implementation focused on Track 1 only.

### 24.2 Codebase Memory MCP Usage Policy

The project will use `codebase-memory-mcp` to reduce token consumption and improve continuity between sessions.

Claude Code must use codebase memory for:

| Memory Area | What to Store | When to Update |
|---|---|---|
| Project summary | Track 1 goal, input/output contract, runtime constraints | Initial setup and major PRD updates |
| Architecture map | File responsibilities and module relationships | After structure changes |
| Decisions | Model-routing choices, Docker choices, local-solver policy | After decisions are made |
| Current phase | Active roadmap phase and next action | At the end of each work session |
| Known risks | Docker, GHCR, env vars, model violation, schema risks | When risk status changes |
| Manual setup status | What the human has completed or still needs to do | After user confirms setup |
| Test status | Latest passing/failing tests and unresolved failures | After test/debug sessions |

Claude Code must not use memory to store:

- API keys.
- Personal access tokens.
- Fireworks credentials.
- GitHub tokens.
- Private hackathon credentials.
- Hidden evaluation inputs.
- Any secret or sensitive environment value.

### 24.3 Token-Minimization Protocol for Claude Code

Claude Code must follow this protocol to reduce unnecessary token usage:

1. Start each session by checking codebase memory for:
   - Current phase.
   - Current architecture.
   - Open TODOs.
   - Recent decisions.
   - Known failing tests.
2. Read only the relevant PRD section when needed.
3. Read only the files required for the current task.
4. Avoid broad repository scans unless:
   - The issue is architectural.
   - Tests fail for unknown reasons.
   - The user asks for a full audit.
5. Prefer small, focused edits over large rewrites.
6. Prefer compact summaries over long explanations.
7. Do not paste full file contents back to the user unless requested.
8. After completing a task, update memory with a concise summary:
   - What changed.
   - Why it changed.
   - What to do next.
   - Any manual action required.

### 24.4 Manual Setup Detection Protocol

If implementation requires an action that Claude Code cannot safely complete itself, it must stop and output a clearly labeled manual setup block.

Manual setup includes but is not limited to:

| Manual Setup Item | Why Manual |
|---|---|
| Installing Docker Desktop | Requires local machine installation and user permissions |
| Starting Docker Desktop | Requires user system interaction |
| Logging into GitHub CLI | Requires browser/device authentication |
| Creating the GitHub repository | May require user account/org choice |
| Enabling GitHub Actions permissions | Requires repository settings access |
| Making GHCR package public | Requires GitHub UI/package permissions |
| Creating/using Fireworks local API key | Requires user account secret |
| Setting local environment variables | User must provide secret values |
| Running final hackathon submission | Requires official submission portal access |
| Confirming allowed models at launch | Must match official runtime list |
| Installing/configuring codebase-memory-mcp | Requires local MCP setup |
| Connecting Claude Code/Codex/Anti Gravity tools | Requires user environment setup |

When manual setup is needed, Claude Code must output exactly this style of block:

```text
MANUAL SETUP REQUIRED

What you need to do:
1. ...

Why this is needed:
...

Exact steps:
...

How to verify:
...

After you finish, tell me:
"Done: <setup name>"
```

Claude Code must not waste tokens repeatedly attempting an action that requires manual credentials, UI access, local hardware access, or user permissions.

### 24.5 Decision-Making and Brainstorming Protocol

When a decision affects scoring, architecture, token usage, Docker reliability, or model strategy, Claude Code must not guess silently.

Instead, it must use a short brainstorming process inspired by Anti Gravity-style planning:

1. Identify the decision.
2. Present 2–3 realistic options.
3. Compare pros, cons, risk, and speed.
4. Recommend one option.
5. Ask for confirmation only if the decision is high-impact or irreversible.
6. If the best option is obvious and low-risk, proceed and record the decision in memory.

Examples of decisions requiring this protocol:

| Decision Type | Example |
|---|---|
| Runtime architecture | Whether to add local LLMs or keep API-only |
| Dependency choice | Whether to add heavy libraries |
| Model strategy | Which model should handle reasoning/code/general |
| Local solver policy | Whether a local solver is accurate enough |
| Docker strategy | Local build vs GitHub Actions buildx |
| Submission image registry | GHCR vs Docker Hub |
| Error policy | Fail entire batch vs per-task fallback |
| Prompt strategy | Short answer only vs short explanation |
| Optimization strategy | Accuracy-first vs token-first |

### 24.6 Required Root `CLAUDE.md` Content

Create a root `CLAUDE.md` file containing the following:

```markdown
# Claude Project Rules — AMD Track 1 Agent

This repository implements AMD Developer Hackathon Track 1: a Dockerized Python CLI batch agent.

Use `PRD.md` as the single source of truth.

## 1. Hard Product Rules

- Python CLI batch app only.
- No web server.
- No frontend.
- No Streamlit.
- No FastAPI unless the PRD is changed.
- Read `/input/tasks.json`.
- Write `/output/results.json`.
- Output must be a JSON list of `{task_id, answer}` objects.
- Preserve every input `task_id`.
- Every input task must receive exactly one output result.
- All answers must be in English.
- Never hardcode or cache answers.
- Never overfit to practice tasks.

## 2. Fireworks Runtime Rules

- Read `FIREWORKS_API_KEY` from environment.
- Read `FIREWORKS_BASE_URL` from environment.
- Read `ALLOWED_MODELS` from environment.
- Parse `ALLOWED_MODELS` at runtime.
- Use only models present in runtime `ALLOWED_MODELS`.
- Route all Fireworks calls through `FIREWORKS_BASE_URL`.
- Never hardcode API keys.
- Never bundle `.env`.
- Never log secrets.
- Never call Claude, OpenAI, Gemini, or any non-Fireworks runtime model in the submitted container.

## 3. Docker and Submission Rules

- Docker image must support `linux/amd64`.
- Keep image small and dependency-light.
- Do not copy `.env`, `input/`, `output/`, test artifacts, or unnecessary docs into the image.
- Default command must run the batch app and exit.
- Final image must be publicly pullable.
- Reliability first, accuracy second, token efficiency third.

## 4. Codebase Memory MCP Rules

We use `codebase-memory-mcp` to minimize token usage.

Before broad work:
- Check codebase memory for current phase, architecture, previous decisions, and known issues.

During work:
- Read targeted files instead of scanning everything.
- Avoid re-reading the full PRD unless necessary.
- Avoid repeating long summaries.
- Make small, focused edits.

After meaningful work:
- Update codebase memory with:
  - What changed.
  - Why it changed.
  - Files touched.
  - Tests run.
  - Remaining TODOs.
  - Manual setup required, if any.

Never store secrets in memory:
- No API keys.
- No GitHub tokens.
- No Fireworks keys.
- No hidden evaluation data.

## 5. Manual Setup Rule

If a task requires user-side setup, credentials, UI access, local machine permissions, or official hackathon portal access, stop and tell the user.

Use this format:

MANUAL SETUP REQUIRED

What you need to do:
1. ...

Why this is needed:
...

Exact steps:
...

How to verify:
...

After you finish, tell me:
"Done: <setup name>"

Do not waste tokens pretending to complete manual setup.

Manual setup examples:
- Install Docker Desktop.
- Start Docker Desktop.
- Log in to GitHub CLI.
- Create GitHub repo.
- Make GHCR package public.
- Set local Fireworks API key.
- Configure environment variables.
- Submit image to hackathon portal.
- Install/configure codebase-memory-mcp.

## 6. Decision-Making Rule

If a decision affects architecture, scoring, Docker reliability, token usage, model routing, or dependencies, use a short brainstorming/options analysis before implementing.

For important decisions:
1. State the decision.
2. Give 2–3 options.
3. Compare pros/cons.
4. Recommend one.
5. Ask for confirmation if high-impact or irreversible.

Use Anti Gravity-style brainstorming for:
- Architecture tradeoffs.
- Dependency decisions.
- Model routing strategy.
- Local solver confidence.
- Docker/GHCR strategy.
- Token optimization strategy.

If the decision is low-risk and obvious, proceed and record it in codebase memory.

## 7. Implementation Priorities

1. Batch skeleton.
2. Input/output validation.
3. Fireworks client.
4. Runtime model selection.
5. Router.
6. Local solvers.
7. Tests.
8. Docker.
9. GitHub Actions/GHCR.
10. Practice evaluation.
11. Token optimization.

## 8. Default Engineering Principle

Make it run.
Make it right.
Make it efficient.
```

### 24.7 Acceptance Criteria for `CLAUDE.md`

The `CLAUDE.md` file is accepted when:

- It exists at repository root.
- It references `PRD.md` as the single source of truth.
- It includes codebase-memory-mcp usage rules.
- It includes token-minimization behavior.
- It includes manual setup detection behavior.
- It includes decision-making/brainstorming behavior.
- It forbids storing secrets in memory.
- It forbids wasting tokens on actions requiring user setup.
- It preserves all Track 1 hard requirements.

## 25. README Requirements

The `README.md` must include:

- Project overview.
- Track 1 explanation.
- Runtime input/output contract.
- Environment variables.
- Allowed model handling.
- Local setup.
- Local Docker build/run commands.
- GitHub Actions/GHCR instructions.
- Testing commands.
- Submission checklist.
- Troubleshooting table.

---

## 26. Acceptance Criteria

### 26.1 MVP Acceptance Criteria

The MVP is accepted when:

- Docker image builds locally.
- Docker container reads mounted `/input/tasks.json`.
- Docker container writes `/output/results.json`.
- Output JSON is valid.
- Output items contain `task_id` and `answer`.
- At least one Fireworks model call succeeds locally.
- Model selected is inside runtime `ALLOWED_MODELS`.
- `FIREWORKS_BASE_URL` is used.
- Tests pass.

### 26.2 Competitive Acceptance Criteria

The competitive version is accepted when:

- MVP criteria are complete.
- Router covers all eight categories.
- Code tasks route to `kimi-k2p7-code` when available.
- Reasoning tasks route to `minimax-m3` when available.
- Simple math avoids model calls.
- Obvious sentiment avoids model calls.
- Practice set has been reviewed.
- Prompt lengths are compact.
- Answers are concise.
- GitHub Actions builds `linux/amd64`.
- GHCR image is public.
- Public pull test passes.

### 26.3 Final Submission Acceptance Criteria

Final submission is approved only when:

- `pytest -q` passes.
- Local Docker build succeeds.
- Local Docker run succeeds.
- `/output/results.json` validates with `python -m json.tool`.
- Public GHCR image pulls without authentication.
- No `.env` exists in image.
- No API keys are committed.
- No hardcoded sample answers exist.
- Final image URL is recorded.

---

## 27. Final Pre-Submission Checklist

### Product

- [ ] Track 1 only.
- [ ] No web app.
- [ ] No server.
- [ ] All eight categories considered.

### Input/Output

- [ ] Reads `/input/tasks.json`.
- [ ] Writes `/output/results.json`.
- [ ] Valid JSON.
- [ ] Output list.
- [ ] Each item has `task_id` and `answer`.

### Fireworks

- [ ] Uses `FIREWORKS_API_KEY` from env.
- [ ] Uses `FIREWORKS_BASE_URL` from env.
- [ ] Parses `ALLOWED_MODELS` from env.
- [ ] Never calls disallowed models.
- [ ] No hardcoded key.
- [ ] No bundled `.env`.

### Docker

- [ ] Builds locally.
- [ ] Runs locally.
- [ ] Image size under 10GB.
- [ ] Supports `linux/amd64`.
- [ ] Public GHCR image.
- [ ] Public pull works.

### Runtime

- [ ] Starts under 60 seconds.
- [ ] Finishes under 10 minutes.
- [ ] No infinite loops.
- [ ] API timeout configured.
- [ ] No excessive retries.

### Quality

- [ ] Code routing works.
- [ ] Reasoning routing works.
- [ ] Math local solver works for simple cases.
- [ ] Sentiment local solver works for obvious cases.
- [ ] Summary constraints followed.
- [ ] NER outputs entity/type pairs.
- [ ] Answers are English.
- [ ] Answers are concise.

### Submission

- [ ] Rate limit respected.
- [ ] Final image URL saved.
- [ ] Final local run completed.
- [ ] Final public pull completed.
- [ ] Submitted image tag confirmed.

---

## 28. Final Product Principle

The product must be engineered like a serious evaluation system, not a class assignment.

A sophisticated AI architecture that fails Docker or schema loses immediately.

A reliable container with correct model usage, valid output, strong answers, and efficient routing can compete internationally.

Final operating principle:

```text
Reliability is the entry ticket.
Accuracy is the gate.
Token efficiency is the ranking edge.
```
