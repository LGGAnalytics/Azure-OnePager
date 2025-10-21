# ---------- PAGE CONFIG ----------
import importlib
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Final_theme import apply_theme

# app.py
import os
import textwrap
from dotenv import load_dotenv, find_dotenv
from openai import APIConnectionError
import json
import streamlit as st
from uuid import uuid4 
from app_azure.blob_functions import get_companies
from pages.design.dialogues import *
from prompts import default_gpt_prompt

from rags.rag import (
    retrieve,
    retrieve_hybrid,
    retrieve_semantic,
    retrieve_hybrid_enhanced,
    build_context,
    get_aoai_client,
    AOAI_DEPLOYMENT,
    TEXT_FIELD,
)
from prompts import new_system_finance_prompt, finance_prompt_web

from gpts.gpt_agent import profileAgent
from io import BytesIO
from typing import Tuple
import time
from engines.hybrig_eng_enhanced import HybridEngine
from gpts.gpt_assistants import general_assistant
from prompts4 import section7, finance_calculations, system_mod

from gpts.gpt5_web import WebAgent

from gpts.gpt_assistants import maybe_route_to_action
from app_azure.blob_functions import companyHouseListAdd
from app_azure.adf_functions import trigger_function
from app_azure.search_functions import run_indexer

load_dotenv(find_dotenv(), override=True)
OPENAI_API_KEY  = os.getenv("FELIPE_OPENAI_API_KEY")        # required


# =====================================================

st.set_page_config(page_title="Oraculum", layout="wide")
# st.title("Oraculum")

# -------- Session state --------

if "greeted" not in st.session_state:
    st.session_state.greeted = False

if "websearch" not in st.session_state:
    st.session_state.websearch = False
if "mixsource" not in st.session_state:
    st.session_state.mixsource = False

if "convos" not in st.session_state:
    cid = str(uuid4())
    st.session_state.convos = {cid: {"title": "New chat", "messages": []}}
    st.session_state.current_cid = cid

if "history" not in st.session_state:
    st.session_state.history = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None  # used by sidebar suggestion buttons
if "theme" not in st.session_state:
    st.session_state.theme = "light"   # default: Dark Mode
if "rag" not in st.session_state:
    st.session_state.rag = "FIND THE VARIABLES 'Net cash from operating activities' and 'Net cash used in investing activities' in the statement of cash flows. FILES FROM 2024."
if "sys_message_mod" not in st.session_state:
    st.session_state.sys_message_mod = system_mod
if "calculations" not in st.session_state:
    st.session_state.calculations = finance_calculations
if "company_name" not in st.session_state:
    st.session_state.company_name = None
if "companies_name" not in st.session_state:
    st.session_state.companies_name = ['Seaport Topco Limited']
if "companies_name_dic" not in st.session_state:
    st.session_state.companies_name_dic = {'Seaport Topco Limited':"SEAPORT_TOPCO_LIMITED",
                                           'Radley Co': 'RADLEY_+_CO._LIMITED',
                                           'James Donaldson': 'JAMES_DONALDSON_GROUP_LTD'}
if "profile_mod" not in st.session_state:
    st.session_state.profile_mod = new_system_finance_prompt
if "profile_mod_web" not in st.session_state:
    st.session_state.profile_mod_web = finance_prompt_web

if "pdf_mod" not in st.session_state:
    st.session_state.pdf_mod = False
if "just_ingested" not in st.session_state:
    st.session_state.just_ingested = False
if "just_ingested_msg" not in st.session_state:
    st.session_state.just_ingested_msg = ""

if "ocr_chain" not in st.session_state:
    st.session_state.ocr_chain = None
if "ocr_chain_with_sources" not in st.session_state:
    st.session_state.ocr_chain_with_sources = None
if "ocr_timings" not in st.session_state:
    st.session_state.ocr_timings = None

if "section_build" not in st.session_state:
    st.session_state.section_build = None

output_placeholder = st.empty()
# apply_theme(st.session_state.theme)

# =====================================================

