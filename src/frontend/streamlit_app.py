import base64
import html as html_lib
import json
import time
import httpx
from httpx_sse import connect_sse
import streamlit as st

API_URL = "http://localhost:8000"

PLACEHOLDER_SCENARIO = "— Custom Query —"
PRESET_SCENARIOS = [
    "FlexPendant screen stays black during boot",
    "Event Code 38101: SMB battery capacity is exhausted",
    "Axis 1 jerky motion during manual jogging",
    "How to make strawberry ice cream (Adversarial)",
]

st.set_page_config(
    page_title="ABB IRC5 Field Diagnostics",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
#  THEME
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

:root {
    --bg-app: #090d16;
    --bg-panel: #10151f;
    --bg-card: #131a29;
    --bg-card-hover: #17203350;
    --border-subtle: #212a3d;
    --text-primary: #e7ecf6;
    --text-secondary: #8b96ab;
    --accent-blue: #3b82f6;
    --accent-cyan: #22d3ee;
    --accent-green: #10b981;
    --accent-amber: #f59e0b;
    --accent-red: #ef4444;
}

/* Backgrounds */
.stApp {
    background:
        radial-gradient(circle at 12% 0%, rgba(59,130,246,0.09), transparent 42%),
        radial-gradient(circle at 88% 10%, rgba(34,211,238,0.07), transparent 45%),
        var(--bg-app);
}
section[data-testid="stSidebar"] {
    background: var(--bg-panel);
    border-right: 1px solid var(--border-subtle);
}
#MainMenu, footer { visibility: hidden; height: 0; }
header[data-testid="stHeader"] {
    background: var(--bg-app) !important;
    box-shadow: none !important;
}

/* Typography */
h1, h2, h3, h4 { color: var(--text-primary) !important; font-weight: 700 !important; }
p, span, label, div { color: var(--text-primary); }
.small-caption, .stCaption { color: var(--text-secondary) !important; }

/* ---- Header ---- */
.app-title {
    font-size: 1.65rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #ffffff 10%, #7fb4ff 60%, #22d3ee 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.app-subtitle { color: var(--text-secondary); font-size: 0.88rem; margin-top: 2px; }

.status-chip {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--bg-card); border: 1px solid var(--border-subtle);
    border-radius: 999px; padding: 6px 14px; font-size: 0.8rem; font-weight: 600;
    float: right; margin-top: 6px;
}
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot-online { background: var(--accent-green); box-shadow: 0 0 8px var(--accent-green); animation: pulse 1.8s infinite; }
.dot-offline { background: var(--accent-red); box-shadow: 0 0 8px var(--accent-red); }
@keyframes pulse { 0%{opacity:1;} 50%{opacity:0.4;} 100%{opacity:1;} }

/* ---- Sidebar cards ---- */
.side-card {
    background: var(--bg-card); border: 1px solid var(--border-subtle);
    border-radius: 10px; padding: 12px 14px; margin-bottom: 12px;
}
.side-card h4 { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em;
    color: var(--text-secondary) !important; margin: 0 0 8px 0; font-weight: 700 !important; }

/* Buttons (preset scenarios / chips / quick-start) */
.stButton>button {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
    text-align: left !important;
    font-size: 0.85rem !important;
    padding: 8px 12px !important;
    transition: all 0.15s ease;
}
.stButton>button:hover {
    border-color: var(--accent-blue) !important;
    background: #16213a !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(59,130,246,0.18);
}
.stButton>button:active { transform: translateY(0); }
.stButton>button:focus:not(:active) { color: var(--text-primary) !important; }

/* Page-wide themed scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg-app); }
::-webkit-scrollbar-thumb { background: #253046; border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: #33415e; }

/* Entrance animation */
@keyframes fadeSlideIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
[data-testid="stChatMessage"], .pipeline-wrap, .citation-card {
    animation: fadeSlideIn 0.28s ease-out;
}

/* Chat input */
[data-testid="stChatInput"] textarea {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-primary) !important;
}

