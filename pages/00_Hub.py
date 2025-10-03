# pages/00_Hub.py
import sys, pathlib, importlib
import streamlit as st
from uuid import uuid4 

if "history" not in st.session_state:
    st.session_state.history = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "thread_id_pdf" not in st.session_state:               
    st.session_state.thread_id_pdf = str(uuid4())

# ---------- read tile clicks via query param (no new tab) ----------
params = st.query_params
clicked = params.get("tile")
if clicked:
    st.session_state.active_tile = clicked[0] if isinstance(clicked, list) else clicked
    # clear param so the URL stays clean on next rerun
    st.query_params.clear()

# ---------- make repo root importable for submodules (engines, rags, etc.) ----------
repo_root = pathlib.Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from theme_mod import apply_theme

# ---------- page / theme ----------
apply_theme("light")
st.set_page_config(page_title="Oraculum", layout="wide")

# ---------- default route: open chat ----------
if "active_tile" not in st.session_state or not st.session_state.active_tile:
    st.session_state.active_tile = "chat"  # default landing

# ---------- small CSS polish ----------
st.markdown("""
<style>
.block-container {max-width: 1320px; padding-left: 1rem; padding-right: 1rem;}
[data-testid="stChatMessage"] { margin-bottom: .5rem; }  /* tighter chat spacing */
</style>
""", unsafe_allow_html=True)

st.title("Oraculum")
st.caption("What I can do")

# ---------- tile helper (the tile itself is the click target) ----------
def tile(title: str, subtitle: str, icon_svg: str, key: str):
    st.markdown(
        f"""
        <a href="?tile={key}" target="_self" style="text-decoration:none;">
          <div style="
              background:#F0F2F6; border-radius:10px; padding:14px;
              min-height:90px; display:flex; align-items:center; gap:12px;
              margin-bottom:14px; cursor:pointer;">
            <div style="width:22px;height:22px;display:flex;align-items:center;justify-content:center;">
              {icon_svg}
            </div>
            <div>
              <div style="font-weight:600; font-size:15px; color:#000;">{title}</div>
              <div style="font-size:13px; color:#555;">{subtitle}</div>
            </div>
          </div>
        </a>
        """,
        unsafe_allow_html=True
    )

# ---------- icons ----------
def ic_search():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="7" stroke="#2563EB" stroke-width="1.6"/><path d="M20 20l-3.5-3.5" stroke="#2563EB" stroke-width="1.6" stroke-linecap="round"/></svg>'

def ic_pdf():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M7 3h7l5 5v13H7z" stroke="#2563EB" stroke-width="1.6"/><path d="M14 3v5h5" stroke="#2563EB" stroke-width="1.6"/></svg>'

def ic_dev():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M8 9l-4 3 4 3M16 9l4 3-4 3" stroke="#2563EB" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def ic_auto():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3" stroke="#2563EB" stroke-width="1.6"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2" stroke="#2563EB" stroke-width="1.6" stroke-linecap="round"/></svg>'

# ---------- ROW: four tiles ----------
c1, c2, c3, c4 = st.columns(4, gap="small")
with c1: tile("Chat with Your PDF", "Upload reports and analyze", ic_pdf(), "pdf")
with c2: tile("Web Search", "Search the web and summarize", ic_search(), "web")
with c3: tile("Developer Mode", "Access advanced API features", ic_dev(), "dev")
with c4: tile("Create Automation", "Set up automated workflows", ic_auto(), "auto")

# ===========================
# CHAT AREA (compact welcome + history)
# ===========================
if "messages" not in st.session_state:
    st.session_state.messages = []  # list[{"role": "user"|"assistant", "content": str}]
if "greeted" not in st.session_state:
    st.session_state.greeted = False

# show a small one-time welcome *bubble* when conversation is empty
if not st.session_state.messages and not st.session_state.greeted:
    with st.chat_message("assistant"):
        st.write(
            "Hi, welcome! I’m a financial assistant with access to a list of companies that can be retrieved from Companies House. "
            "Do you want me to list all companies I already have, add a new company, or answer any question about a specific company?"
        )
    st.session_state.greeted = True

# render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# one input at the bottom (single source of truth)
typed = st.chat_input("Type your message here...", key="main_chat")
injected = st.session_state.pop("pending_prompt", None)
query = injected or typed


# ===========================
# IMPORT SUBPAGES (functions only; no UI)
# ===========================
chat_module     = importlib.import_module("pages.chat_with_GPT5")
profile_module  = importlib.import_module("pages.company_profile")          # used only if you route to "profile" later
chouse_module   = importlib.import_module("pages.add_from_company_house")   # used only if you route to "chouse" later
web_module      = importlib.import_module("pages.web_search")
pdf_module      = importlib.import_module("pages.PDF")
dev_module      = importlib.import_module("pages.dev_mode")
auto_module     = importlib.import_module("pages.automations")

