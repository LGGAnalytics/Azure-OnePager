# app.py
import os
import textwrap
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from openai import APIConnectionError
import json
import streamlit as st

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
from theme_mod import apply_theme
from prompts import new_system_finance_prompt, finance_prompt_web

from gpts.gpt_agent import profileAgent
from io import BytesIO
from typing import Tuple
import time
from engines.hybrig_eng_enhanced import HybridEngine
from gpts.gpt_assistants import general_assistant
from prompts4 import section7, finance_calculations, system_mod


load_dotenv(find_dotenv(), override=True)
OPENAI_API_KEY  = os.getenv("FELIPE_OPENAI_API_KEY")        # required

# =====================================================

st.set_page_config(page_title="Oraculum v2", layout="wide")
st.title("📄 Oraculum v2.2 (Testing Prompt)")

# -------- Session state --------

if "greeted" not in st.session_state:
    st.session_state.greeted = False

if "history" not in st.session_state:
    st.session_state.history = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None  # used by sidebar suggestion buttons
if "theme" not in st.session_state:
    st.session_state.theme = "white"   # default: Dark Mode
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

output_placeholder = st.empty()
apply_theme(st.session_state.theme)

# =====================================================

# -------- Left sidebar with collapsible sections --------
with st.sidebar:
    mode = st.session_state.theme
    toggle_label = "White Mode" if mode == "dark" else "Dark Mode"
    if st.button(toggle_label, use_container_width=True, key="theme_toggle"):
        st.session_state.theme = "light" if mode == "dark" else "dark"
        st.rerun()
    st.markdown("---")


with st.sidebar.expander("Script Mod", expanded=False):
    st.title("Define RAG question:")
    st.write('Sets the question that will go to RAG system (not the same as the one you ask the bot). This one is responsible for Retrieval from the database.')
    st.session_state.rag = st.text_area(
        "RAG", value=st.session_state.rag, key="rag_ta"
    )
    st.title("Define System script:")
    st.write('App-specific instructions and tools; override user phrasing when conflicting.')
    st.session_state.sys_message_mod = st.text_area(
        "System", value=st.session_state.sys_message_mod, key="sys_ta"
    )
    st.title("Finance Calculations script:")
    st.write('App-specific instructions and tools; override user phrasing when conflicting.')
    st.session_state.calculations = st.text_area(
        "Calculations", value=st.session_state.calculations, key="cal_ta"
    )
    # st.title("Define Section Script:")
    # st.session_state.profile_mod = st.text_area(
    #     "Profile", value= st.session_state.profile_mod , key="pro_ta"
    # )

with st.sidebar.expander("Companies Selection", expanded=False):
    st.write('This section allows you to select the company you are debugging')
    suggestions = [
        "Seaport Topco Limited",
        "Radley Co",
        "James Donaldson"
    ]
    for i, s in enumerate(suggestions):
        if st.button(s, key=f"sb_sugg_{i}", use_container_width=True):
            st.session_state.company_name = st.session_state.companies_name_dic[s]
            answer_text = f"You have selected the \n {s}"
            st.session_state.history.append({"q": f'User selected company {s}', "a": answer_text})

            ph = st.empty()
            ph.write(answer_text)
            st.rerun()


# =====================================================

# after session-state defaults, before rendering history
companies = st.session_state.get("companies_name") or []

if not st.session_state.greeted:
    if companies:  # only greet when list is ready
        with st.chat_message("assistant"):
            st.write(
                "Hey, welcome! I am a Financial Assistant with access to Company House! \n "
                f"Currently we have the following companies available: \n {', '.join(companies)}.\n"
                "Tell me which one you'd like to talk about."
            )
        st.session_state.greeted = True
    else:
        with st.chat_message("assistant"):
            st.write("Hey, welcome! Loading the list of companies…")
        # Optional: auto-refresh soon after to pick up the list when it arrives
        # st.rerun()  # modern API to rerun script if you detect it's ready

# =====================================================


client = get_aoai_client()

# def get_company(prompt: str):

#     try:

#         instruction = f"""
#         You are an ASSISTANT which PURPOSE is to understand the company name from user prompt, and give out the correct equivalent name from the system list.
#         \n List of official company names: {st.session_state.companies_name}. \n RETURN THE COMPANY NAME GIVEN IN THE PREVIOUS LIST WHICH IS SIMILAR TO USER PROMPT.
#         """
#         offline_question = general_assistant(instruction, prompt, OPENAI_API_KEY, 'gpt-4o')

#         st.session_state.company_name = st.session_state.companies_name_dic[offline_question]
         
#         stream_answer(prompt)
#     except Exception as e:
#         answer_text = 'The company you selected isnt in the list.'
#         st.session_state.history.append({"q": prompt, "a": answer_text})
#         ph = st.empty()
#         ph.write(answer_text)


#     pass

def stream_answer(prompt: str):

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

        resp = agent._rag_answer(rag_nl = st.session_state.rag, question= prompt)
        answer_text = resp['answer']

    except Exception as e:
        answer_text = f"ERROR. \n {e}"

    st.session_state.history.append({"q": prompt, "a": answer_text})

    ph = st.empty()
    ph.write(answer_text)


# Render prior turns every run so the conversation persists
for turn in st.session_state.history:
    if turn.get("q"):                      # only render a user bubble when it exists
        with st.chat_message("user"):
            st.write(turn["q"])
    with st.chat_message("assistant"):
        st.write(turn["a"])

# Accept either a typed prompt or an injected one from sidebar suggestions
placeholder = "Ask a question about your PDFs…" if st.session_state.pdf_mod else "Ask about the ingested PDFs…"
typed = st.chat_input(placeholder)
pending = st.session_state.pop("pending_prompt", None)
prompt = typed or pending


if prompt:
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        # Try tool routing first
        model_profile = "gpt-5" #if model_profile_mod else "o3"
        if not st.session_state.company_name:
            # get_company(prompt)
            with st.chat_message("assistant"):
                st.write("Please select a company in the sidebar before asking a question.")
            st.session_state.history.append({"q": prompt, "a": "Please select a company first."})
            st.stop()
        else:
            with st.chat_message("assistant"):
                stream_answer(prompt)
