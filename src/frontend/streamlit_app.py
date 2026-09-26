import base64
import html as html_lib
import json
import os
import uuid
from pathlib import Path

import httpx
import streamlit as st
from httpx_sse import connect_sse
from PIL import Image

API_URL = os.getenv("API_URL", "http://localhost:8000")

CURRENT_DIR = Path(__file__).parent.resolve()
FAVICON_PATH = CURRENT_DIR / "irc5_favicon.png"

if FAVICON_PATH.exists():
    page_icon = Image.open(FAVICON_PATH)
else:
    page_icon = "🛠️"

APP_SHORT_NAME = "IRC5 Diagnostic Agent"
APP_TAGLINE = "Field Diagnostics · CRAG"

PRESET_SCENARIOS = [
    "FlexPendant screen stays black during boot",
    "Event Code 38101: SMB battery capacity is exhausted",
    "Axis 1 jerky motion during manual jogging",
    "How to make strawberry ice cream (Adversarial)",
]

st.set_page_config(
    page_title="ABB IRC5 Field Diagnostics",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

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

/* ---- Sidebar brand + chat history ---- */
.brand-row { display: flex; align-items: center; gap: 10px; margin: 2px 0 4px 0; }
.brand-name { font-weight: 800; font-size: 1.08rem; color: var(--text-primary); line-height: 1.15; }
.brand-sub { font-size: 0.72rem; color: var(--text-secondary); }
.conv-status-line {
    font-size: 0.78rem; color: var(--text-secondary);
    display: flex; align-items: center; gap: 6px; margin: 2px 0 14px 26px;
}
.side-section-label {
    font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
    color: var(--text-secondary); margin: 16px 2px 6px 2px; font-weight: 700;
}


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
.pipeline-wrap, .citation-card {
    animation: fadeSlideIn 0.28s ease-out;
}

/* Chat input */
[data-testid="stChatInput"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 16px !important;
    box-shadow: none !important;
    outline: none !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.18) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    color: var(--text-primary) !important;
    font-size: 0.95rem !important;
    padding: 14px 6px !important;
}
[data-testid="stChatInput"] textarea:focus {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-secondary) !important;
}
[data-testid="stChatInput"] button {
    background: var(--accent-blue) !important;
    border: none !important;
    border-radius: 10px !important;
    transition: background 0.15s ease, transform 0.15s ease;
}
[data-testid="stChatInput"] button:hover {
    background: var(--accent-cyan) !important;
    transform: translateY(-1px);
}
[data-testid="stChatInput"] button svg { fill: #04101f !important; }

/* Assistant turns: no avatar/icon — plain st.container(border=True), Streamlit's own
   native bordered box (no CSS override needed for the border/radius itself). Just add
   spacing to match the rest of the layout. */
[data-testid="stVerticalBlockBorderWrapper"] {
    margin-bottom: 10px;
}

/* User turns are rendered as one self-contained HTML block (see render_user_turn()),
   not through st.chat_message — full control over layout, no dependency on Streamlit's
   internal avatar/content structure. */
.user-turn-row {
    display: flex;
    align-items: flex-start;
    justify-content: flex-end;
    gap: 10px;
    margin: 4px 0 14px 0;
}
.user-bubble {
    background: #16213a;
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    border-top-right-radius: 4px;
    padding: 12px 18px;
    max-width: 68%;
    color: var(--text-primary);
    text-align: left;
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


_ICON_PATHS = {
   "brand": '<rect x="3" y="4" width="8" height="16" rx="1.5"></rect>'
       + '<line x1="5" y1="8" x2="9" y2="8"></line>'
       + '<line x1="5" y1="10.5" x2="9" y2="10.5"></line>'
       + '<circle cx="7" cy="14" r="1.2" fill="none"></circle>'
       + '<line x1="11.5" y1="9" x2="14.5" y2="6"></line>'
       + '<line x1="14.5" y1="6" x2="19" y2="8.5"></line>'
       + '<line x1="19" y1="8.5" x2="19" y2="12"></line>'
       + '<line x1="19" y1="12" x2="17" y2="14.5"></line>'
       + '<line x1="19" y1="12" x2="21" y2="14"></line>'
       + '<circle cx="14.5" cy="6" r="1.5" fill="none"></circle>'
       + '<circle cx="19" cy="8.5" r="1.5" fill="none"></circle>',
    "check-circle": '<circle cx="12" cy="12" r="9"></circle><polyline points="8 12 11 15 16 9"></polyline>',
    "alert-triangle": '<path d="M12 3 2 20h20L12 3z"></path><line x1="12" y1="9" x2="12" y2="13.5"></line>'
                       '<circle cx="12" cy="16.5" r="0.9" fill="currentColor" stroke="none"></circle>',
    "x-circle": '<circle cx="12" cy="12" r="9"></circle><line x1="9" y1="9" x2="15" y2="15"></line>'
                '<line x1="15" y1="9" x2="9" y2="15"></line>',
    "clock": '<circle cx="12" cy="12" r="9"></circle><polyline points="12 7 12 12 15.5 14"></polyline>',
    "node": '<circle cx="12" cy="12" r="4"></circle>',
    "user": '<circle cx="12" cy="8" r="3.2"></circle><path d="M5 20a7 7 0 0 1 14 0"></path>',
    "link": '<circle cx="7" cy="12" r="3"></circle><circle cx="17" cy="12" r="3"></circle>'
            '<line x1="10" y1="12" x2="14" y2="12"></line>',
    "book": '<rect x="5" y="3" width="14" height="18" rx="2"></rect>'
            '<line x1="8" y1="8" x2="16" y2="8"></line><line x1="8" y1="12" x2="16" y2="12"></line>'
            '<line x1="8" y1="16" x2="12" y2="16"></line>',
    "flag": '<line x1="5" y1="3" x2="5" y2="21"></line><path d="M5 4h11l-2 4 2 4H5"></path>',
    "trash": '<line x1="4" y1="7" x2="20" y2="7"></line>'
             '<path d="M6 7v13a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7"></path>'
             '<path d="M9 7V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3"></path>',
    "pencil": '<path d="M4 20l1-4L15.5 5.5l3 3L8 19l-4 1z"></path><line x1="13.5" y1="7.5" x2="16.5" y2="10.5"></line>',
    "plus": '<line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line>',
    "dots-vertical": '<circle cx="12" cy="5" r="1.6" fill="currentColor" stroke="none"></circle>'
                      '<circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none"></circle>'
                      '<circle cx="12" cy="19" r="1.6" fill="currentColor" stroke="none"></circle>',
}


def icon(name: str, size: int = 15, color: str = "currentColor") -> str:
    body = _ICON_PATHS.get(name, _ICON_PATHS["node"])

    # Make the IRC5 icon slightly bolder without changing the other icons.
    stroke_width = "1" if name == "brand" else "2"

    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="vertical-align:-3px;">{body}</svg>'
    )


def icon_data_uri(name: str, color: str) -> str:
    """A fixed-color version of an icon, baked into a data URI for use as a CSS
    background-image — needed because st.button()/st.popover() labels are plain
    text only and can't render our inline-SVG icons directly."""
    body = _ICON_PATHS.get(name, _ICON_PATHS["node"])
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    )
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


