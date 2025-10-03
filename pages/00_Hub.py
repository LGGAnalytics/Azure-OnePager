import sys, pathlib
repo_root = pathlib.Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import streamlit as st
st.set_page_config(page_title="Oraculum", layout="wide")  # <-- move this to the very top
from theme_mod import apply_theme
apply_theme("light")

if "history" not in st.session_state:
    st.session_state.history = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# --- handle tile clicks via query param ---
params = st.query_params
clicked = params.get("tile")
if clicked:
    # if it's a list, take the first value
    st.session_state.active_tile = clicked[0] if isinstance(clicked, list) else clicked
    # optional: clear the param so URL stays clean on next rerun
    st.query_params.clear()


# Ensure repo root is importable



def require(mod, fn_name):
    if not hasattr(mod, fn_name):
        st.warning(f"Missing function `{fn_name}` in `{mod.__name__}`")
        return False
    return True





# --- widen content so 4+3 tiles have breathing room (keeps sidebar space) ---
st.markdown("""
<style>
/* Streamlit has changed selectors across versions; cover all common cases */
.block-container,
[data-testid="stAppViewContainer"] .main .block-container,
.appview-container .main .block-container {
  max-width: 1320px;   /* try 1240–1360 to taste */
  padding-left: 1rem;
  padding-right: 1rem;
}

/* Slightly taller tiles so icon + text breathe */
.tile .stButton>button { height: 82px !important; }
</style>
""", unsafe_allow_html=True)

st.title("Oraculum")
st.caption("What I can do")

