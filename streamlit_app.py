"""AstraRoute AI Agent -" Streamlit demo frontend.

Parallel entry point to the Docker CLI batch agent.
Reuses app/ modules unchanged. No file-system writes (stateless).
"""
from __future__ import annotations

import json
import time
from typing import Any

import streamlit as st

# "" page config (must be first st call) """"""""""""""""""""""""""""""""""""""
st.set_page_config(
    page_title="AstraRoute AI Agent",
    page_icon=":zap:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# "" CSS: Brutalist Light Theme """"""""""""""""""""""""""""""""""""""""""""""""
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700;900&family=IBM+Plex+Mono:wght@400;700&display=swap');
    html, body, [class*= css ] {
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
    section[data-testid= stSidebar ] {
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
    [data-testid= metric-container ] {
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

    /*    Hero                                                             */
    .hero-container {
        border: 3px solid #1C1C1C;
        padding: 3rem 2rem;
        margin-bottom: 2rem;
        box-shadow: 8px 8px 0px #1C1C1C;
        background: #FFFFFF;
        text-align: center;
    }
    .hero-title {
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: -2px;
        line-height: 1.1;
        margin-bottom: 0.5rem;
    }
    .hero-subtitle {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1rem;
        color: #D93B0F;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .typewriter {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.15rem;
        color: #1C1C1C;
        margin-top: 1rem;
        overflow: hidden;
        white-space: nowrap;
        border-right: 3px solid #D93B0F;
        width: 0;
        animation: typing 2.5s steps(40) 0.5s forwards,
                   blink 0.75s step-end infinite;
    }
    @keyframes typing {
        from { width: 0; }
        to   { width: 100%; max-width: 520px; }
    }
    @keyframes blink {
        50% { border-color: transparent; }
    }
    .hero-stats {
        display: flex;
        justify-content: center;
        gap: 3rem;
        margin-top: 2rem;
        flex-wrap: wrap;
    }
    .hero-stat {
        text-align: center;
        border: 3px solid #1C1C1C;
        padding: 1rem 1.5rem;
        background: #FAFAF5;
        box-shadow: 4px 4px 0px #1C1C1C;
    }
    .hero-stat-number {
        font-size: 2rem;
        font-weight: 900;
        color: #D93B0F;
    }
    .hero-stat-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 0.25rem;
    }

    /*    Team cards                                                       */
    .team-card {
        background: #FFFFFF;
        border: 3px solid #1C1C1C;
        padding: 1.5rem;
        box-shadow: 6px 6px 0px #1C1C1C;
    }
    .team-name {
        font-weight: 900;
        font-size: 1.2rem;
        margin: 0.75rem 0 0.25rem 0;
    }
    .team-role {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.8rem;
        color: #D93B0F;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.75rem;
    }
    .team-bio {
        font-size: 0.92rem;
        line-height: 1.55;
        margin-bottom: 1rem;
    }
    .team-link {
        display: inline-block;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 700;
        font-size: 0.8rem;
        color: #1C1C1C;
        text-decoration: none;
        border: 2px solid #1C1C1C;
        padding: 4px 12px;
        margin-right: 0.5rem;
        transition: background 0.15s, color 0.15s;
    }
    .team-link:hover { background: #1C1C1C; color: #FFFFFF; }
    .team-link.li:hover { background: #0A66C2; border-color: #0A66C2; color: #FFFFFF; }

    /*    Tech stack badges                                                */
    .tech-badge {
        display: inline-block;
        padding: 4px 14px;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 700;
        font-size: 0.8rem;
        border: 2px solid #1C1C1C;
        margin: 3px;
        letter-spacing: 0.5px;
        background: #FAFAF5;
    }

    /*    Example prompt buttons                                           */
    .example-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr 1fr;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
    }

    /*    Routing trace                                                    */
    .trace-container {
        border: 3px solid #1C1C1C;
        background: #FFFFFF;
        padding: 1.25rem 1.5rem;
        box-shadow: 4px 4px 0px #1C1C1C;
        margin-top: 1rem;
    }
    .trace-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #D93B0F;
        margin-bottom: 1rem;
    }
    .trace-step {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 0.75rem;
        opacity: 0;
        animation: fadeSlideIn 0.4s ease forwards;
    }
    .trace-step:nth-child(2) { animation-delay: 0.15s; }
    .trace-step:nth-child(3) { animation-delay: 0.35s; }
    .trace-step:nth-child(4) { animation-delay: 0.55s; }
    .trace-step:nth-child(5) { animation-delay: 0.75s; }
    @keyframes fadeSlideIn {
        from { opacity: 0; transform: translateX(-10px); }
        to   { opacity: 1; transform: translateX(0); }
    }
    .trace-marker {
        width: 12px;
        height: 12px;
        border: 3px solid #1C1C1C;
        background: #D93B0F;
        flex-shrink: 0;
        margin-top: 4px;
    }
    .trace-marker.green { background: #2E7D32; }
    .trace-label {
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 700;
        font-size: 0.78rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .trace-detail {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.83rem;
        color: #555555;
    }

    /*    Animated architecture                                            */
    .arch-node {
        display: inline-block;
        border: 3px solid #1C1C1C;
        padding: 6px 20px;
        font-weight: 700;
        opacity: 0;
        animation: archFadeIn 0.5s ease forwards;
    }
    .arch-arrow {
        margin: 6px 0;
        font-size: 1.4rem;
        opacity: 0;
        animation: archFadeIn 0.3s ease forwards;
    }
    @keyframes archFadeIn {
        from { opacity: 0; transform: translateY(-8px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .arch-local-yes {
        border: 3px solid #2E7D32;
        background: #E8F5E9;
        color: #2E7D32;
        font-weight: 700;
        opacity: 0;
        animation: archFadeIn 0.5s ease 1.6s forwards, archPulse 1.5s ease 2.5s 2;
    }
    .arch-api-path {
        opacity: 0;
        animation: archFadeIn 0.5s ease 1.8s forwards;
    }
    @keyframes archPulse {
        0%, 100% { box-shadow: 4px 4px 0 #2E7D32; }
        50%      { box-shadow: 4px 4px 0 #2E7D32, 0 0 0 6px rgba(46,125,50,0.12); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# "" team data """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
TEAM_NAME = "Chaotic_Team"
TEAM_TAGLINE = "Chaos in creativity. Precision in execution."

TEAM_MEMBERS = [
    {
        "name": "Muhammad Ali Arif",
        "role": "GSoC '26 Contributor | Software Engineering Student",
        "initials": "MA",
        "photo": "Muhammad Ali Arif.jpeg",
        "bio": (
            "GSoC 2026 contributor at EMBL-EBI, building browser-native genomic "
            "search tools using SQLite WASM and JBrowse. Software Engineering "
            "student at NUST, skilled in C++, front-end development, and OOP."
        ),
        "linkedin": "https://www.linkedin.com/in/aliarif-se28/",
        "github": "https://github.com/aliarif2050",
    },
    {
        "name": "Sara Arif",
        "role": "Applied AI Engineer & Data Systems Builder",
        "initials": "SA",
        "photo": "sara arif.png",
        "bio": (
            "Applied AI Engineer specializing in Agentic AI, Data Engineering, "
            "and Full-Stack Architecture. ICSC Silver Honour awardee (Top 2% of "
            "3,800+ participants). BSc Computer Science, 3.85 CGPA."
        ),
        "linkedin": "https://www.linkedin.com/in/sara-arif-792p/",
        "github": "https://github.com/SaraArif6198",
    },
]

# "" example prompts """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""
EXAMPLE_PROMPTS = {
    "math":      "A store has 240 items. It sells 15% on Monday and 30 more on Tuesday. How many remain?",
    "code":      "Write a Python function that takes a list and returns the second-largest number.",
    "sentiment": "Classify the sentiment: 'The battery life is amazing and the screen is perfect.'",
    "ner":       "Extract all named entities and their types from: Maria joined Fireworks AI in San Francisco.",
    "summary":   "Summarize the following in exactly one sentence: Artificial intelligence has transformed industries ranging from healthcare to finance, enabling automation of complex tasks and data-driven decisions.",
    "factual":   "What is the capital of Australia and what is it known for?",
    "reasoning": "Three friends each own a different pet: a cat, a dog, and a fish. Alex does not own the cat. Sam does not own the dog. Who owns what?",
    "general":   "Explain the difference between machine learning and deep learning.",
}

CATEGORY_BORDER_COLORS = {
    "math": "#F5A623", "code": "#1C1C1C", "sentiment": "#D93B0F",
    "ner": "#4A90D9", "summary": "#7B5EA7", "factual": "#2E7D32",
    "reasoning": "#E65100", "general": "#546E7A",
}

# "" session state init """"""""""""""""""""""""""""""""""""""""""""""""""""""""
for key, default in {
    "total_tasks": 0,
    "local_tasks": 0,
    "fireworks_tasks": 0,
    "total_tokens": 0,
    "last_result": None,
    "batch_results": None,
    "prompt_prefill": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# "" helpers """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

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


def get_image_base64(path: str) -> str | None:
    import base64
    import os
    try:
        if not os.path.exists(path):
            return None
        with open(path, "rb") as image_file:
            ext = os.path.splitext(path)[1].lower().replace('.', '')
            mime = 'image/jpeg' if ext in ['jpg', 'jpeg'] else 'image/png'
            return f"data:{mime};base64," + base64.b64encode(image_file.read()).decode('utf-8')
    except Exception:
        return None


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
    """Run one prompt through the full pipeline. Returns result + routing trace."""
    from app import local_solvers, prompts, router

    t0 = time.time()
    task_type = router.classify(prompt)
    trace = [{"step": "CLASSIFY", "detail": f"Detected category: {task_type.upper()}", "green": False}]

    local_answer = local_solvers.try_solve(task_type, prompt)
    if local_answer is not None:
        trace.append({"step": "LOCAL SOLVER", "detail": "Solved deterministically - 0 tokens consumed", "green": True})
        latency_ms = int((time.time() - t0) * 1000)
        return {
            "answer": local_answer,
            "task_type": task_type,
            "solver": "Local Solver",
            "model": None,
            "tokens": 0,
            "latency_ms": latency_ms,
            "error": None,
            "trace": trace,
        }

    trace.append({"step": "LOCAL SOLVER", "detail": "No deterministic solver available - routing to API", "green": False})

    if not config.has_fireworks():
        trace.append({"step": "API", "detail": "No API key configured", "green": False})
        return {
            "answer": "Fireworks API key required - enter your key in the sidebar.",
            "task_type": task_type,
            "solver": "-",
            "model": None,
            "tokens": 0,
            "latency_ms": 0,
            "error": "no_config",
            "trace": trace,
        }

    model = router.pick_model(task_type, config.allowed_models)
    trace.append({"step": "MODEL ROUTER", "detail": f"Selected: {model}", "green": False})

    system = prompts.system_prompt(task_type)
    try:
        answer, tokens = complete_with_usage(config, prompt, system, model)
    except Exception as exc:
        trace.append({"step": "FIREWORKS API", "detail": f"Error: {str(exc)[:80]}", "green": False})
        return {
            "answer": "Unable to determine.",
            "task_type": task_type,
            "solver": "Fireworks AI",
            "model": model,
            "tokens": 0,
            "latency_ms": int((time.time() - t0) * 1000),
            "error": str(exc),
            "trace": trace,
        }

    trace.append({"step": "FIREWORKS API", "detail": f"Response received - {tokens} tokens used", "green": False})
    latency_ms = int((time.time() - t0) * 1000)
    return {
        "answer": answer,
        "task_type": task_type,
        "solver": "Fireworks AI",
        "model": model,
        "tokens": tokens,
        "latency_ms": latency_ms,
        "error": None,
        "trace": trace,
    }


def update_scoreboard(result: dict) -> None:
    st.session_state.total_tasks += 1
    st.session_state.total_tokens += result["tokens"]
    if result["tokens"] == 0 and result["error"] is None:
        st.session_state.local_tasks += 1
    else:
        st.session_state.fireworks_tasks += 1


# "" SIDEBAR """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
with st.sidebar:
    st.markdown("### AstraRoute Config")
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
        st.success("Connected - ready to call Fireworks")
    elif not api_key:
        st.warning("No API key - local solvers only")
    else:
        st.warning("Select at least one model")

    st.markdown("---")
    st.markdown(f"**{TEAM_NAME}**")
    st.markdown("Muhammad Ali Arif & Sara Arif")
    st.markdown("**AMD Developer Hackathon &mdash; Track 1**")
    st.markdown("[GitHub](https://github.com/aliarif2050) . [Fireworks AI](https://fireworks.ai)")

# "" HEADER """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
st.markdown("# AstraRoute AI Agent")
st.markdown(
    '*AMD Developer Hackathon &mdash; Track 1 &nbsp;|&nbsp; '
    f'Team: {TEAM_NAME}*'
)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# Build config from sidebar
cfg = build_config(api_key, base_url, selected_models)

# "" TABS """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
tab_home, tab_try, tab_batch, tab_arch, tab_dash, tab_team = st.tabs(
    ["Home", "Try It", "Batch", "Architecture", "Dashboard", "Team"]
)

# ****************************************************************************
# TAB -" HOME
# ****************************************************************************
with tab_home:
    st.html("""
    <div class="hero-container">
        <div class="hero-subtitle">AMD DEVELOPER HACKATHON &mdash; TRACK 1</div>
        <div class="hero-title">AstraRoute AI Agent</div>
        <div style="display:flex; justify-content:center; margin-top:1rem;">
            <div class="typewriter">Route smarter. Solve faster. Save tokens.</div>
        </div>
        <div class="hero-stats">
            <div class="hero-stat">
                <div class="hero-stat-number">8</div>
                <div class="hero-stat-label">Task Categories</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-number">5</div>
                <div class="hero-stat-label">AI Models</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-number">0</div>
                <div class="hero-stat-label">Tokens -" Local Solving</div>
            </div>
        </div>
    </div>
    """)

    st.markdown('<p class="section-label">How It Works</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.html("""
        <div class="brut-card" style="text-align:center; margin:0;">
            <div style="font-size:1.6rem; font-weight:900; color:#D93B0F;">01</div>
            <div style="font-weight:900; margin:0.5rem 0; font-size:1.05rem;">CLASSIFY</div>
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.83rem; line-height:1.5;">
                Keyword heuristic identifies the task type across 8 categories in milliseconds
            </div>
        </div>
        """)
    with c2:
        st.html("""
        <div class="brut-card" style="text-align:center; margin:0;">
            <div style="font-size:1.6rem; font-weight:900; color:#D93B0F;">02</div>
            <div style="font-weight:900; margin:0.5rem 0; font-size:1.05rem;">ROUTE</div>
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.83rem; line-height:1.5;">
                Local deterministic solver attempted first. If confident, answer returned -" 0 tokens
            </div>
        </div>
        """)
    with c3:
        st.html("""
        <div class="brut-card" style="text-align:center; margin:0;">
            <div style="font-size:1.6rem; font-weight:900; color:#D93B0F;">03</div>
            <div style="font-weight:900; margin:0.5rem 0; font-size:1.05rem;">ANSWER</div>
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.83rem; line-height:1.5;">
                Optimal Fireworks model selected per task type. Concise, accurate, token-efficient
            </div>
        </div>
        """)

# ****************************************************************************
# TAB -" TRY IT (Single Task + Examples + Preview + Trace)
# ****************************************************************************
with tab_try:
    st.markdown('<p class="section-label">Example Prompts -" click to load</p>', unsafe_allow_html=True)

    # Example prompts grid: 4 columns x 2 rows
    row1_cats = ["math", "code", "sentiment", "ner"]
    row2_cats = ["summary", "factual", "reasoning", "general"]

    for row_cats in [row1_cats, row2_cats]:
        cols = st.columns(4)
        for col, cat in zip(cols, row_cats):
            with col:
                border_color = CATEGORY_BORDER_COLORS.get(cat, "#1C1C1C")
                if st.button(
                    cat.upper(),
                    key=f"ex_{cat}",
                    use_container_width=True,
                    help=EXAMPLE_PROMPTS[cat],
                ):
                    st.session_state.prompt_prefill = EXAMPLE_PROMPTS[cat]

    st.markdown("---")
    st.markdown('<p class="section-label">Task Prompt</p>', unsafe_allow_html=True)

    prompt_input = st.text_area(
        "Enter your task prompt",
        value=st.session_state.prompt_prefill,
        height=120,
        placeholder="Type a prompt or click an example above.",
        label_visibility="collapsed",
    )

    # Live classification preview
    if prompt_input.strip():
        from app import router as _router
        preview_type = _router.classify(prompt_input.strip())
        st.markdown(
            f'<div style="margin:0.4rem 0 0.8rem 0;">'
            f'<span class="section-label" style="margin-right:0.5rem;">Detected:</span>'
            f'{badge_html(preview_type)}'
            f'</div>',
            unsafe_allow_html=True,
        )

    run_btn = st.button("RUN AGENT", use_container_width=False)

    if run_btn:
        if not prompt_input.strip():
            st.error("Please enter a prompt first.")
        else:
            with st.spinner("Solving..."):
                result = run_single_task(prompt_input.strip(), cfg)
            st.session_state.last_result = result
            st.session_state.prompt_prefill = prompt_input  # preserve input
            update_scoreboard(result)

    # Result card
    if st.session_state.last_result:
        r = st.session_state.last_result
        solver_label = (
            "Local Solver (0 tokens)" if r["tokens"] == 0 and r["error"] is None
            else f"Fireworks AI - {r['model']}"
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
                {"<div style='margin-top:0.5rem; color:#D93B0F; font-size:0.8rem;'>Error: " + r['error'] + "</div>" if r['error'] and r['error'] != 'no_config' else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Routing Decision Trace
        if r.get("trace"):
            steps_html = "".join([
                f'<div class="trace-step">'
                f'<div class="{"trace-marker green" if step["green"] else "trace-marker"}"></div>'
                f'<div>'
                f'<div class="trace-label">{step["step"]}</div>'
                f'<div class="trace-detail">{step["detail"]}</div>'
                f'</div>'
                f'</div>'
                for step in r["trace"]
            ])
            st.html(f'<div class="trace-container"><div class="trace-title">Routing Decision Trace</div>{steps_html}</div>')

# ****************************************************************************
# TAB - BATCH
# ****************************************************************************
with tab_batch:
    st.markdown('<p class="section-label">Batch Runner</p>', unsafe_allow_html=True)
    st.markdown("### Upload `tasks.json` - run all tasks - download `results.json`")

    uploaded = st.file_uploader("Upload tasks.json", type=["json"])

    if uploaded:
        try:
            raw = json.loads(uploaded.read())
            from app.schema import Task
            tasks = [Task(**item) for item in raw]
            st.success(f"{len(tasks)} tasks loaded")
            st.dataframe(
                [{"task_id": t.task_id, "prompt": t.prompt[:80] + ("..." if len(t.prompt) > 80 else "")} for t in tasks],
                use_container_width=True,
            )

            if st.button("RUN BATCH", use_container_width=False):
                results_data = []
                display_rows = []
                progress = st.progress(0, text="Running batch...")

                for i, task in enumerate(tasks):
                    r = run_single_task(task.prompt, cfg)
                    update_scoreboard(r)
                    results_data.append({"task_id": task.task_id, "answer": r["answer"]})
                    display_rows.append({
                        "task_id": task.task_id,
                        "answer": r["answer"][:60] + ("..." if len(r["answer"]) > 60 else ""),
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
            label="Download results.json",
            data=json.dumps(results_data, indent=2),
            file_name="results.json",
            mime="application/json",
        )

# ****************************************************************************
# TAB -" ARCHITECTURE (animated)
# ****************************************************************************
with tab_arch:
    st.markdown('<p class="section-label">Architecture</p>', unsafe_allow_html=True)
    st.markdown("### How AstraRoute Routes Every Task")

    st.html("""
<div class="brut-card" style="font-family:'IBM Plex Mono',monospace; font-size:0.9rem; line-height:2.2;">
<div style="text-align:center;">

<div class="arch-node" style="background:#FAFAF5; animation-delay:0s;">INPUT PROMPT</div>
<div class="arch-arrow" style="animation-delay:0.4s;">&#8595;</div>
<div class="arch-node" style="background:#F5A623; animation-delay:0.6s;">TASK CLASSIFIER &mdash; 8 categories</div>
<div style="font-size:0.75rem; margin:2px 0; color:#555; opacity:0; animation:archFadeIn 0.4s ease 1s forwards;">
    code &middot; math &middot; sentiment &middot; ner &middot; summary &middot; factual &middot; reasoning &middot; general
</div>
<div class="arch-arrow" style="animation-delay:1.1s;">&#8595;</div>
<div class="arch-node" style="background:#FAFAF5; animation-delay:1.2s;">
    LOCAL SOLVER? <span style="color:#D93B0F;">(math &amp; sentiment)</span>
</div>

<div style="display:flex; justify-content:center; gap:80px; margin:12px 0; align-items:flex-start;">
    <div style="text-align:center;">
        <div style="font-weight:700; color:#2E7D32; opacity:0; animation:archFadeIn 0.4s ease 1.5s forwards;">YES</div>
        <div style="font-size:1.2rem; opacity:0; animation:archFadeIn 0.3s ease 1.7s forwards;">&#8595;</div>
        <div class="arch-local-yes" style="padding:8px 16px; box-shadow:4px 4px 0 #2E7D32;">
            ANSWER<br><span style="font-size:0.78rem; font-weight:400;">0 tokens</span>
        </div>
    </div>
    <div class="arch-api-path" style="text-align:center;">
        <div style="font-weight:700; color:#D93B0F;">NO</div>
        <div style="font-size:1.2rem;">&#8595;</div>
        <div style="display:inline-block; border:3px solid #1C1C1C; padding:8px 16px; font-weight:700; background:#1C1C1C; color:#FFFFFF; box-shadow:4px 4px 0 #D93B0F;">MODEL ROUTER</div>
        <div style="font-size:1.2rem; margin:4px 0;">&#8595;</div>
        <div style="display:inline-block; border:3px solid #4A90D9; padding:8px 16px; font-weight:700; background:#E3F2FD; color:#1C1C1C; box-shadow:4px 4px 0 #4A90D9;">
            FIREWORKS AI API<br>
            <span style="font-size:0.72rem; font-weight:400;">minimax-m3 &middot; kimi-k2p7-code<br>gemma-4-31b-it &middot; gemma-4-26b-a4b-it</span>
        </div>
        <div style="font-size:1.2rem; margin:4px 0;">&#8595;</div>
        <div style="display:inline-block; border:3px solid #D93B0F; padding:8px 16px; font-weight:700; background:#FFEBEE; color:#D93B0F; box-shadow:4px 4px 0 #D93B0F;">
            ANSWER<br><span style="font-size:0.78rem; font-weight:400;">tokens recorded</span>
        </div>
    </div>
</div>

</div>
</div>

<div class="brut-card" style="margin-top:1rem;">
<strong>Key design choices:</strong>
<ul style="margin-top:0.5rem; font-family:'IBM Plex Mono',monospace; font-size:0.85rem;">
<li>Deterministic local solvers run <strong>before</strong> any API call &mdash; zero token cost</li>
<li>Model router picks the optimal model per task type from <code>ALLOWED_MODELS</code></li>
<li>404-aware fallback chain &mdash; retries next allowed model if one is unavailable</li>
<li>Per-task fallback: <code>"Unable to determine."</code> &mdash; batch never crashes</li>
<li><code>temperature=0</code> on all calls &mdash; deterministic, consistent answers</li>
</ul>
</div>
""")

# ****************************************************************************
# TAB -" DASHBOARD (Scoreboard + Token Donut)
# ****************************************************************************
with tab_dash:
    st.markdown('<p class="section-label">Dashboard</p>', unsafe_allow_html=True)
    st.markdown("### Session Token Usage")
    st.caption("Counters reset on page refresh. Run tasks in the Try It or Batch tab to populate.")

    tokens_saved = st.session_state.local_tasks * 150

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Tasks", st.session_state.total_tasks)
    col2.metric("Solved Locally", st.session_state.local_tasks, help="0 tokens consumed")
    col3.metric("Sent to Fireworks", st.session_state.fireworks_tasks)
    col4.metric("Tokens Used", st.session_state.total_tokens)
    col5.metric("Tokens Saved", tokens_saved, help="Local tasks x 150 conservative baseline")

    st.markdown("---")

    if st.session_state.total_tasks > 0:
        local_pct = int(st.session_state.local_tasks / st.session_state.total_tasks * 100)
        api_pct = 100 - local_pct

        st.markdown(
            f"""<div class="brut-card" style="display:flex; align-items:center; gap:3rem; flex-wrap:wrap;">
                <div style="
                    width:160px; height:160px;
                    border-radius:50%;
                    background: conic-gradient(
                        #2E7D32 0% {local_pct}%,
                        #D93B0F {local_pct}% 100%
                    );
                    display:flex; align-items:center; justify-content:center;
                    border:3px solid #1C1C1C; flex-shrink:0;">
                    <div style="
                        width:100px; height:100px; border-radius:50%;
                        background:#FFFFFF; border:3px solid #1C1C1C;
                        display:flex; align-items:center; justify-content:center;
                        font-weight:900; font-size:1.4rem;">{local_pct}%</div>
                </div>
                <div>
                    <div style="font-weight:900; font-size:1.05rem; margin-bottom:0.75rem;">TOKEN EFFICIENCY</div>
                    <div style="display:flex; align-items:center; gap:0.5rem; margin:0.4rem 0;">
                        <div style="width:14px; height:14px; background:#2E7D32; border:2px solid #1C1C1C;"></div>
                        <span style="font-family:'IBM Plex Mono',monospace; font-size:0.83rem;">
                            Local &mdash; {local_pct}% &nbsp;({st.session_state.local_tasks} tasks, 0 tokens)
                        </span>
                    </div>
                    <div style="display:flex; align-items:center; gap:0.5rem; margin:0.4rem 0;">
                        <div style="width:14px; height:14px; background:#D93B0F; border:2px solid #1C1C1C;"></div>
                        <span style="font-family:'IBM Plex Mono',monospace; font-size:0.83rem;">
                            API &mdash; {api_pct}% &nbsp;({st.session_state.fireworks_tasks} tasks, {st.session_state.total_tokens} tokens)
                        </span>
                    </div>
                    <div style="margin-top:0.75rem; font-family:'IBM Plex Mono',monospace; font-size:0.83rem;">
                        <strong>ESTIMATED TOKENS SAVED:</strong> {tokens_saved}
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="brut-card" style="color:#888; font-family:\'IBM Plex Mono\',monospace;">'
            'No tasks run yet. Use the <strong>Try It</strong> or <strong>Batch</strong> tab.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        """
        <div class="brut-card">
            <strong>Scoring Strategy</strong>
            <ul style="font-family:'IBM Plex Mono',monospace; font-size:0.85rem; margin-top:0.5rem;">
                <li><strong>Gate 1 &mdash; Accuracy:</strong> Binary LLM-judge. Must pass to be ranked at all.</li>
                <li><strong>Gate 2 &mdash; Token rank:</strong> Among passers, fewer total Fireworks tokens = higher rank.</li>
                <li>Local math + sentiment solvers &rarr; <strong>0 tokens</strong></li>
                <li>Concise prompts + short <code>max_tokens</code> caps per task type</li>
                <li>Single call, <code>temperature=0</code>, no runaway retries</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Reset Scoreboard"):
        for key in ["total_tasks", "local_tasks", "fireworks_tasks", "total_tokens"]:
            st.session_state[key] = 0
        st.rerun()

# ****************************************************************************
# TAB -" TEAM
# ****************************************************************************
with tab_team:
    st.markdown('<p class="section-label">The Team</p>', unsafe_allow_html=True)
    st.markdown(f"### {TEAM_NAME}")
    st.markdown(f"*{TEAM_TAGLINE}*")
    st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2, gap="large")
    for col, member in zip([col_a, col_b], TEAM_MEMBERS):
        with col:
            img_base64 = get_image_base64(member["photo"])
            if img_base64:
                img_html = f'<img src="{img_base64}" style="width:80px; height:80px; border:3px solid #1C1C1C; object-fit:cover; display:block;" />'
            else:
                img_html = f'<div style="width:80px; height:80px; border:3px solid #1C1C1C; background:#1C1C1C; color:#FFF; display:flex; align-items:center; justify-content:center; font-weight:900; font-size:1.4rem;">{member["initials"]}</div>'

            st.html(f"""
            <div class="team-card">
                {img_html}
                <div class="team-name">{member['name']}</div>
                <div class="team-role">{member['role']}</div>
                <div class="team-bio">{member['bio']}</div>
                <div>
                    <a class="team-link li" href="{member['linkedin']}" target="_blank">LinkedIn</a>
                    <a class="team-link" href="{member['github']}" target="_blank">GitHub</a>
                </div>
            </div>
            """)

    st.markdown("---")
    st.markdown('<p class="section-label">About the Project</p>', unsafe_allow_html=True)
    st.html("""
    <div class="brut-card">
        <strong>Why AstraRoute?</strong>
        <p style="font-family:'IBM Plex Mono',monospace; font-size:0.88rem; margin-top:0.5rem; line-height:1.6;">
            <em>Astra</em> (stars) + <em>Route</em> &mdash; navigating the constellation of AI models
            to find the optimal path for every task. The agent classifies each prompt, attempts a
            zero-token local solve, then routes to the best-fit Fireworks model. Fewer tokens,
            same accuracy, higher leaderboard rank.
        </p>
    </div>
    """)

    st.markdown('<p class="section-label">Tech Stack</p>', unsafe_allow_html=True)
    tech_stack = ["Python 3.11", "Fireworks AI", "Docker (linux/amd64)", "AMD GPU Pod",
                  "OpenAI-compatible API", "GitHub Actions", "Streamlit"]
    badges_html = "".join(f'<span class="tech-badge">{t}</span>' for t in tech_stack)
    st.markdown(
        f'<div style="margin-top:0.5rem;">{badges_html}</div>',
        unsafe_allow_html=True,
    )