def check_actions(prompt, client, deployment) -> bool:

    calls = maybe_route_to_action(prompt, client.az_openai, deployment)

    if not calls:
        return False

    for call in calls:
        if call.function.name == "create_company_profile":
            args = json.loads(call.function.arguments or "{}")
            company = args.get("companyName") or "(unknown)"

            out_pdf = client.generate_company_profile()

            st.download_button(
                "Download Profile PDF",
                data=out_pdf,
                file_name=f"{company}_profile.pdf",
                mime="application/pdf",
            )
            st.success("Profile creation done.")
            st.markdown(f"**Functionality in construction..**  (requested company: `{company}`)")

            # Also persist this turn in the chat history so it shows up on rerun
            st.session_state.history.append({
                "q": prompt,
                "a": f"Created a company profile for **{company}**. Use the button above to download the PDF."
            })
            return True
        elif call.function.name == 'add_company':
            args = json.loads(call.function.arguments or "{}")
            companyNumber = args.get("companyNumber") or "(unknown)"
            
            try:
                companyHouseListAdd(CompanyNumber = companyNumber)
                st.success(f"Added {companyNumber} to internal list...")
            except Exception as e:
                print(f'Adding to internal list problem \n{e}')

            try:
                trigger_function(companyNumber = companyNumber)
                st.success(f"Downloaded {companyNumber} files...")
            except Exception as e:
                print(f'Downloading file problem \n{e}')

            try:
                st.success("Running OCR and Vectorization, come back in 10 minutes ... ")
                run_indexer()
            except Exception as e:
                print(f'OCR and Vector problem \n{e}')
            
            return True


    return False

def stream_answer(prompt: str, section_build = False, section = ''):

    try:
        agent = profileAgent(
            company_name = st.session_state.company_name,
            k=50, 
            max_text_recall_size=35, 
            max_chars=10000,
            model='gpt-5', 
            profile_prompt= st.session_state.sys_message_mod, 
            finance_calculations= st.session_state.calculations
        )

        if section_build:
            answer_text = agent._generate_section(section = section)

        else:
            if check_actions(prompt,
                             agent, 
                             'gpt-5'
                             ):
                pass
            else:
                resp = agent._rag_answer(rag_nl = prompt, question= prompt)
                answer_text = resp['answer']

    except Exception as e:
        answer_text = f"ERROR. \n {e}"

    if section_build:
        st.session_state.history.append({"q": section, "a": answer_text})
    else:
        st.session_state.history.append({"q": prompt, "a": answer_text})

    ph = st.empty()
    ph.write(answer_text)


# ---------- Dark/White Mode----------
if "theme" not in st.session_state:
    st.session_state.theme = "light"  # or "dark" as default
apply_theme(st.session_state.theme)


# ---------- CUSTOM TOP BAR ----------
from pathlib import Path
LOGO = Path(__file__).parent / "images" / "teneo_logo.png"

st.logo(
    str(LOGO),                 # main logo
    size="large",             # "small" | "medium" | "large"
)

# ---- Chat sessions ----
if "convos" not in st.session_state:
    cid = str(uuid4())
    st.session_state.convos = {cid: {"title": "New chat", "messages": []}}
    st.session_state.current_cid = cid

# if "history" not in st.session_state:
#     st.session_state.history = []


# ---------- NAV STATE ----------
if "view" not in st.session_state:
    st.session_state.view = "home"          

def go(view):
    st.session_state.view = view


# ---------- SIDEBAR (static for now) ----------
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

    # # ---- Chat History picker ----
    # ids = list(st.session_state.convos.keys())
    # titles = [st.session_state.convos[i]["title"] for i in ids]

    # pick = st.radio("Chat History", options=ids,
    #                 format_func=lambda x: st.session_state.convos[x]["title"])

    # st.session_state.current_cid = pick



    # Each button uses Streamlit’s native Material icon support
    st.markdown("### Select Mode")

    # Companies House (PDF) mode
    if st.button("Research with Companies House PDF", icon=":material/domain:", use_container_width=True):
        st.session_state.websearch = False
        st.session_state.mixsource = False
        for k in ["history", "messages", "pending_prompt"]:
            st.session_state.pop(k, None)
        st.session_state.greeted = False
        st.rerun()

    # Web Search mode
    if st.button("Research with Web Search", icon=":material/language:", use_container_width=True, key="mode_web"):
        st.session_state.mixsource = False
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
        for k in ["history", "messages", "pending_prompt"]:
            st.session_state.pop(k, None)
        if "history" not in st.session_state:
            st.session_state.history = []
        name_map, names = get_companies()
        st.session_state.history.append({"a": f"{greeting_3}\n\n Companies Available: \n" + "\n".join(f"- {n}" for n in names)})
        st.rerun()


    def render_chat(header: str, intro_msg=None):
        # visual header (uses your existing chat-panel CSS)
        st.markdown(f"""
        <div class='chat-panel'>
        <div class='head'>🏛️ {header}</div>
        <div class='body'>
            {f"<div class='msg bot'>{intro_msg}</div>" if intro_msg else ""}
        </div>
        </div>
        """, unsafe_allow_html=True)

        # render history (your boss’s pattern)
        for turn in st.session_state.history:
            if turn.get("q"):
                with st.chat_message("user"):
                    st.write(turn["q"])
            with st.chat_message("assistant"):
                st.write(turn["a"])

        # single input
        return st.chat_input("Type your message...")