st.markdown("""
<style>
/* Uses st.container(key=...): Streamlit adds a real class "st-key-<key>" to that
   container's wrapper element, matched here with a plain [class*="..."] attribute
   selector — no :has()/sibling tricks, works in every browser. */

/* Recent chat list: flat rows, no per-item card/border — highlight only on hover / active.
   Also styles the plain buttons used by the inline Rename/Delete reveal (no popover). */
[class*="st-key-convrow-"] {
    border-radius: 8px;
    margin-bottom: 1px;
    padding-bottom: 2px;
}
[class*="st-key-convrow-active-"] {
    background: rgba(59,130,246,0.12);
    border-left: 2px solid var(--accent-blue);
    border-radius: 6px;
}
[class*="st-key-convrow-"] .stButton>button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    text-align: left !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 7px 8px !important;
}
[class*="st-key-convrow-"] .stButton>button:hover {
    background: var(--bg-card-hover) !important;
    transform: none !important;
    box-shadow: none !important;
}

/* "Try an example" trigger */
[class*="st-key-suggest-toggle-wrap"] {
    width: 100% !important;
    max-width: 100% !important;

    margin-top: -8px !important;
    margin-bottom: 18px !important;

    display: block !important;
}

[class*="st-key-suggest-toggle-wrap"] .stButton {
    width: 100% !important;

    display: flex !important;
    justify-content: center !important;
}

[class*="st-key-suggest-toggle-wrap"] .stButton > button {
    width: 150px !important;
    min-width: 150px !important;
    max-width: 150px !important;

    height: 34px !important;
    min-height: 34px !important;

    padding: 0 13px !important;

    border-radius: 9px !important;
    border: 1px solid var(--border-subtle) !important;
    background: var(--bg-card) !important;

    color: var(--text-secondary) !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;

    display: flex !important;
    align-items: center !important;
    justify-content: center !important;

    white-space: nowrap !important;
    overflow: visible !important;
    text-overflow: clip !important;

    box-shadow: none !important;
    transform: none !important;
}

[class*="st-key-suggest-toggle-wrap"] .stButton > button:hover {
    color: var(--text-primary) !important;
    border-color: var(--accent-blue) !important;
    background: #16213a !important;
    box-shadow: 0 3px 10px rgba(59,130,246,0.12) !important;
    transform: none !important;
}
[class*="st-key-suggest-toggle-wrap"] {
    width: 520px !important;
    max-width: 0% !important;
    margin: -8px auto 18px auto !important;
}

[class*="st-key-suggest-toggle-wrap"] .stButton {
    display: flex !important;
    justify-content: center !important;
}
</style>
""", unsafe_allow_html=True)


