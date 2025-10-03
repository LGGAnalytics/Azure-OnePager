#02 company profile app.py
import os
import textwrap
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from openai import APIConnectionError
import json
import streamlit as st
import sys, pathlib
repo_root = pathlib.Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
import sys, pathlib
repo_root = pathlib.Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

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
from engines.prompts4 import section7, finance_calculations, system_mod


load_dotenv(find_dotenv(), override=True)
OPENAI_API_KEY  = os.getenv("FELIPE_OPENAI_API_KEY")        # required

# =====================================================


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
    st.session_state.companies_name_dic = {'Seaport Topco Limited':"SEAPORT_TOPCO_LIMITED"}
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


apply_theme(st.session_state.theme)

# CORE LOGIC

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
    return answer_text

# STANDALONE RUN (only executes when you run this file directly)
# =====================================================
# if __name__ == "__main__":
#     st.set_page_config(page_title="Oraculum v2", layout="wide")
#     st.title("📄 Oraculum v2.2 (Testing Prompt)")

#     # Sidebar controls (kept here so you can still debug this page by itself)
#     with st.sidebar:
#         mode = st.session_state.theme
#         toggle_label = "White Mode" if mode == "dark" else "Dark Mode"
#         if st.button(toggle_label, use_container_width=True, key="theme_toggle"):
#             st.session_state.theme = "light" if mode == "dark" else "dark"
#             st.rerun()
#         st.markdown("---")

#     with st.sidebar.expander("Script Mod", expanded=False):
#         st.title("Define RAG question:")
#         st.write('Sets the question that will go to RAG system.')
#         st.session_state.rag = st.text_area("RAG", value=st.session_state.rag, key="rag_ta")

#         st.title("Define System script:")
#         st.write('App-specific instructions and tools; override user phrasing when conflicting.')
#         st.session_state.sys_message_mod = st.text_area("System", value=st.session_state.sys_message_mod, key="sys_ta")

#         st.title("Finance Calculations script:")
#         st.write('App-specific instructions and tools.')
#         st.session_state.calculations = st.text_area("Calculations", value=st.session_state.calculations, key="cal_ta")

#     with st.sidebar.expander("Companies Selection", expanded=False):
#         st.write('Select the company you are debugging')
#         suggestions = ["Seaport Topco Limited"]
#         for i, s in enumerate(suggestions):
#             if st.button(s, key=f"sb_sugg_{i}", use_container_width=True):
#                 st.session_state.company_name = st.session_state.companies_name_dic[s]
#                 msg = f"You have selected {s}"
#                 st.session_state.history.append({"q": f'User selected company {s}', "a": msg})
#                 st.empty().write(msg)
#                 st.rerun()

#     # Greeting (only in standalone)
#     companies = st.session_state.get("companies_name") or []
#     if not st.session_state.greeted:
#         if companies:
#             with st.chat_message("assistant"):
#                 st.write(
#                     "Hey, welcome! I am a Financial Assistant with access to Company House!\n"
#                     f"Currently we have: {', '.join(companies)}.\n"
#                     "Tell me which one you'd like to talk about."
#                 )
#             st.session_state.greeted = True
#         else:
#             with st.chat_message("assistant"):
#                 st.write("Hey, welcome! Loading the list of companies…")

#     # Render prior turns
#     for turn in st.session_state.history:
#         if turn.get("q"):
#             with st.chat_message("user"):
#                 st.write(turn["q"])
#         with st.chat_message("assistant"):
#             st.write(turn["a"])

#     # Single input for standalone testing
#     placeholder = "Ask about the ingested PDFs…"  # same placeholder you used
#     typed = st.chat_input(placeholder)
#     if typed:
#         with st.chat_message("user"):
#             st.write(typed)

#         if not st.session_state.company_name:
#             with st.chat_message("assistant"):
#                 st.write("Please select a company in the sidebar before asking a question.")
#             st.session_state.history.append({"q": typed, "a": "Please select a company first."})
#             st.stop()
#         else:
#             ans = stream_answer(typed)
#             with st.chat_message("assistant"):
#                 st.write(ans)
def render(**kwargs):
    return