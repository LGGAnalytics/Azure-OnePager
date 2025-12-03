# ===================== PAGE CONFIG ===============
import importlib
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Final_theme import apply_theme
import streamlit as st
from dotenv import load_dotenv, find_dotenv

from uuid import uuid4 
from azure.blob_functions import get_companies
from pages.design.dialogues import *
import difflib


# ===================== Variables

load_dotenv(find_dotenv(), override=True)
OPENAI_API_KEY  = os.getenv("FELIPE_OPENAI_API_KEY")

if "greeted" not in st.session_state:
    st.session_state.greeted = False

if "view" not in st.session_state:
    st.session_state.view = "home"

if "theme" not in st.session_state:
    st.session_state.theme = "light"  # or "dark" as default

if "convos" not in st.session_state:
    cid = str(uuid4())
    st.session_state.convos = {cid: {"title": "New chat", "messages": []}}
    st.session_state.current_cid = cid

if "history" not in st.session_state:
    st.session_state.history = []

if "pdf_mod" not in st.session_state:
    st.session_state.pdf_mod = False


if "pdf" not in st.session_state:
    st.session_state.pdf = False

    

LOGO = '/Users/felipesilverio/Documents/GitHub/Azure-OnePager/logo_teneo.png'

# =====================  Design
# apply_theme(st.session_state.theme)

st.logo(
    str(LOGO),                 # main logo
    size="large",             # "small" | "medium" | "large"
)

output_placeholder = st.empty()

COMPANIES = [
    "JAMES DONALDSON GROUP LTD",
    "RADLEY + CO. LIMITED",
    "SEAPORT TOPCO LIMITED",
    "ASCOT LLOYD LIMITED",
    "VITA (HOLDINGS) LIMITED",
]

def pick_company(user_text: str) -> str | None:
    _, names = get_companies()
    # normalize user input a bit
    cleaned = user_text.strip().upper()

    # try fuzzy match against the official list
    matches = difflib.get_close_matches(
        cleaned,
        names,
        n=1,          # only want the single best
        cutoff=0.6    # 0.0–1.0; raise this if you want to be stricter
    )

    if matches:
        return matches[0]  # this is the canonical company name
    return None

def go(view: str):
    st.session_state.view = view
    st.session_state.websearch      = (view == "web")
    st.session_state.mixsource      = (view == "mix")
    st.session_state.pdf            = (view == "pdf")
    st.session_state.companieshouse = (view == "companies")

    if st.session_state.websearch:
        st.session_state.history.append({"a": greeting_2})
        st.rerun()
    elif st.session_state.mixsource:
        name_map, names = get_companies()
        st.session_state.history.append({"a": f"{greeting_3}\n\n Companies Available: \n" + "\n".join(f"- {n}" for n in names)})
        st.rerun()
    elif st.session_state.pdf:
        pass
    elif st.session_state.companieshouse:
        _ , names = get_companies()
        st.session_state.history.append({"a":f"{greeting_1}\n\n" + "\n".join(f"- {n}" for n in names)})
        st.rerun()

if st.session_state.pdf:
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded_file:
        st.success(f"Uploaded: {uploaded_file.name}")

# =====================  MAIN PAGE ================