def render_user_turn(text: str):
    """Renders a user message as one self-contained HTML block — no avatar/icon,
    just the right-aligned bubble."""
    safe_text = html_lib.escape(text).replace("\n", "<br>")
    st.markdown(
        f'<div class="user-turn-row"><div class="user-bubble">{safe_text}</div></div>',
        unsafe_allow_html=True,
    )


_ICON_URI_PENCIL = icon_data_uri("pencil", "#aeb8ca")
_ICON_URI_TRASH = icon_data_uri("trash", "#aeb8ca")

st.markdown("""
<style>

/* Rename action */
[class*="st-key-rename_open_"] .stButton > button {
    background-image: url("__PENCIL_ICON__") !important;
    background-repeat: no-repeat !important;
    background-position: 12px center !important;
    background-size: 15px 15px !important;

    padding-left: 34px !important;
    padding-right: 12px !important;

    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: var(--text-secondary) !important;

    border-radius: 8px !important;
}

/* Delete action */
[class*="st-key-delete_"] .stButton > button {
    background-image: url("__TRASH_ICON__") !important;
    background-repeat: no-repeat !important;
    background-position: 12px center !important;
    background-size: 15px 15px !important;

    padding-left: 34px !important;
    padding-right: 12px !important;

    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: var(--text-secondary) !important;

    border-radius: 8px !important;
}

/* Hover */
[class*="st-key-rename_open_"] .stButton > button:hover {
    background-image: url("__PENCIL_ICON__") !important;
    background-repeat: no-repeat !important;
    background-position: 12px center !important;
    background-size: 15px 15px !important;

    color: var(--text-primary) !important;
    background-color: #182238 !important;
    border-color: #33415e !important;
    transform: none !important;
}

[class*="st-key-delete_"] .stButton > button:hover {
    background-image: url("__TRASH_ICON__") !important;
    background-repeat: no-repeat !important;
    background-position: 12px center !important;
    background-size: 15px 15px !important;

    color: #fca5a5 !important;
    background-color: rgba(239,68,68,0.08) !important;
    border-color: rgba(239,68,68,0.25) !important;
    transform: none !important;
}

</style>
""".replace("__PENCIL_ICON__", _ICON_URI_PENCIL)
   .replace("__TRASH_ICON__", _ICON_URI_TRASH),
unsafe_allow_html=True)

def _new_conversation_id() -> str:
    return uuid.uuid4().hex[:8]


def ensure_conversation_state():
    if "conversations" not in st.session_state:
        cid = _new_conversation_id()
        st.session_state.conversations = {cid: {"title": "New chat", "messages": []}}
        st.session_state.conversation_order = [cid]
        st.session_state.active_conversation_id = cid


