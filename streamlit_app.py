"""AstraRoute AI Agent — Streamlit demo frontend.

Parallel entry point to the Docker CLI batch agent.
Reuses app/ modules unchanged. No file-system writes (stateless).
"""
from __future__ import annotations

import json
import time
from typing import Any

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()  # local dev only — Streamlit Cloud uses Secrets manager
except ImportError:
    pass  # python-dotenv not installed on Cloud — env vars come from st.secrets

# ── page config (must be first st call) ──────────────────────────────────────
st.set_page_config(
    page_title="AstraRoute AI Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS: Brutalist Light Theme ────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700;900&family=IBM+Plex+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
        background-color: #FAFAF5;
        color: #1C1C1C;
    }
    /* Headings */
    h1, h2, h3 { font-weight: 900; letter-spacing: -1px; }

    /* Main area */
    .block-container { padding-top: 2rem; }

    /* Accent bar */
    .accent-bar {
        height: 6px; background: #D93B0F;
        margin: 0.5rem 0 1.5rem 0; border: none;
    }

    /* Cards */
    .brut-card {
        background: #FFFFFF;
        border: 3px solid #1C1C1C;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 6px 6px 0px #1C1C1C;
    }

    /* Buttons */
    .stButton > button {
        background: #1C1C1C !important;
        color: #FFFFFF !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border: 3px solid #1C1C1C !important;
        border-radius: 0 !important;
        padding: 0.6rem 1.8rem !important;
        box-shadow: 4px 4px 0px #D93B0F !important;
        transition: box-shadow 0.1s, transform 0.1s !important;
    }
    .stButton > button:hover {
        box-shadow: 2px 2px 0px #D93B0F !important;
        transform: translate(2px, 2px) !important;
    }

    /* Text inputs / text areas */
    .stTextArea textarea, .stTextInput input {
        border: 3px solid #1C1C1C !important;
        border-radius: 0 !important;
        font-family: 'IBM Plex Mono', monospace !important;
        background: #FFFFFF !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 3px solid #1C1C1C;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 700;
        font-size: 0.85rem;
        border: 2px solid #1C1C1C;
        margin: 2px;
    }
    .badge-math     { background: #F5A623; color: #1C1C1C; }
    .badge-code     { background: #1C1C1C; color: #FFFFFF; }
    .badge-sentiment{ background: #D93B0F; color: #FFFFFF; }
    .badge-ner      { background: #4A90D9; color: #FFFFFF; }
    .badge-summary  { background: #7B5EA7; color: #FFFFFF; }
    .badge-factual  { background: #2E7D32; color: #FFFFFF; }
    .badge-reasoning{ background: #E65100; color: #FFFFFF; }
    .badge-general  { background: #546E7A; color: #FFFFFF; }

    /* Answer box */
    .answer-box {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.05rem;
        background: #FAFAF5;
        border-left: 5px solid #D93B0F;
        padding: 1rem;
        margin-top: 0.5rem;
        white-space: pre-wrap;
    }

    /* Metric overrides */
    [data-testid="metric-container"] {
        border: 3px solid #1C1C1C;
        padding: 1rem;
        box-shadow: 4px 4px 0px #1C1C1C;
        background: #FFFFFF;
    }

    /* Dividers */
    hr { border: 2px solid #1C1C1C; margin: 2rem 0; }

    /* Section labels */
    .section-label {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #D93B0F;
        margin-bottom: 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── session state init ────────────────────────────────────────────────────────
for key, default in {
    "total_tasks": 0,
    "local_tasks": 0,
    "fireworks_tasks": 0,
    "total_tokens": 0,
    "last_result": None,
    "batch_results": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── helpers ───────────────────────────────────────────────────────────────────

KNOWN_MODELS = [
    "minimax-m3",
    "kimi-k2p7-code",
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it-nvfp4",
]

CATEGORY_COLORS = {
    "math": "badge-math", "code": "badge-code", "sentiment": "badge-sentiment",
    "ner": "badge-ner", "summary": "badge-summary", "factual": "badge-factual",
    "reasoning": "badge-reasoning", "general": "badge-general",
}


def badge_html(category: str) -> str:
    css = CATEGORY_COLORS.get(category, "badge-general")
    return f'<span class="badge {css}">{category.upper()}</span>'


def build_config(api_key: str, base_url: str, models: list[str]):
    """Build a Config object from sidebar inputs."""
    from app.config import Config
    return Config(api_key=api_key or None, base_url=base_url or None, allowed_models=models)


def complete_with_usage(
    config: Any,
    prompt: str,
    system: str | None,
    model: str,
    max_tokens: int = 512,
) -> tuple[str, int]:
    """Call Fireworks and return (answer, total_tokens). Zero changes to app/."""
    from openai import OpenAI
    client = OpenAI(api_key=config.api_key, base_url=config.base_url, timeout=config.timeout)
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=0, max_tokens=max_tokens
    )
    answer = (resp.choices[0].message.content or "").strip()
    tokens = resp.usage.total_tokens if resp.usage else 0
    return answer, tokens


def run_single_task(prompt: str, config: Any) -> dict:
    """Run one prompt through the full pipeline. Returns trace dict."""
    from app import local_solvers, prompts, router
    from app.fireworks_client import FireworksError

    t0 = time.time()
    task_type = router.classify(prompt)
    local_answer = local_solvers.try_solve(task_type, prompt)

    if local_answer is not None:
        latency_ms = int((time.time() - t0) * 1000)
        return {
            "answer": local_answer,
            "task_type": task_type,
            "solver": "Local Solver",
            "model": None,
            "tokens": 0,
            "latency_ms": latency_ms,
            "error": None,
        }

    if not config.has_fireworks():
        return {
            "answer": "Fireworks API key required — enter your key in the sidebar.",
            "task_type": task_type,
            "solver": "—",
            "model": None,
            "tokens": 0,
            "latency_ms": 0,
            "error": "no_config",
        }

    model = router.pick_model(task_type, config.allowed_models)
    system = prompts.system_prompt(task_type)
    try:
        answer, tokens = complete_with_usage(config, prompt, system, model)
    except Exception as exc:
        return {
            "answer": "Unable to determine.",
            "task_type": task_type,
            "solver": "Fireworks AI",
            "model": model,
            "tokens": 0,
            "latency_ms": int((time.time() - t0) * 1000),
            "error": str(exc),
        }

    latency_ms = int((time.time() - t0) * 1000)
    return {
        "answer": answer,
        "task_type": task_type,
        "solver": "Fireworks AI",
        "model": model,
        "tokens": tokens,
        "latency_ms": latency_ms,
        "error": None,
    }


def update_scoreboard(result: dict) -> None:
    st.session_state.total_tasks += 1
    st.session_state.total_tokens += result["tokens"]
    if result["tokens"] == 0 and result["error"] is None:
        st.session_state.local_tasks += 1
    else:
        st.session_state.fireworks_tasks += 1


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚡ AstraRoute Config")
    st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

    api_key = st.text_input(
        "FIREWORKS_API_KEY",
        type="password",
        placeholder="fw-...",
        help="Your Fireworks AI API key. Never stored.",
    )
    base_url = st.text_input(
        "FIREWORKS_BASE_URL",
        value="https://api.fireworks.ai/inference/v1",
    )
    selected_models = st.multiselect(
        "ALLOWED_MODELS",
        options=KNOWN_MODELS,
        default=KNOWN_MODELS,
    )

    st.markdown("---")
    if api_key and selected_models:
        st.success("🟢 Connected — ready to call Fireworks")
    elif not api_key:
        st.warning("🔴 No API key — local solvers only")
    else:
        st.warning("🔴 Select at least one model")

    st.markdown("---")
    st.markdown("**Team**")
    st.markdown("Sara Arif & Muhammad Ali Arif")
    st.markdown("**AMD Developer Hackathon — Track 1**")
    st.markdown("[GitHub Repo](https://github.com) · [Fireworks AI](https://fireworks.ai)")

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("# ⚡ AstraRoute AI Agent")
st.markdown(
    "*AMD Developer Hackathon — Track 1 &nbsp;|&nbsp; "
    "Team: Sara Arif & Muhammad Ali Arif*"
)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# Build config from sidebar
cfg = build_config(api_key, base_url, selected_models)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["🚀 Single Task", "📦 Batch Runner", "🗺️ Architecture", "📊 Scoreboard"]
)

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — SINGLE TASK RUNNER
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-label">Section 1 — Single Task Runner</p>', unsafe_allow_html=True)
    st.markdown("### Run a single prompt through the agent pipeline")

    prompt_input = st.text_area(
        "Enter your task prompt",
        height=120,
        placeholder=(
            "Examples:\n"
            "• What is the capital of France?\n"
            "• Calculate 156 + 89\n"
            "• Classify the sentiment: 'I loved this product!'\n"
            "• Write a Python function to reverse a string."
        ),
    )

    run_btn = st.button("▶ RUN AGENT", use_container_width=False)

    if run_btn:
        if not prompt_input.strip():
            st.error("Please enter a prompt first.")
        else:
            with st.spinner("Classifying task…"):
                time.sleep(0.3)  # brief pause for UX
            with st.spinner("Solving…"):
                result = run_single_task(prompt_input.strip(), cfg)
            st.session_state.last_result = result
            update_scoreboard(result)

    # Display result card
    if st.session_state.last_result:
        r = st.session_state.last_result
        solver_label = (
            "Local Solver (0 tokens)" if r["tokens"] == 0 and r["error"] is None
            else f"Fireworks AI — {r['model']}"
        )
        st.markdown(
            f"""
            <div class="brut-card">
                <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
                    <span style="font-weight:900; font-size:1.1rem;">RESULT</span>
                    {badge_html(r['task_type'])}
                </div>
                <div class="answer-box">{r['answer']}</div>
                <div style="margin-top:1rem; display:flex; gap:2rem; flex-wrap:wrap; font-family:'IBM Plex Mono',monospace; font-size:0.85rem;">
                    <span><strong>SOLVER:</strong> {solver_label}</span>
                    <span><strong>TOKENS:</strong> {r['tokens']}</span>
                    <span><strong>LATENCY:</strong> {r['latency_ms']} ms</span>
                </div>
                {"<div style='margin-top:0.5rem; color:#D93B0F; font-size:0.8rem;'>⚠ " + r['error'] + "</div>" if r['error'] and r['error'] != 'no_config' else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — BATCH RUNNER
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<p class="section-label">Section 2 — Batch Runner</p>', unsafe_allow_html=True)
    st.markdown("### Upload `tasks.json` → run all tasks → download `results.json`")

    uploaded = st.file_uploader("Upload tasks.json", type=["json"])

    if uploaded:
        try:
            raw = json.loads(uploaded.read())
            from app.schema import Task
            tasks = [Task(**item) for item in raw]
            st.success(f"{len(tasks)} tasks loaded")
            st.dataframe(
                [{"task_id": t.task_id, "prompt": t.prompt[:80] + ("…" if len(t.prompt) > 80 else "")} for t in tasks],
                use_container_width=True,
            )

            if st.button("▶ RUN BATCH", use_container_width=False):
                results_data = []
                display_rows = []
                progress = st.progress(0, text="Running batch…")

                for i, task in enumerate(tasks):
                    r = run_single_task(task.prompt, cfg)
                    update_scoreboard(r)
                    results_data.append({"task_id": task.task_id, "answer": r["answer"]})
                    display_rows.append({
                        "task_id": task.task_id,
                        "answer": r["answer"][:60] + ("…" if len(r["answer"]) > 60 else ""),
                        "category": r["task_type"],
                        "solver": "local" if r["tokens"] == 0 and not r["error"] else "fireworks",
                        "tokens": r["tokens"],
                    })
                    progress.progress((i + 1) / len(tasks), text=f"Task {i+1}/{len(tasks)}")

                progress.empty()
                st.session_state.batch_results = (results_data, display_rows)

        except Exception as e:
            st.error(f"Invalid tasks.json: {e}")

    if st.session_state.batch_results:
        results_data, display_rows = st.session_state.batch_results
        st.markdown("#### Results")
        st.dataframe(display_rows, use_container_width=True)
        st.download_button(
            label="⬇ Download results.json",
            data=json.dumps(results_data, indent=2),
            file_name="results.json",
            mime="application/json",
        )

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — ARCHITECTURE DIAGRAM
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-label">Section 3 — Architecture</p>', unsafe_allow_html=True)
    st.markdown("### How AstraRoute Routes Every Task")

    st.html("""
<div class="brut-card" style="font-family:'IBM Plex Mono',monospace; font-size:0.92rem; line-height:2;">
<div style="text-align:center;">
<div style="display:inline-block; border:3px solid #1C1C1C; padding:6px 20px; background:#FAFAF5; font-weight:700;">INPUT PROMPT</div>
<div style="margin:8px 0; font-size:1.5rem;">↓</div>
<div style="display:inline-block; border:3px solid #1C1C1C; padding:6px 20px; background:#F5A623; font-weight:700;">TASK CLASSIFIER — 8 categories</div>
<div style="font-size:0.78rem; margin:4px 0; color:#555;">code · math · sentiment · ner · summary · factual · reasoning · general</div>
<div style="margin:8px 0; font-size:1.5rem;">↓</div>
<div style="display:inline-block; border:3px solid #1C1C1C; padding:6px 20px; background:#FAFAF5; font-weight:700;">LOCAL SOLVER? <span style="color:#D93B0F;">(math &amp; sentiment only)</span></div>
<div style="display:flex; justify-content:center; gap:80px; margin:12px 0; align-items:flex-start;">
<div style="text-align:center;">
<div style="font-weight:700; color:#2E7D32;">YES ✓</div>
<div style="font-size:1.2rem;">↓</div>
<div style="border:3px solid #2E7D32; background:#E8F5E9; padding:8px 16px; font-weight:700; color:#2E7D32; box-shadow:4px 4px 0 #2E7D32;">ANSWER<br><span style="font-size:0.8rem;">0 tokens 🟢</span></div>
</div>
<div style="text-align:center;">
<div style="font-weight:700; color:#D93B0F;">NO ✗</div>
<div style="font-size:1.2rem;">↓</div>
<div style="border:3px solid #1C1C1C; background:#1C1C1C; padding:8px 16px; font-weight:700; color:#FFFFFF; box-shadow:4px 4px 0 #D93B0F;">MODEL ROUTER</div>
<div style="font-size:1.2rem;">↓</div>
<div style="border:3px solid #4A90D9; background:#E3F2FD; padding:8px 16px; font-weight:700; color:#1C1C1C; box-shadow:4px 4px 0 #4A90D9;">FIREWORKS AI API<br><span style="font-size:0.75rem; font-weight:400;">minimax-m3 · kimi-k2p7-code<br>gemma-4-31b-it · gemma-4-26b-a4b-it</span></div>
<div style="font-size:1.2rem;">↓</div>
<div style="border:3px solid #D93B0F; background:#FFEBEE; padding:8px 16px; font-weight:700; color:#D93B0F; box-shadow:4px 4px 0 #D93B0F;">ANSWER<br><span style="font-size:0.8rem;">tokens logged 🔴</span></div>
</div>
</div>
</div>
</div>
<div class="brut-card" style="margin-top:1rem;">
<strong>Key design choices:</strong>
<ul style="margin-top:0.5rem; font-family:'IBM Plex Mono',monospace; font-size:0.88rem;">
<li>Deterministic local solvers run <strong>before</strong> any API call — zero token cost</li>
<li>Model router picks the cheapest capable model per task type from <code>ALLOWED_MODELS</code></li>
<li>404-aware fallback chain — retries next allowed model if one is unavailable</li>
<li>Per-task fallback: <code>"Unable to determine."</code> — batch never crashes</li>
<li><code>temperature=0</code> on all calls — deterministic, consistent answers</li>
</ul>
</div>
""")

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — TOKEN EFFICIENCY SCOREBOARD
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<p class="section-label">Section 4 — Token Efficiency Scoreboard</p>', unsafe_allow_html=True)
    st.markdown("### Session Token Usage")
    st.caption("Counters reset on page refresh. Run tasks in the other tabs to populate.")

    tokens_saved = st.session_state.local_tasks * 150  # conservative baseline

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Tasks Run", st.session_state.total_tasks)
    col2.metric("Solved Locally 🟢", st.session_state.local_tasks, help="math + sentiment only — 0 tokens")
    col3.metric("Sent to Fireworks 🔴", st.session_state.fireworks_tasks)
    col4.metric("Total Tokens Used", st.session_state.total_tokens)
    col5.metric("Tokens Saved ✨", tokens_saved, help="Locally solved tasks × 150 (conservative baseline)")

    st.markdown("---")

    if st.session_state.total_tasks > 0:
        local_pct = int(st.session_state.local_tasks / st.session_state.total_tasks * 100)
        st.markdown(
            f"""
            <div class="brut-card">
                <strong>Local solve rate this session: {local_pct}%</strong>
                <div style="margin-top:0.5rem; background:#FAFAF5; border:2px solid #1C1C1C; height:24px;">
                    <div style="width:{local_pct}%; background:#D93B0F; height:100%;"></div>
                </div>
                <div style="margin-top:0.75rem; font-family:'IBM Plex Mono',monospace; font-size:0.85rem;">
                    Scoring model: <strong>Accuracy gate first</strong>, then ranked ascending by Fireworks token count.<br>
                    Every locally solved task = <strong>0 tokens</strong> = better leaderboard rank.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="brut-card" style="color:#888; font-family:\'IBM Plex Mono\',monospace;">No tasks run yet. Use the <strong>Single Task</strong> or <strong>Batch Runner</strong> tab.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        """
        <div class="brut-card">
            <strong>Scoring Strategy</strong>
            <ul style="font-family:'IBM Plex Mono',monospace; font-size:0.85rem; margin-top:0.5rem;">
                <li><strong>Gate 1 — Accuracy:</strong> Binary LLM-judge. Must pass to be ranked at all.</li>
                <li><strong>Gate 2 — Token rank:</strong> Among passers, fewer total Fireworks tokens = higher rank.</li>
                <li>Local math + sentiment solvers → <strong>0 tokens</strong></li>
                <li>Concise prompts + short <code>max_tokens</code> caps per task type</li>
                <li>Single call, <code>temperature=0</code>, no runaway retries</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🔄 Reset Scoreboard"):
        for key in ["total_tasks", "local_tasks", "fireworks_tasks", "total_tokens"]:
            st.session_state[key] = 0
        st.rerun()
