# pages/00_Hub.py
import sys, pathlib, importlib
import streamlit as st
from uuid import uuid4 


repo_root = pathlib.Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from theme_mod import apply_theme

st.set_page_config(page_title="Oraculum", layout="wide")



if "history" not in st.session_state:
    st.session_state.history = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "thread_id_pdf" not in st.session_state:               
    st.session_state.thread_id_pdf = str(uuid4())


if "convos" not in st.session_state:
    cid = str(uuid4())
    st.session_state.convos = {cid: {"title": "New chat", "messages": []}}
    st.session_state.current_cid = cid
    
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

# ---------- Chat History----------
with st.sidebar:
    if st.button("╋ New chat", use_container_width=True):
        cid = str(uuid4())
        st.session_state.convos[cid] = {"title": "New chat", "messages": []}
        st.session_state.current_cid = cid
        st.rerun()

    ids = list(st.session_state.convos.keys())
    titles = [st.session_state.convos[i]["title"] for i in ids]
    pick = st.radio("Chats", options=ids, format_func=lambda x: st.session_state.convos[x]["title"])
    st.session_state.current_cid = pick

cur = st.session_state.convos[st.session_state.current_cid]
messages = cur["messages"]


# ===========================
# CHAT AREA (compact welcome + history)
# ===========================
# if "messages" not in st.session_state:
#     st.session_state.messages = []  # list[{"role": "user"|"assistant", "content": str}]
# if "greeted" not in st.session_state:
#     st.session_state.greeted = False

# show a small one-time welcome *bubble* when conversation is empty
if not messages:  # first time in this chat
    with st.chat_message("assistant"):
        st.write("Hi, welcome! I’m a financial assistant with access to a list of companies that can be retrieved from Companies House. "
                 "Do you want me to list all companies I already have, add a new company, or answer any question about a specific company?")

# render history
for msg in messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# one input at the bottom (single source of truth)
prefill = st.session_state.pop("prefill", "")



typed = st.chat_input("Type your message here...", key="main_chat")
query = typed or prefill  # if user didn't type anything, use the prefill
# Make sure query is always a string, not None
# if injected:
#     query = injected
# elif typed:
#     query = typed
# else:
#     query = None


# ===========================
# IMPORT SUBPAGES (functions only; no UI)
# ===========================
chat_module     = importlib.import_module("pages.chat_with_GPT5")
profile_module  = importlib.import_module("pages.company_profile")          
chouse_module   = importlib.import_module("pages.add_from_company_house") 
web_module      = importlib.import_module("pages.web_search")
pdf_module      = importlib.import_module("pages.PDF")
dev_module      = importlib.import_module("pages.dev_mode")
auto_module     = importlib.import_module("pages.automations")

# ===========================
# ROUTE THE MESSAGE + APPEND REPLY
# ===========================
if query:
    messages.append({"role": "user", "content": query})

    # auto-title if still "New chat"
    if cur["title"] == "New chat":
        cur["title"] = query[:30] + ("…" if len(query) > 30 else "")

    answer = None
    view = st.session_state.active_tile

    if view == "chat":
        if not chat_module.check_actions(query, chat_module.client, chat_module.AOAI_DEPLOYMENT,
                                         k=50, ts=35, cs=8000, model_profile="gpt-5"):
            answer = chat_module.stream_answer(query)

    elif view == "web":
        answer = web_module.answer_web(query)

    elif view == "pdf":
        if st.session_state.get("graph"):
            state = {"messages": [{"role": "user", "content": query}]}
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
        if not dev_module.check_actions(query, dev_module.client, dev_module.AOAI_DEPLOYMENT,
                                        k=100, ts=200, cs=8000, model_profile="gpt-5"):
            answer = dev_module.stream_answer(query) or "…"

    elif view == "auto":
        answer = auto_module.create_automation(query)

    elif view == "profile":
        answer = profile_module.stream_answer(query)

    elif view == "chouse":
        answer = chouse_module.add_company(query)

    else:
        answer = "⚠️ Select a tile first."

    if answer is None:
        answer = "OK."
    messages.append({"role": "assistant", "content": answer})
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

# ---------- QUICK ACTIONS ----------
if "prefill" not in st.session_state:
    st.session_state.prefill = ""

st.markdown("**Quick actions**")
qa_cols = st.columns(6)

with qa_cols[0]:
    if st.button("🔵 Extract Key Figures", key="qa_figs"):
        st.session_state.prefill = (
            "Can you extract the key financial figures from the uploaded PDF, "
            "including Revenue, Gross Profit, Operating Income, Net Income, EPS, "
            "Cash Flow, Total Assets, and Liabilities?"
        )

with qa_cols[1]:
    if st.button("📑 Summarize Overview", key="qa_overview"):
        st.session_state.prefill = (
            "Can you give me a concise business overview of the company from the PDF? "
            "Please include what the company does, main products/services, geographies, "
            "key business units, and strategy themes."
        )

with qa_cols[2]:
    if st.button("🗞️ Show Recent News", key="qa_news"):
        st.session_state.prefill = (
            "Can you show me recent news (last 90 days) about this company with dates, titles, "
            "short takeaways, and links if possible?"
        )

# --- Felipe’s future actions (not available now) ---
with qa_cols[3]:
    if st.button("📋 List Companies", key="qa_list_companies"):
        st.info("📋 List Companies — not available now")

with qa_cols[4]:
    if st.button("✚ Add Company", key="qa_add_company"):
        st.info("✚ Add Company — not available now")

with qa_cols[5]:
    if st.button("⚙️ Create Profile", key="qa_create_profile"):
        st.info("⚙️ Create Profile — not available now")