def create_new_conversation():
    cid = _new_conversation_id()
    st.session_state.conversations[cid] = {"title": "New chat", "messages": []}
    st.session_state.conversation_order.insert(0, cid)
    st.session_state.active_conversation_id = cid


def delete_conversation(cid: str):
    st.session_state.conversations.pop(cid, None)
    if cid in st.session_state.conversation_order:
        st.session_state.conversation_order.remove(cid)
    if not st.session_state.conversation_order:
        create_new_conversation()
    elif st.session_state.active_conversation_id == cid:
        st.session_state.active_conversation_id = st.session_state.conversation_order[0]


def rename_conversation(cid: str, new_title: str):
    new_title = new_title.strip()
    if new_title and cid in st.session_state.conversations:
        st.session_state.conversations[cid]["title"] = new_title[:60]


def render_pipeline(container, node_history, grade_verdict, relevant_count, retrieved_count, is_complete=False):
    """Renders the CRAG execution trace as a connected step pipeline.

    is_complete=False: this turn is still streaming — the most recent step pulses to show it's active.
    is_complete=True: the turn is finished (or being redrawn from history) — every step is static/done,
    nothing should keep animating.
    """
    if not node_history:
        container.markdown(
            f'<div class="pipeline-wrap"><span class="pipe-idle">{icon("clock", 14)} Awaiting query…</span></div>',
            unsafe_allow_html=True,
        )
        return

    steps_html = ""
    for i, n in enumerate(node_history):
        is_last = i == len(node_history) - 1
        state_class = "step-active" if (is_last and not is_complete) else "step-done"
        node_glyph = icon("node", 10)
        safe_label = html_lib.escape(n.replace("_", " ").title())
        steps_html += (
            f'<div class="pipe-step {state_class}">'
            f'<span>{node_glyph}</span><span>{safe_label}</span></div>'
        )
        if not is_last:
            steps_html += '<div class="pipe-arrow">›</div>'

    if grade_verdict is None and not is_complete:
        verdict_html = (
            f'<div class="verdict-row"><span class="verdict-badge v-eval">'
            f'{icon("clock", 13)} Evaluating context…</span></div>'
        )
    elif grade_verdict is None:
        verdict_html = ""
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
    cards = []
    for src in sources:
        raw_content = src.get("snippet") or src.get("content") or src.get("text") or "No text available"
        raw_page = src.get("page", "N/A")
        raw_chunk_id = src.get("chunk_id", "manual-excerpt")

        content = html_lib.escape(str(raw_content)).replace("\n", "<br>")
        page = html_lib.escape(str(raw_page))
        chunk_id = html_lib.escape(str(raw_chunk_id))

        card_html = (
            '<div class="citation-card">'
            '<div class="cite-head">'
            f'<span class="badge-page">{icon("book", 12)} Page {page}</span>'
            f'<span class="chunk-id">{chunk_id}</span>'
            '</div>'
            '<hr class="cite-divider">'
            f'{content}'
            '</div>'
        )
        cards.append(card_html)
    return '<div class="citation-grid">' + "".join(cards) + '</div>'


def render_citations(container, sources, title, expanded=False):
    if not sources:
        return
    with container.expander(title, expanded=expanded):
        st.markdown(build_citation_grid_html(sources), unsafe_allow_html=True)


try:
    health = httpx.get(f"{API_URL}/health", timeout=2.0)
    api_online = health.status_code == 200
except Exception:
    api_online = False

ensure_conversation_state()
active_conv = st.session_state.conversations[st.session_state.active_conversation_id]