def tile(title, subtitle, icon, key):
    st.markdown(
        f"""
        <a href="?tile={key}" target="_self" style="text-decoration:none;">
          <div style="
              background:#F0F2F6;
              border-radius:10px;
              padding:14px;
              min-height:90px;
              display:flex;
              align-items:center;
              gap:12px;
              margin-bottom:14px;
              cursor:pointer;">
            <div style="width:22px;height:22px;display:flex;align-items:center;justify-content:center;">
              {icon}
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



# ---- ICONS (blue emojis now, can swap to FontAwesome later) ----
def ic_chat():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M4 6h16v9H7l-3 3V6z" stroke="#2563EB" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def ic_profile():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 12a5 5 0 1 0-5-5 5 5 0 0 0 5 5Zm7 9v-1a6 6 0 0 0-6-6H11a6 6 0 0 0-6 6v1" stroke="#2563EB" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def ic_house():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M3 10l9-7 9 7v9a2 2 0 0 1-2 2h-3v-6H8v6H5a2 2 0 0 1-2-2v-9z" stroke="#2563EB" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def ic_search():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="7" stroke="#2563EB" stroke-width="1.6"/><path d="M20 20l-3.5-3.5" stroke="#2563EB" stroke-width="1.6" stroke-linecap="round"/></svg>'

def ic_pdf():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M7 3h7l5 5v13H7z" stroke="#2563EB" stroke-width="1.6"/><path d="M14 3v5h5" stroke="#2563EB" stroke-width="1.6"/></svg>'

def ic_dev():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M8 9l-4 3 4 3M16 9l4 3-4 3" stroke="#2563EB" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def ic_auto():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3" stroke="#2563EB" stroke-width="1.6"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2" stroke="#2563EB" stroke-width="1.6" stroke-linecap="round"/></svg>'



# ---- ROW 1: 4 tiles ----
c1, c2, c3, c4 = st.columns(4, gap="small")

with c1:
    tile("Chat with Your PDF", "Upload reports and analyze", ic_pdf(), "pdf")

with c2:
    tile("Web Search", "Search the web and summarize", ic_search(), "web")

with c3:
    tile("Developer Mode", "Access advanced API features", ic_dev(), "dev")

with c4:
    tile("Create Automation", "Set up automated workflows", ic_auto(), "auto")



# # ---- ROW 2: 3 tiles ----
# d1, d2, d3 = st.columns(3, gap="small")

# with d1:
#     tile("Chat with Your PDF", "Upload reports and analyze", ic_pdf(), "pdf")


# with d2:
#     tile("Developer Mode", "Access advanced API features", ic_dev(), "dev")


# with d3:
#     tile("Create Automation", "Set up automated workflows", ic_auto(), "auto")



# ---- CHAT AREA ----
st.markdown("### ")
chat_container = st.container()

with chat_container:
    st.markdown("""
    <div style="
        background-color:#F9FAFB;
        border-radius:12px;
        padding:18px;
        margin-top:12px;
        min-height:280px;">
        <p style="color:#111; font-size:14px;">Hi, welcome! I am a Financial Assistant with access to a list of companies that can be retrieved from Companies House or via a pdf! Do you want me to list all companies I already have? Add a new company? Or answer any question about a specific company?</p>
    </div>
    """, unsafe_allow_html=True)


# ---- QUICK ACTIONS ----
st.markdown(
    """
    <div style="display:flex; gap:10px; margin-top:10px; margin-bottom:10px;">
        <div style="background:#F3F4F6; border-radius:20px; padding:6px 14px; font-size:13px; cursor:pointer;">Extract Key Figures</div>
        <div style="background:#F3F4F6; border-radius:20px; padding:6px 14px; font-size:13px; cursor:pointer;">Summarize Overview</div>
        <div style="background:#F3F4F6; border-radius:20px; padding:6px 14px; font-size:13px; cursor:pointer;">Show Recent News</div>
    </div>
    """,
    unsafe_allow_html=True
)


# ---- INPUT BAR (final version with your airplane) ----
# st.markdown("""
# <div style="
#     display:flex;
#     align-items:center;
#     background:#F3F4F6;
#     border-radius:20px;
#     padding:6px 12px;
#     margin-top:14px;">
#     <input type="text" placeholder="Type your message here..." 
#         style="flex:1; border:none; background:transparent; outline:none;
#         font-size:14px; color:#111; opacity:0.7;">
#     <svg width="18" height="18" viewBox="0 0 24 24" fill="none" 
#         xmlns="http://www.w3.org/2000/svg" style="cursor:pointer; margin-left:6px;">
#         <path d="M2 21l21-9L2 3v7l15 2-15 2v7z" 
#             stroke="#2563EB" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
#     </svg>
# </div>
# """, unsafe_allow_html=True)

# ---- IMPORT PAGES ----
# ---- IMPORT PAGES ----
import sys, pathlib, importlib

# Ensure repo root is importable so "rag", "engines", etc. work in subpages
repo_root = pathlib.Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Import each page as a module and expose its helper functions
chat_module     = importlib.import_module("pages.chat_with_GPT5")
profile_module  = importlib.import_module("pages.company_profile")
chouse_module   = importlib.import_module("pages.add_from_company_house")
web_module      = importlib.import_module("pages.web_search")
pdf_module      = importlib.import_module("pages.PDF")
dev_module      = importlib.import_module("pages.dev_mode")
auto_module     = importlib.import_module("pages.automations")



if "active_tile" not in st.session_state or not st.session_state.active_tile:
    st.session_state.active_tile = "chat"   # default screen

typed = st.chat_input("Type your message here...", key="main_chat")

if typed:
    with st.chat_message("user"):
        st.write(typed)

    # Switch behavior depending on tile
    if st.session_state.active_tile == "chat":
        if not chat_module.check_actions(typed, chat_module.client, chat_module.AOAI_DEPLOYMENT,
                                         k=50, ts=35, cs=8000, model_profile="gpt-5"):
            ans = chat_module.stream_answer(typed)
            with st.chat_message("assistant"):
                st.write(ans)

    elif st.session_state.active_tile == "profile":
        ans = profile_module.stream_answer(typed)
        with st.chat_message("assistant"):
            st.write(ans)

    elif st.session_state.active_tile == "chouse":
        ans = chouse_module.add_company(typed)   # e.g. pass company number
        with st.chat_message("assistant"):
            st.write(ans)

    elif st.session_state.active_tile == "web":
        ans = web_module.answer_web(typed)
        with st.chat_message("assistant"):
            st.write(ans)

    elif st.session_state.active_tile == "pdf":
        if st.session_state.get("graph"):
            state = {"messages": [{"role": "user", "content": typed}]}
            out = st.session_state.graph.invoke(state)
            ans = out["messages"][-1].content
            with st.chat_message("assistant"):
                st.write(ans)
        else:
            with st.chat_message("assistant"):
                st.write("⚠️ Please upload a PDF and build index first.")

    elif st.session_state.active_tile == "dev":
        if not dev_module.check_actions(typed, dev_module.client, dev_module.AOAI_DEPLOYMENT,
                                        k=100, ts=200, cs=8000, model_profile="gpt-5"):
            dev_module.stream_answer(typed)

    elif st.session_state.active_tile == "auto":
        ans = auto_module.create_automation(typed)  # example stub
        with st.chat_message("assistant"):
            st.write(ans)

    else:
        with st.chat_message("assistant"):
            st.write("⚠️ Select a tile first.")


# ---- PDF CONTROLS (shown only when PDF tile is active) ----
if st.session_state.get("active_tile") == "pdf":
    with st.sidebar:
        st.markdown("### PDF")
        pdf_files = st.file_uploader("Upload PDF(s)", type=["pdf"], accept_multiple_files=True, key="hub_pdf_uploader")
        build = st.button("Build Index (OCR)", use_container_width=True, key="hub_pdf_build")

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
            st.success("OCR index ready. Ask a question below.")