if st.session_state.view == "home":
    L, C, R = st.columns([0.25, 14, 0.25], gap="large")
    with C:
        st.markdown("<div class='home-wrap'>", unsafe_allow_html=True)
        st.markdown("<div class='hero-wrap'>", unsafe_allow_html=True)

        st.markdown("<h1 class='hero-title'>Welcome to Oraculum</h1>", unsafe_allow_html=True)
        st.markdown("<p class='hero-sub'>Your AI assistant for financial documents and company research, Please select a mode to get started.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    # Cards row (clickable; no business logic yet)
        c1, c2, c3, c4 = st.columns([0.5, 0.5, 0.5, 0.5], gap="medium")

        with c1:
            st.button("**Research with Companies House**  \n_Access comprehensive company data from Companies House. Search for companies, view financial filings, and analyze company structures. Perfect for due diligence and company research._", 
                         icon=":material/domain:", key="open_companies", use_container_width=True, on_click=go, args=("companies",))
        with c2:
            st.button("**Research with Web Search**  \n_Leverage real-time web search capabilities to find the latest news, market data, and insights. Stay updated with current information about companies and industries._", 
                         icon=":material/language:", key="open_web", use_container_width=True, on_click=go, args=("web",))
        with c3:
            st.button("**Research with Companies House & Web Search**  \n_Extract key figures, generate summaries, and identify important metrics from financial reports, contracts, and other documents._", 
                         icon=":material/picture_as_pdf:", key="mix", use_container_width=True, on_click=go, args=("mix",))
        with c4:
            st.button("**Talk with Your PDF**  \n_Upload and analyze PDF documents with advanced OCR._", 
                         icon=":material/picture_as_pdf:", key="open_pdf", use_container_width=True, on_click=go, args=("pdf",))

        st.markdown("</div>", unsafe_allow_html=True)


# apply_theme(st.session_state.theme)

# ====================  SIDEBAR ================
if "theme" not in st.session_state:
    st.session_state.theme = "light"  # or "dark" as default
apply_theme(st.session_state.theme)


with st.sidebar:
    
     # ---- Theme toggle  ----
    mode = st.session_state.theme
    label = "Light Mode" if mode == "dark" else "⏾ Dark Mode"
    if st.button(label, use_container_width=True, key="theme_toggle"):
        st.session_state.theme = "light" if mode == "dark" else "dark"
        st.rerun()
    # ---- New Chat ----
    if st.session_state.get("view") != "home":
        if st.button("✚ New chat", use_container_width=True, key="new_chat"):
            cid = str(uuid4())
            st.session_state.convos[cid] = {"title": "New chat", "messages": []}
            st.session_state.current_cid = cid
            st.rerun()

        ids = list(st.session_state.convos.keys())
        pick = st.radio(
            "Chat History",
            options=ids,
            key="chat_history_radio",  # <-- important to avoid duplicate-ID error
            format_func=lambda x: st.session_state.convos[x]["title"],
        )
        st.session_state.current_cid = pick


    # Each button uses Streamlit’s native Material icon support
    st.markdown("### Select Mode")

    # Companies House (PDF) mode
    if st.button("Research with Companies House PDF", icon=":material/domain:", use_container_width=True):
        st.session_state.websearch = False
        st.session_state.mixsource = False
        st.session_state.pdf = False
        st.session_state.companieshouse = True
        
        for k in ["history", "messages", "pending_prompt"]:
            st.session_state.pop(k, None)
        if "history" not in st.session_state:
            st.session_state.history = []

        _ , names = get_companies()
        st.session_state.history.append({"a":f"{greeting_1}\n\n" + "\n".join(f"- {n}" for n in names)})
        st.rerun()

    # Web Search mode
    if st.button("Research with Web Search", icon=":material/language:", use_container_width=True, key="mode_web"):
        st.session_state.websearch = False
        st.session_state.mixsource = False
        st.session_state.pdf = False
        st.session_state.companieshouse = False
        for k in ["history", "messages", "pending_prompt"]:
            st.session_state.pop(k, None)
        if "history" not in st.session_state:
            st.session_state.history = []
        st.session_state.history.append({"a": greeting_2})
        st.session_state.websearch = True
        st.rerun()

    # Both (Web + CH) mode
    if st.button("Research with Companies House and Web Search", icon=":material/picture_as_pdf:", use_container_width=True, key="mode_both"):
        st.session_state.websearch = False
        st.session_state.mixsource = True
        st.session_state.pdf = False
        st.session_state.companieshouse = False
        for k in ["history", "messages", "pending_prompt"]:
            st.session_state.pop(k, None)
        if "history" not in st.session_state:
            st.session_state.history = []
        name_map, names = get_companies()
        st.session_state.history.append({"a": f"{greeting_3}\n\n Companies Available: \n" + "\n".join(f"- {n}" for n in names)})
        st.rerun()

    # Both PDF mode
    if st.button("Talk with Your PDF", icon=":material/picture_as_pdf:", use_container_width=True, key="mode_pdf"):
        st.session_state.websearch = False
        st.session_state.mixsource = False
        st.session_state.pdf = True
        st.session_state.companieshouse = False
        # st.session_state.view = "pdf"
        for k in ["history", "messages", "pending_prompt"]:
            st.session_state.pop(k, None)
        if "history" not in st.session_state:
            st.session_state.history = []
        st.session_state.history.append({"a": "Upload your PDF and have a chat!"})
        
        st.rerun()


# ====================  COMPANIES HOUSE PAGE ================

if st.session_state.view != "home":
    header_map = {
        "companies": ("Companies House Research", "Search and manage company data."),
        "pdf": ("PDF Analysis", "Upload and analyze PDFs."),
        "web": ("Research with Web Search", "Find latest news and insights."),
        "combo": ("Research with Companies House and Web Search", "Use both ingested filings and the live web.")
    }

    # NEW: resolve mode from flags first, then fallback to view
    mode = ("web" if st.session_state.get("websearch") else
            "combo" if st.session_state.get("mixsource") else
            "companies" if st.session_state.get("companieshouse") else
            st.session_state.view)

    title, subtitle = header_map.get(
        mode, 
        ("Companies House Research", "Search and manage company data.")
    )

    st.markdown(
        f"<h2 class='page-h2'>{title}</h2><p class='page-sub'>{subtitle}</p>",
        unsafe_allow_html=True
    )
    for turn in st.session_state.history:
        if turn.get("q"):  
            with st.chat_message("user"):
                st.write(turn["q"])
        with st.chat_message("assistant"):
            st.write(turn["a"])
    
    placeholder = (
        "Ask a question about your PDFs…" 
        if st.session_state.pdf_mod 
        else "Ask about the ingested PDFs…"
    )

    typed = st.chat_input(placeholder)
    pending = st.session_state.pop("pending_prompt", None)
    prompt = typed or pending

    if not st.session_state.company:
        company = pick_company(prompt)

    if st.session_state.companieshouse:
            qa1, qa2, qa3 = st.columns([0.5,0.5,0.5])
            with qa1:
                if st.button("List Companies", use_container_width=True, key="list_companies_btn"):
                    _, names = get_companies()
                    answer_text = f"{companies_available}\n\n" + "\n".join(f"- {n}" for n in names)
                    st.session_state.history.append({"q": "Which companies are available?", "a": answer_text})
                    st.rerun()
            with qa2:
                if st.button("Add New from CH", use_container_width=True, key="add_company_btn"):
                    answer_text = f"{add_company_tutorial_1}\n\n"
                    st.session_state.history.append({"q": "How do I add new companies?", "a": answer_text})
                    st.rerun()
            with qa3:
                if st.button("Create Company Profile", use_container_width=True, key="create_profile_btn"):
                    answer_text = f"{profile_tutorial_1}\n\n"
                    st.session_state.history.append({"q": "How do I ask for a Company Profile?", "a": answer_text})
                    st.rerun()
else:
    # Home view → no chat shown
    prompt = None


if prompt:
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):

        # Try tool routing first
        model_profile = "gpt-5" #if model_profile_mod else "o3"

        st.write("Please select a company in the sidebar before asking a question.")
            
if not st.session_state.greeted and st.session_state.view == "companies":
    _, names = get_companies()
    st.session_state.history.append({
        "a": f"{greeting_1}\n\n" + "\n".join(f"- {n}" for n in names)
    })
    st.session_state.greeted = True