with st.sidebar:
    st.markdown(
        f'<div class="brand-row">{icon("brand", 26, "#7fb4ff")}'
        f'<div><div class="brand-name">{APP_SHORT_NAME}</div>'
        f'<div class="brand-sub">{APP_TAGLINE}</div></div></div>',
        unsafe_allow_html=True,
    )
    dot_class = "dot-online" if api_online else "dot-offline"
    status_text = "Connected" if api_online else "Offline — run docker compose"
    st.markdown(
        f'<div class="conv-status-line"><span class="dot {dot_class}"></span>{status_text}</div>',
        unsafe_allow_html=True,
    )

    if st.button("+  New chat", use_container_width=True, key="new_chat_btn"):
        if active_conv["messages"] or active_conv["title"] != "New chat":
            create_new_conversation()
        st.rerun()

    st.markdown('<div class="side-section-label">Recent</div>', unsafe_allow_html=True)

    for cid in st.session_state.conversation_order:
        conv = st.session_state.conversations[cid]
        if not conv["messages"] and conv["title"] == "New chat":
            continue 
        is_active = cid == st.session_state.active_conversation_id
        title_display = conv["title"]
        if len(title_display) > 28:
            title_display = title_display[:27] + "…"

        row_key = f"convrow-active-{cid}" if is_active else f"convrow-{cid}"
        menu_open_key = f"menu_open_{cid}"
        renaming_key = f"renaming_{cid}"
        with st.container(key=row_key):
            row_cols = st.columns([0.82, 0.18])
            with row_cols[0]:
                if st.button(title_display, key=f"conv_select_{cid}", use_container_width=True):
                    st.session_state.active_conversation_id = cid
                    st.rerun()
            with row_cols[1]:
                if st.button("⋯", key=f"menu_toggle_{cid}", use_container_width=True):
                    st.session_state[menu_open_key] = not st.session_state.get(menu_open_key, False)

            if st.session_state.get(menu_open_key):
                with st.container(border=True):
                    if st.session_state.get(renaming_key):
                        new_title = st.text_input(
                            "Rename chat", value=conv["title"], key=f"rename_input_{cid}",
                            label_visibility="collapsed",
                        )
                        save_c, cancel_c = st.columns(2)
                        with save_c:
                            if st.button("Save", key=f"rename_save_{cid}", use_container_width=True):
                                rename_conversation(cid, new_title)
                                st.session_state[renaming_key] = False
                                st.session_state[menu_open_key] = False
                                st.rerun()
                        with cancel_c:
                            if st.button("Cancel", key=f"rename_cancel_{cid}", use_container_width=True):
                                st.session_state[renaming_key] = False
                                st.session_state[menu_open_key] = False
                                st.rerun()
                    else:
                        menu_c1, menu_c2 = st.columns(2)

                        with menu_c1:
                            if st.button(
                                "Rename",
                                key=f"rename_open_{cid}",
                                use_container_width=True,
                            ):
                                st.session_state[renaming_key] = True
                                st.rerun()

                        with menu_c2:
                            if st.button(
                                "Delete",
                                key=f"delete_{cid}",
                                use_container_width=True,
                            ):
                                delete_conversation(cid)
                                st.session_state[menu_open_key] = False
                                st.rerun()


    st.markdown(f"""
    <div class="side-card">
        <h4>CRAG Pipeline Legend</h4>
        <span class="verdict-badge v-correct" style="margin-bottom:6px;">{icon('check-circle', 12)} CORRECT</span> High relevant <br><br>
        <span class="verdict-badge v-ambiguous" style="margin-bottom:6px;">{icon('alert-triangle', 12)} AMBIGUOUS</span> Partial relevant<br><br>
        <span class="verdict-badge v-incorrect" style="margin-bottom:6px;">{icon('x-circle', 12)} REJECTED</span> No relevant
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Roadmap"):
        st.caption("v1.1.0 (planned): multi-turn conversational memory across the CRAG pipeline, so follow-up questions reuse prior context instead of running as isolated single-turn queries.")

    if st.button("Clear conversation", use_container_width=True):
        active_conv["messages"] = []
        st.rerun()


if "queued_prompt" not in st.session_state:
    st.session_state.queued_prompt = None

if not active_conv["messages"]:
    st.markdown(f"""
    <div class="hero-box">
        <div class="hero-icon">{icon('brand', 40, '#7fb4ff')}</div>
        <div class="hero-title">Describe a fault, or paste an Event Code</div>
        <div class="hero-sub">The agent retrieves from the IRC5 troubleshooting manual, grades relevance,
        and only answers when the evidence is grounded. Type a query below, or tap
        "Try an example" for a benchmark case</div>
    </div>
    """, unsafe_allow_html=True)

if "suggest_open" not in st.session_state:
    st.session_state["suggest_open"] = False

for i, msg in enumerate(active_conv["messages"]):
    if msg["role"] == "user":
        render_user_turn(msg["content"])
        continue
    with st.container(border=True):
        if msg.get("node_history"):
            hist_pipeline_box = st.empty()
            render_pipeline(
                hist_pipeline_box,
                msg.get("node_history", []),
                msg.get("grade_verdict"),
                msg.get("relevant_count", 0),
                msg.get("retrieved_count", 0),
                is_complete=True,
            )
        st.markdown(msg["content"])
        if msg.get("sources"):
            render_citations(st, msg["sources"], f"View {len(msg['sources'])} grounded manual citations")

with st.container(key="suggest-toggle-wrap"):
    if st.button(
        "Try an example",
        key="suggest_toggle",
        use_container_width=False,
    ):
        st.session_state["suggest_open"] = not st.session_state["suggest_open"]

if st.session_state["suggest_open"]:
    with st.container(border=True):
        for i, scenario_text in enumerate(PRESET_SCENARIOS):
            if st.button(
                scenario_text,
                key=f"suggest_{i}",
                use_container_width=True,
            ):
                st.session_state["queued_prompt"] = scenario_text
                st.session_state["suggest_open"] = False
                st.rerun()

user_query = st.chat_input("Enter fault description or event code...", key="main_chat_input")

if user_query:
    active_prompt = user_query
elif st.session_state.queued_prompt:
    active_prompt = st.session_state.queued_prompt
    st.session_state.queued_prompt = None
else:
    active_prompt = None


if active_prompt:
    if not active_conv["messages"] and active_conv["title"] == "New chat":
        auto_title = active_prompt.strip()
        active_conv["title"] = (auto_title[:40] + "…") if len(auto_title) > 40 else auto_title

    active_conv["messages"].append({"role": "user", "content": active_prompt})
    render_user_turn(active_prompt)

    node_history = []
    grade_verdict = None
    relevant_count = 0
    retrieved_count = 0
    accumulated_text = ""
    final_sources = []
    event_count = 0 

    with st.container(border=True):
        pipeline_box = st.empty()
        generation_box = st.empty()
        citations_box = st.empty()

        render_pipeline(pipeline_box, node_history, grade_verdict, relevant_count, retrieved_count)
        request_rejected = False
        rejection_message = None
        try:
            with (
                httpx.Client(timeout=90.0) as client,
                connect_sse(
                    client, "POST", f"{API_URL}/diagnose/stream", json={"query": active_prompt}
                ) as sse_stream,
            ):
                    response = sse_stream.response
                    if response.status_code >= 400:
                        request_rejected = True
                        try:
                            error_data = response.json()
                            detail = error_data.get("detail", "Invalid request.")

                            if isinstance(detail, list) and detail:
                                detail = detail[0].get("msg", "Invalid request.")

                            rejection_message = (
                                "Invalid query. Please enter a meaningful "
                                "fault description or Event Code."
                            )

                        except Exception:
                            rejection_message = (
                                "Invalid query. Please enter a meaningful "
                                "fault description or Event Code."
                            )
                    else:
                        for event in sse_stream.iter_sse():
                            event_count += 1

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

            render_pipeline(pipeline_box, node_history, grade_verdict, relevant_count, retrieved_count, is_complete=True)
            render_citations(citations_box, final_sources, "Grounded manual excerpts & citations", expanded=True)

            if not request_rejected and not accumulated_text and not event_count:
                st.warning(
                    "The backend returned no events for this query. If this only happens on the "
                    "2nd+ message, check that `/diagnose/stream` starts a fresh graph run per "
                    "request rather than reusing state (e.g. a shared checkpointer/thread_id) "
                    "from the previous turn."
                )
            elif not request_rejected and not accumulated_text:
                st.warning("The pipeline ran but produced no answer text for this query.")
            
            if rejection_message:
                active_conv["messages"].append({
                    "role": "assistant",
                    "content": rejection_message,
                    "sources": [],
                    "node_history": [],
                    "grade_verdict": None,
                    "relevant_count": 0,
                    "retrieved_count": 0,
                })
                st.rerun()

            elif accumulated_text:
                active_conv["messages"].append({
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
            render_pipeline(pipeline_box, node_history, grade_verdict, relevant_count, retrieved_count, is_complete=True)
            st.error("Inference error — see full traceback below.")
            st.exception(err)