# after session-state defaults, before rendering history
companies = st.session_state.get("companies_name") or []

if not st.session_state.greeted and st.session_state.view == "companies":
    _, names = get_companies()
    st.session_state.history.append({
        "a": f"{greeting_1}\n\n" + "\n".join(f"- {n}" for n in names)
    })
    st.session_state.greeted = True
    # ---------- VIEWS ----------
if st.session_state.view == "home":
    L, C, R = st.columns([0.25, 14, 0.25], gap="large")
    with C:
        st.markdown("<div class='home-wrap'>", unsafe_allow_html=True)
        st.markdown("<div class='hero-wrap'>", unsafe_allow_html=True)

        st.markdown("<h1 class='hero-title'>Welcome to Oraculum</h1>", unsafe_allow_html=True)
        st.markdown("<p class='hero-sub'>Your AI assistant for financial documents and company research, Please select a mode to get started.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    # Cards row (clickable; no business logic yet)
        c1, c2, c3 = st.columns([0.5, 0.5, 0.5], gap="medium")

        with c1:
            st.button("**Research with Companies House**  \n_Access comprehensive company data from Companies House. Search for companies, view financial filings, and analyze company structures. Perfect for due diligence and company research._", icon=":material/domain:", key="open_companies", use_container_width=True, on_click=go, args=("companies",))
        with c2:
            st.button("**Research with Web Search**  \n_Leverage real-time web search capabilities to find the latest news, market data, and insights. Stay updated with current information about companies and industries._", icon=":material/language:", key="open_web", use_container_width=True, on_click=go, args=("web",))
        with c3:
            st.button("**Research with Comapanies House & Web Search**  \n_Upload and analyze PDF documents with advanced OCR. Extract key figures, generate summaries, and identify important metrics from financial reports, contracts, and other documents._", icon=":material/picture_as_pdf:", key="open_pdf", use_container_width=True, on_click=go, args=("pdf",))


        st.markdown("</div>", unsafe_allow_html=True)
elif st.session_state.view == "companies":
    # st.markdown("<h2 class='page-h2'>Companies House Research</h2><p class='page-sub'>Search and manage company data.</p>", unsafe_allow_html=True)

    if st.session_state.get("mixsource"):
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
        if uploaded_file:
            st.success(f"Uploaded: {uploaded_file.name}")
    




# =====================================================

client = get_aoai_client()

# Render prior turns every run so the conversation persists
# ---------- CHAT RENDERING ----------
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
 
    # Accept either a typed prompt or an injected one from sidebar suggestions
    placeholder = (
        "Ask a question about your PDFs…" 
        if st.session_state.pdf_mod 
        else "Ask about the ingested PDFs…"
    )
    typed = st.chat_input(placeholder)
    pending = st.session_state.pop("pending_prompt", None)
    prompt = typed or pending
    if not st.session_state.websearch and not st.session_state.mixsource:
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

# Web Answer
def web_answer(prompt):

    agent = WebAgent()

    messages = [
    {"role": "system", "content": default_gpt_prompt},
    {"role": "user",   "content": prompt},
    ]

    try: 
        answer_text = agent._web_search(messages)
    except Exception as e:
        answer_text = f"ERROR. \n {e}"

    st.session_state.history.append({"q": prompt, "a": answer_text})

    ph = st.empty()
    ph.write(answer_text)

def mix_answer(prompt):

    agent = WebAgent()

    try: 
        answer_text = agent._answer(question=prompt)
    except Exception as e:
        answer_text = f"ERROR. \n {e}"

    st.session_state.history.append({"q": prompt, "a": answer_text})

    ph = st.empty()
    ph.write(answer_text)


if prompt:
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):

        # Try tool routing first
        model_profile = "gpt-5" #if model_profile_mod else "o3"

        if st.session_state.websearch:
            web_answer(prompt)
        elif st.session_state.mixsource:
            if not st.session_state.company_name:
                with st.chat_message("assistant"):
                    st.write("Please select a company in the sidebar before asking a question.")
                # st.session_state.history.append({"q": prompt, "a": "Please select a company first."})
                st.stop()
            else:
                with st.chat_message("assistant"):
                    mix_answer(prompt)
        else:
            if not st.session_state.company_name:
                # get_company(prompt)
                with st.chat_message("assistant"):
                    st.write("Please select a company in the sidebar before asking a question.")
                # st.session_state.history.append({"q": prompt, "a": "Please select a company first."})
                st.stop()
            else:
                with st.chat_message("assistant"):
                    stream_answer(prompt)