# ===========================
# ROUTE THE MESSAGE + APPEND REPLY
# ===========================
if query:
    st.session_state.messages.append({"role": "user", "content": query})

    answer = None
    view = st.session_state.active_tile

    if view == "chat":
        # default screen — call your chat functions if you want (or leave as basic echo)
        if not chat_module.check_actions(typed, chat_module.client, chat_module.AOAI_DEPLOYMENT,
                                         k=50, ts=35, cs=8000, model_profile="gpt-5"):
            answer = chat_module.stream_answer(typed)

    elif view == "web":
        answer = web_module.answer_web(typed)

    elif view == "pdf":
        # requires OCR graph to be built (see PDF sidebar below)
        if st.session_state.get("graph"):
            state = {"messages": [{"role": "user", "content": typed}]}
            out = st.session_state.graph.invoke(
                state,
                config={"configurable": {
                    "thread_id": st.session_state.thread_id_pdf,
                    "checkpoint_ns": "pdf"
                    }}
                )
            answer = out["messages"][-1].content
        else:
            answer = "⚠️ Please upload a PDF and build index first."

    elif view == "dev":
        # dev_mode has tool routing; stream_answer writes to page; still add a stub
        if not dev_module.check_actions(typed, dev_module.client, dev_module.AOAI_DEPLOYMENT,
                                        k=100, ts=200, cs=8000, model_profile="gpt-5"):
            answer = dev_module.stream_answer(typed) or "…"

    elif view == "auto":
        answer = auto_module.create_automation(typed)

    elif view == "profile":
        answer = profile_module.stream_answer(typed)

    elif view == "chouse":
        answer = chouse_module.add_company(typed)

    else:
        answer = "⚠️ Select a tile first."

    if answer is None:
        answer = "OK."
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

# ===========================
# PDF CONTROLS (sidebar only when PDF tile is active)
# ===========================
if st.session_state.get("active_tile") == "pdf":
    with st.sidebar:
        st.markdown("### Documents")
        pdf_files = st.file_uploader("Upload PDF(s)", type=["pdf"], accept_multiple_files=True, key="hub_pdf_uploader")
        build = st.button("🔎︎ Build Index (OCR)", use_container_width=True, key="hub_pdf_build")

    if build:
        if not pdf_files:
            st.warning("Upload at least one PDF.")
        else:
            files_bytes = tuple(f.getvalue() for f in pdf_files)
            files_names = tuple(f.name for f in pdf_files)
            engine, timings = pdf_module.ocr_engine_cached_multi(files_bytes, files_names)
            st.session_state.ocr_engine = engine
            st.session_state.ocr_timings = timings
            st.session_state.graph = pdf_module.build_graph(engine)
            st.success("✅ OCR index ready — ask your question below.")

# ---------- QUICK ACTIONS  ----------
PROMPT_KEY_FIGURES = (
    "Extract key financial figures from the current context. Prefer the uploaded PDF "
    "(if indexed) and cite page numbers. Return a compact table with columns:\n"
    "Metric | Value | Unit | Period | Page\n"
    "Cover at least: Revenue, Gross Profit, Operating Income (EBIT), Net Income, EPS, "
    "Cash from Operations, CapEx, Free Cash Flow, Total Assets, Total Liabilities, "
    "Shareholders’ Equity. If a number isn’t found, write '—'."
)

PROMPT_BUSINESS_OVERVIEW = (
    "Give a concise business overview of the company using the current context "
    "(prefer PDF if present). Bullet points only (5–8 bullets). Include: what the "
    "company does, key products/services, geographies, customer segments, main "
    "business units, leadership highlights, strategy themes, and notable risks. "
    "Cite page numbers where possible."
)

PROMPT_RECENT_NEWS = (
    "Find recent news (last 90 days) about the company. Return 5 bullets in the form:\n"
    "[Date] Title — one-line takeaway (include link if available)\n"
    "Then add a 2–3 sentence summary of the overall theme. Prefer official sources, "
    "filings, and major outlets."
)

st.markdown("**Quick actions**")
qa_cols = st.columns(6)

with qa_cols[0]:
    if st.button("🔵 Extract Key Figures", key="qa_figs"):
        st.session_state.pending_prompt = PROMPT_KEY_FIGURES
        st.rerun()

with qa_cols[1]:
    if st.button("📑 Summarize Overview", key="qa_overview"):
        st.session_state.pending_prompt = PROMPT_BUSINESS_OVERVIEW
        st.rerun()

with qa_cols[2]:
    if st.button("🗞️ Show Recent News", key="qa_news"):
        st.session_state.pending_prompt = PROMPT_RECENT_NEWS
        st.rerun()

# Stubs / inactive for now (Felipe will wire later)
with qa_cols[3]:
    if st.button("📋 List Companies", key="qa_list_companies"):
        st.toast("List Companies — coming soon", icon="🛠️")

with qa_cols[4]:
    if st.button("✚ Add Company", key="qa_add_company"):
        st.toast("Add Company — coming soon", icon="🛠️")

with qa_cols[5]:
    if st.button("⚙️ Create Profile", key="qa_create_profile"):
        st.toast("Create Profile — coming soon", icon="🛠️")