/* Chat bubbles */
[data-testid="stChatMessage"] {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 8px 6px;
    margin-bottom: 10px;
}

/* User turns: right-aligned, compact bubble, avatar flips to the right */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse;
    margin-left: auto;
    max-width: 72%;
    background: #16213a;
    border-top-right-radius: 4px;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    text-align: right;
}

/* Assistant turns: left-aligned, full width (needs room for the pipeline + citation grid) */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    margin-right: auto;
    border-top-left-radius: 4px;
}

/* ---- CRAG Pipeline visualizer ---- */
.pipeline-wrap {
    background: var(--bg-card); border: 1px solid var(--border-subtle);
    border-radius: 10px; padding: 12px 14px; margin-bottom: 10px;
}
.pipe-track { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.pipe-step {
    display: inline-flex; align-items: center; gap: 6px;
    background: #17223a; border: 1px solid var(--border-subtle);
    border-radius: 999px; padding: 4px 12px; font-size: 0.78rem; font-weight: 600;
}
.step-done { border-color: #2d3f5f; color: #b7c3d9; }
.step-active { border-color: var(--accent-blue); color: #cfe3ff;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15); animation: pulse 1.6s infinite; }
.pipe-arrow { color: var(--text-secondary); font-size: 1rem; margin: 0 2px; }
.pipe-idle { color: var(--text-secondary); font-size: 0.85rem; font-style: italic; }

.verdict-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.verdict-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 999px; font-size: 0.78rem; font-weight: 700;
    letter-spacing: 0.02em;
}
.v-correct { background: rgba(16,185,129,0.15); color: var(--accent-green); border: 1px solid rgba(16,185,129,0.35); }
.v-ambiguous { background: rgba(245,158,11,0.15); color: var(--accent-amber); border: 1px solid rgba(245,158,11,0.35); }
.v-incorrect { background: rgba(239,68,68,0.15); color: var(--accent-red); border: 1px solid rgba(239,68,68,0.35); }
.v-eval { background: #17223a; color: var(--text-secondary); border: 1px solid var(--border-subtle); }

.rel-bar-track { flex: 1; min-width: 120px; height: 6px; background: #1c2437; border-radius: 999px; overflow: hidden; }
.rel-bar-fill { height: 100%; border-radius: 999px; }
.rel-label { font-size: 0.75rem; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; }

/* ---- Citation grid ---- */
.citation-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap: 12px; margin-top: 4px;
}
.citation-card {
    background: var(--bg-card); border: 1px solid var(--border-subtle);
    border-left: 3px solid var(--accent-blue); border-radius: 8px;
    padding: 12px 14px; font-size: 0.85rem; line-height: 1.5; color: #dbe3f0;
    height: 190px; overflow-y: auto; transition: all 0.15s ease;
}
.citation-card:hover { border-left-color: var(--accent-cyan); background: var(--bg-card-hover); }
.citation-card::-webkit-scrollbar { width: 5px; }
.citation-card::-webkit-scrollbar-thumb { background: #2d3a52; border-radius: 4px; }
.cite-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.badge-page {
    background: #1c2b45; color: #79b8ff; padding: 2px 9px; border-radius: 5px;
    font-size: 0.72rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;
}
.chunk-id { color: var(--text-secondary); font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; }
.cite-divider { border: none; border-top: 1px solid var(--border-subtle); margin: 0 0 8px 0; }

/* Hero / empty state */
.hero-box {
    text-align: center; padding: 46px 20px 30px 20px;
}
.hero-icon { font-size: 2.6rem; margin-bottom: 10px; }
.hero-title { font-size: 1.3rem; font-weight: 700; color: var(--text-primary); margin-bottom: 6px; }
.hero-sub { color: var(--text-secondary); font-size: 0.9rem; max-width: 520px; margin: 0 auto 22px auto; }
</style>
""", unsafe_allow_html=True)


# ============================================================
#  ICON SET  (self-contained inline SVG — no external font/CDN, renders
#  identically on any OS, unlike emoji)
# ============================================================
_ICON_PATHS = {
    "brand": '<rect x="2" y="2" width="20" height="20" rx="5"></rect>'
             '<line x1="7" y1="12" x2="12" y2="7"></line>'
             '<line x1="12" y1="7" x2="17" y2="12"></line>'
             '<line x1="7" y1="12" x2="17" y2="12"></line>'
             '<circle cx="7" cy="12" r="1.6" fill="currentColor" stroke="none"></circle>'
             '<circle cx="12" cy="7" r="1.6" fill="currentColor" stroke="none"></circle>'
             '<circle cx="17" cy="12" r="1.6" fill="currentColor" stroke="none"></circle>',
    "check-circle": '<circle cx="12" cy="12" r="9"></circle><polyline points="8 12 11 15 16 9"></polyline>',
    "alert-triangle": '<path d="M12 3 2 20h20L12 3z"></path><line x1="12" y1="9" x2="12" y2="13.5"></line>'
                       '<circle cx="12" cy="16.5" r="0.9" fill="currentColor" stroke="none"></circle>',
    "x-circle": '<circle cx="12" cy="12" r="9"></circle><line x1="9" y1="9" x2="15" y2="15"></line>'
                '<line x1="15" y1="9" x2="9" y2="15"></line>',
    "clock": '<circle cx="12" cy="12" r="9"></circle><polyline points="12 7 12 12 15.5 14"></polyline>',
    "node": '<circle cx="12" cy="12" r="4"></circle>',
    "link": '<circle cx="7" cy="12" r="3"></circle><circle cx="17" cy="12" r="3"></circle>'
            '<line x1="10" y1="12" x2="14" y2="12"></line>',
    "book": '<rect x="5" y="3" width="14" height="18" rx="2"></rect>'
            '<line x1="8" y1="8" x2="16" y2="8"></line><line x1="8" y1="12" x2="16" y2="12"></line>'
            '<line x1="8" y1="16" x2="12" y2="16"></line>',
    "flag": '<line x1="5" y1="3" x2="5" y2="21"></line><path d="M5 4h11l-2 4 2 4H5"></path>',
    "trash": '<line x1="4" y1="7" x2="20" y2="7"></line>'
             '<path d="M6 7v13a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7"></path>'
             '<path d="M9 7V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3"></path>',
}


def icon(name: str, size: int = 15, color: str = "currentColor") -> str:
    body = _ICON_PATHS.get(name, _ICON_PATHS["node"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'style="vertical-align:-3px;">{body}</svg>'
    )


def _svg_data_uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


USER_AVATAR = _svg_data_uri(
    '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24">'
    '<rect width="24" height="24" rx="6" fill="#17223a"/>'
    '<circle cx="12" cy="9.2" r="3.2" fill="none" stroke="#7fb4ff" stroke-width="1.8"/>'
    '<path d="M5.2 19.5a6.8 6.8 0 0 1 13.6 0" fill="none" stroke="#7fb4ff" stroke-width="1.8" stroke-linecap="round"/>'
    '</svg>'
)

BOT_AVATAR = _svg_data_uri(
    '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24">'
    '<rect width="24" height="24" rx="6" fill="#17223a"/>'
    '<line x1="12" y1="9" x2="12" y2="6.2" stroke="#22d3ee" stroke-width="1.8" stroke-linecap="round"/>'
    '<circle cx="12" cy="4.9" r="1" fill="#22d3ee"/>'
    '<rect x="6.2" y="9" width="11.6" height="8.6" rx="2.2" fill="none" stroke="#22d3ee" stroke-width="1.8"/>'
    '<circle cx="9.6" cy="13.3" r="1" fill="#22d3ee"/>'
    '<circle cx="14.4" cy="13.3" r="1" fill="#22d3ee"/>'
    '</svg>'
)


def render_pipeline(container, node_history, grade_verdict, relevant_count, retrieved_count):
    """Renders the live CRAG execution trace as a connected step pipeline."""
    if not node_history:
        container.markdown(
            f'<div class="pipeline-wrap"><span class="pipe-idle">{icon("clock", 14)} Awaiting query…</span></div>',
            unsafe_allow_html=True,
        )
        return

    steps_html = ""
    for i, n in enumerate(node_history):
        is_last = i == len(node_history) - 1
        state_class = "step-active" if is_last else "step-done"
        node_glyph = icon("node", 10)
        safe_label = html_lib.escape(n.replace("_", " ").title())
        steps_html += (
            f'<div class="pipe-step {state_class}">'
            f'<span>{node_glyph}</span><span>{safe_label}</span></div>'
        )
        if not is_last:
            steps_html += '<div class="pipe-arrow">›</div>'

    if grade_verdict is None:
        verdict_html = (
            f'<div class="verdict-row"><span class="verdict-badge v-eval">'
            f'{icon("clock", 13)} Evaluating context…</span></div>'
        )
    else:
        verdict_map = {
            "CORRECT": ("v-correct", "check-circle", "CORRECT"),
            "AMBIGUOUS": ("v-ambiguous", "alert-triangle", "AMBIGUOUS"),
            "INCORRECT": ("v-incorrect", "x-circle", "REJECTED"),
        }
        css_class, icon_name, label_text = verdict_map.get(grade_verdict, ("v-eval", "node", grade_verdict))
        label = f'{icon(icon_name, 13)} {label_text}'
        pct = round((relevant_count / retrieved_count) * 100) if retrieved_count else 0
        bar_color = "var(--accent-green)" if pct >= 70 else ("var(--accent-amber)" if pct >= 40 else "var(--accent-red)")
        verdict_html = f"""
        <div class="verdict-row">
            <span class="verdict-badge {css_class}">{label}</span>
            <div class="rel-bar-track"><div class="rel-bar-fill" style="width:{pct}%; background:{bar_color};"></div></div>
            <span class="rel-label">{relevant_count}/{retrieved_count} relevant · {pct}%</span>
        </div>
        """

    container.markdown(
        f'<div class="pipeline-wrap"><div class="pipe-track">{steps_html}</div>{verdict_html}</div>',
        unsafe_allow_html=True,
    )


def build_citation_grid_html(sources):
    cards = ""
    for src in sources:
        raw_content = src.get("snippet") or src.get("content") or src.get("text") or "No text available"
        raw_page = src.get("page", "N/A")
        raw_chunk_id = src.get("chunk_id", "manual-excerpt")

        # Manual text can contain literal < > & characters (e.g. "torque < 5 Nm") which,
        # left unescaped, break the surrounding HTML and leak raw markup onto the page.
        content = html_lib.escape(str(raw_content)).replace("\n", "<br>")
        page = html_lib.escape(str(raw_page))
        chunk_id = html_lib.escape(str(raw_chunk_id))

        cards += f"""
        <div class="citation-card">
            <div class="cite-head">
                <span class="badge-page">{icon('book', 12)} Page {page}</span>
                <span class="chunk-id">{chunk_id}</span>
            </div>
            <hr class="cite-divider">
            {content}
        </div>
        """
    return f'<div class="citation-grid">{cards}</div>'


def render_citations(container, sources, title, expanded=False):
    if not sources:
        return
    with container.expander(title, expanded=expanded):
        st.markdown(build_citation_grid_html(sources), unsafe_allow_html=True)


# ============================================================
#  HEADER
# ============================================================
try:
    health = httpx.get(f"{API_URL}/health", timeout=2.0)
    api_online = health.status_code == 200
except Exception:
    api_online = False

hcol1, hcol2 = st.columns([3, 1])
with hcol1:
    st.markdown(
        f'<p class="app-title">{icon("brand", 24, "#7fb4ff")} ABB Robotics IRC5 — Field Diagnostics Assistant</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="app-subtitle">Agentic Corrective RAG (CRAG) grounded in 3HAC020738-001 Troubleshooting Manual</p>',
        unsafe_allow_html=True,
    )
with hcol2:
    dot_class = "dot-online" if api_online else "dot-offline"
    status_text = "API Gateway Connected" if api_online else "API Gateway Offline"
    st.markdown(
        f'<span class="status-chip"><span class="dot {dot_class}"></span>{status_text}</span>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
st.divider()

# ============================================================
#  SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown('<div class="side-card"><h4>Controller Status</h4>' +
                (f'<span class="status-chip" style="float:none;"><span class="dot dot-online"></span>Connected</span>'
                 if api_online else
                 f'<span class="status-chip" style="float:none;"><span class="dot dot-offline"></span>Offline — run docker compose</span>')
                + '</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-card"><h4>Preset Failure Scenarios</h4>', unsafe_allow_html=True)
    for scenario_text in PRESET_SCENARIOS:
        if st.button(scenario_text, key=f"preset_{scenario_text}", use_container_width=True):
            st.session_state["queued_prompt"] = scenario_text
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="side-card">
        <h4>CRAG Pipeline Legend</h4>
        <span class="verdict-badge v-correct" style="margin-bottom:6px;">{icon('check-circle', 12)} CORRECT</span> High retrieval relevance — direct synthesis.<br><br>
        <span class="verdict-badge v-ambiguous" style="margin-bottom:6px;">{icon('alert-triangle', 12)} AMBIGUOUS</span> Noise detected — query rewritten.<br><br>
        <span class="verdict-badge v-incorrect" style="margin-bottom:6px;">{icon('x-circle', 12)} REJECTED</span> Out-of-domain — guardrail triggered.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Roadmap"):
        st.caption("v2 (planned): multi-turn conversational memory across the CRAG pipeline, so follow-up questions reuse prior context instead of running as isolated single-turn queries.")

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ============================================================
#  SESSION STATE
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "queued_prompt" not in st.session_state:
    st.session_state.queued_prompt = None

# ============================================================
#  EMPTY STATE / QUICK START
# ============================================================
if not st.session_state.messages:
    st.markdown(f"""
    <div class="hero-box">
        <div class="hero-icon">{icon('brand', 40, '#7fb4ff')}</div>
        <div class="hero-title">Describe a fault, or paste an Event Code</div>
        <div class="hero-sub">The agent retrieves from the IRC5 troubleshooting manual, grades relevance,
        and only answers when the evidence is grounded. Try one of the benchmark cases below.</div>
    </div>
    """, unsafe_allow_html=True)

    qcols = st.columns(len(PRESET_SCENARIOS))
    for i, scenario_text in enumerate(PRESET_SCENARIOS):
        with qcols[i]:
            if st.button(scenario_text, key=f"quickstart_{i}", use_container_width=True):
                st.session_state["queued_prompt"] = scenario_text
                st.rerun()

# ============================================================
#  RENDER CHAT HISTORY
# ============================================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=USER_AVATAR if msg["role"] == "user" else BOT_AVATAR):
        if msg["role"] == "assistant" and msg.get("node_history"):
            hist_pipeline_box = st.empty()
            render_pipeline(
                hist_pipeline_box,
                msg.get("node_history", []),
                msg.get("grade_verdict"),
                msg.get("relevant_count", 0),
                msg.get("retrieved_count", 0),
            )
        st.markdown(msg["content"])
        if msg.get("sources"):
            render_citations(st, msg["sources"], f"View {len(msg['sources'])} grounded manual citations")

# ============================================================
#  PROMPT RESOLUTION  (chat box takes priority over a queued preset)
# ============================================================
user_query = st.chat_input("Enter fault description or event code...", key="main_chat_input")

if user_query:
    active_prompt = user_query
elif st.session_state.queued_prompt:
    active_prompt = st.session_state.queued_prompt
    st.session_state.queued_prompt = None
else:
    active_prompt = None

# ============================================================
#  HANDLE TURN
# ============================================================
if active_prompt:
    st.session_state.messages.append({"role": "user", "content": active_prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(active_prompt)

    node_history = []
    grade_verdict = None
    relevant_count = 0
    retrieved_count = 0
    accumulated_text = ""
    final_sources = []
    event_log = []  # diagnostics: (event_name, raw_data) for every SSE event received this turn

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        pipeline_box = st.empty()
        generation_box = st.empty()
        citations_box = st.empty()
        diagnostics_box = st.empty()

        render_pipeline(pipeline_box, node_history, grade_verdict, relevant_count, retrieved_count)

        try:
            with httpx.Client(timeout=90.0) as client:
                with connect_sse(
                    client, "POST", f"{API_URL}/diagnose/stream", json={"query": active_prompt}
                ) as sse_stream:
                    for event in sse_stream.iter_sse():
                        event_log.append((event.event, event.data))

                        if event.event == "status":
                            data = json.loads(event.data)
                            node_history.append(data.get("node", "pipeline"))
                            render_pipeline(pipeline_box, node_history, grade_verdict, relevant_count, retrieved_count)

                        elif event.event == "grade":
                            data = json.loads(event.data)
                            grade_verdict = data.get("verdict")
                            relevant_count = data.get("relevant", 0)
                            retrieved_count = data.get("retrieved", 0)
                            render_pipeline(pipeline_box, node_history, grade_verdict, relevant_count, retrieved_count)

                        elif event.event == "token":
                            data = json.loads(event.data)
                            accumulated_text += data.get("token", "")
                            generation_box.markdown(accumulated_text + "▌")

                        elif event.event == "sources":
                            data = json.loads(event.data)
                            final_sources = data.get("sources", [])

                        elif event.event == "done":
                            generation_box.markdown(accumulated_text)

            render_citations(citations_box, final_sources, "Grounded manual excerpts & citations", expanded=True)

            if not accumulated_text and not event_log:
                # The connection succeeded but the backend sent nothing at all for this turn —
                # this is a backend/session issue, not a rendering issue.
                st.warning(
                    "The backend returned no events for this query. If this only happens on the "
                    "2nd+ message, check that `/diagnose/stream` starts a fresh graph run per "
                    "request rather than reusing state (e.g. a shared checkpointer/thread_id) "
                    "from the previous turn."
                )
            elif not accumulated_text:
                st.warning("The pipeline ran but produced no answer text for this query.")

            with diagnostics_box.expander("🩺 Diagnostics: raw SSE events for this turn", expanded=False):
                st.caption(f"{len(event_log)} event(s) received from {API_URL}/diagnose/stream")
                for ev_name, ev_data in event_log:
                    st.markdown(f"**`{ev_name}`**")
                    st.code(ev_data, language="json")

            st.session_state.messages.append({
                "role": "assistant",
                "content": accumulated_text,
                "sources": final_sources,
                "node_history": list(node_history),
                "grade_verdict": grade_verdict,
                "relevant_count": relevant_count,
                "retrieved_count": retrieved_count,
            })
            if accumulated_text:
                st.rerun()

        except Exception as err:
            st.error("Inference error — see full traceback below.")
            st.exception(err)
            with diagnostics_box.expander("🩺 Diagnostics: events received before the error", expanded=True):
                st.caption(f"{len(event_log)} event(s) received before failure")
                for ev_name, ev_data in event_log:
                    st.markdown(f"**`{ev_name}`**")
                    st.code(ev_data, language="json")