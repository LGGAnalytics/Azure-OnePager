# app.py
import os
import textwrap
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from openai import APIConnectionError
import json
import streamlit as st
from uuid import uuid4 
from azure.blob_functions import get_companies
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
from theme_mod import apply_theme
from prompts import new_system_finance_prompt, finance_prompt_web

from gpts.gpt_agent import profileAgent
from io import BytesIO
from typing import Tuple
import time
# from engines.hybrig_eng_enhanced import HybridEngine
from gpts.gpt_assistants import general_assistant
from prompts4 import section7, finance_calculations, system_mod

from gpts.gpt5_web import WebAgent

from gpts.gpt_assistants import maybe_route_to_action
from azure.blob_functions import companyHouseListAdd
from azure.adf_functions import trigger_function
from azure.search_functions import run_indexer

load_dotenv(find_dotenv(), override=True)
OPENAI_API_KEY  = os.getenv("FELIPE_OPENAI_API_KEY")        # required

# =====================================================

st.set_page_config(page_title="Oraculum", layout="wide")
st.title("Oraculum")

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

if "section_build" not in st.session_state:
    st.session_state.section_build = None

output_placeholder = st.empty()
apply_theme(st.session_state.theme)

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
            answer_text = answer_text

        else:
            if check_actions(prompt,
                             agent, 
                             'gpt-5'
                             ):
                return
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


# -------- Left sidebar with collapsible sections --------
with st.sidebar:
    mode = st.session_state.theme
    toggle_label = "White Mode" if mode == "dark" else "Dark Mode"
    if st.button(toggle_label, use_container_width=True, key="theme_toggle"):
        st.session_state.theme = "light" if mode == "dark" else "dark"
        st.rerun()

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

    st.title('Modes')
    if st.button("📕 Research with CompaniesHouse", use_container_width=True, key="pdf_btn"):
        st.session_state.websearch = False
        st.session_state.mixsource = False
        for k in ["history", "messages", "pending_prompt"]:
            st.session_state.pop(k, None)
        st.session_state.greeted = False
        st.rerun()
    if st.button("🌐 Research with WebSearch", use_container_width=True, key="web_btn"):
        st.session_state.mixsource = False
        for k in ["history", "messages", "pending_prompt"]:
            st.session_state.pop(k, None)
        if "history" not in st.session_state:
            st.session_state.history = []
        st.session_state.history.append({"a": greeting_2})
        ph = st.empty()
        ph.write(greeting_2)
        st.session_state.websearch = True
        
        st.rerun()
    if st.button("🌐📕 Research with Both", use_container_width=True, key="both_btn"):
        st.session_state.websearch = False
        st.session_state.mixsource = True   
        for k in ["history", "messages", "pending_prompt"]:
            st.session_state.pop(k, None)
        if "history" not in st.session_state:
            st.session_state.history = []

        _ , names = get_companies()
        st.session_state.history.append({"a":f"{greeting_3}\n\n Companies Available: \n" + "\n".join(f"- {n}" for n in names)})
        ph = st.empty()
        ph.write(greeting_3)

        st.rerun()


with st.sidebar.expander("Company Selection", expanded=False):
    name_map , names = get_companies()
    unique_names = list(dict.fromkeys(names))      # de-dupe while keeping order
    reverse_map = {v: k for k, v in name_map.items()}  # clean -> orig

    for i, clean_name in enumerate(unique_names):
        # Use a stable, unique key (avoid spaces)
        key = f"company_btn_{i}"
        if st.button(clean_name, key=key):
            st.session_state.company_name = reverse_map.get(clean_name, clean_name)

            answer_text = f"You have selected the \n {clean_name}"
            st.session_state.history.append({"a": answer_text})

            ph = st.empty()
            ph.write(answer_text)
            
            st.rerun() 



with st.sidebar.expander("Quick Actions", expanded=False):

    if st.session_state.websearch:
    
        if st.button("🗞️ Show Recent News", use_container_width=True, key="news_btn"):
            st.session_state.active_tile = "auto"
            st.rerun()
    elif st.session_state.mixsource:
        pass
    else:
        
        if st.button("📋 List Available Companies", use_container_width=True, key="list_companies_btn"):
            st.session_state.active_tile = "auto"
            _ , names = get_companies()
            answer_text = f"{companies_available}\n\n" + "\n".join(f"- {n}" for n in names)
            st.session_state.history.append({"q": f'Which companies are available?', "a": answer_text})

            ph = st.empty()
            ph.write(answer_text)
            st.rerun()

        if st.button("✚ Add Company", use_container_width=True, key="add_company_btn"):
            st.session_state.active_tile = "auto"
            answer_text = f"{add_company_tutorial_1}\n\n"
            st.session_state.history.append({"q": f'How do I add new companies?', "a": answer_text})
            ph = st.empty()
            ph.write(answer_text)
            st.rerun() 

        if st.button("⚙️ Create Profile", use_container_width=True, key="create_profile_btn"):
            st.session_state.active_tile = "auto"
            answer_text = f"{profile_tutorial_1}\n\n"
            st.session_state.history.append({"q": f'How do I ask for a Company Profile?', "a": answer_text})
            ph = st.empty()
            ph.write(answer_text)
            st.rerun()

        if st.button("⚙️ Create Profile Section", use_container_width=True, key="create_profile_btn"):
            st.session_state.active_tile = "auto"
            answer_text = f"{profile_tutorial_1}\n\n"
            st.session_state.history.append({"q": f'How do I ask for a Company Profile?', "a": answer_text})
            ph = st.empty()
            ph.write(answer_text)
            st.rerun()

        # st.rerun()
if st.session_state.websearch or st.session_state.mixsource or st.session_state.pdf:
    pass
else:
    with st.sidebar.expander("Profile Sections", expanded=False):
        st.write('Take in mind that building a section might take between 11-25 minutes in average')
        if st.button("1.Get Business Overview", use_container_width=True, key="overview_btn"):
            if not st.session_state.company_name:
                with st.chat_message("assistant"):
                    st.session_state.history.append({"q": f"1.Get Business Overview", "a": "Please select a company in the sidebar before asking a question."})
                st.rerun()
            else:
                st.session_state.section_build = "GENERATE BUSINESS OVERVIEW"
                stream_answer(prompt='', section_build=True, section=st.session_state.section_build)
            st.rerun()
        if st.button("2.Get Key Stakeholders", use_container_width=True, key="stakeholder_btn"):
            if not st.session_state.company_name:
                with st.chat_message("assistant"):
                    st.session_state.history.append({"q": f"2.Get Key Stakeholders", "a": "Please select a company in the sidebar before asking a question."})

                st.rerun()
            else:
                st.session_state.section_build = "GENERATE KEY STAKEHOLDERS"
                stream_answer(prompt='', section_build=True, section=st.session_state.section_build)
            st.rerun()
        if st.button("3.Revenue split (NEW)", use_container_width=True, key="revenue_btn"):
            if not st.session_state.company_name:
                with st.chat_message("assistant"):
                    st.session_state.history.append({"q": f"3.Revenue split", "a": "Please select a company in the sidebar before asking a question."})
                
                st.rerun()
            else:
                st.session_state.section_build = "GENERATE REVENUE SPLIT"
                stream_answer(prompt='', section_build=True, section=st.session_state.section_build)
            st.rerun()
        if st.button("4a.Products/Services Overview (NEW)", use_container_width=True, key="prod_btn"):
            if not st.session_state.company_name:
                with st.chat_message("assistant"):
                    st.session_state.history.append({"q": f"4a.Products/Services Overview", "a": "Please select a company in the sidebar before asking a question."})
                
                st.rerun()
            else:
                st.session_state.section_build = "GENERATE PRODUCTS SERVICES OVERVIEW"
                stream_answer(prompt='', section_build=True, section=st.session_state.section_build)
            st.rerun()
        if st.button("4b.Geographical Footprint (NEW)", use_container_width=True, key="geo_btn"):
            if not st.session_state.company_name:
                with st.chat_message("assistant"):
                    st.session_state.history.append({"q": f"4b.Geographical Footprint", "a": "Please select a company in the sidebar before asking a question."})
                
                st.rerun()
            else:
                st.session_state.section_build = "GENERATE GEO FOOTPRINT"
                stream_answer(prompt='', section_build=True, section=st.session_state.section_build)
            st.rerun()
        if st.button("5.Key Recent Developments (NEW)", use_container_width=True, key="recent_btn"):
            if not st.session_state.company_name:
                with st.chat_message("assistant"):
                    st.session_state.history.append({"q": f"5.Key Recent Developments", "a": "Please select a company in the sidebar before asking a question."})
                
                st.rerun()
            else:
                st.session_state.section_build = "GENERATE DEVELOPMENTS HIGHLIGHTS"
                stream_answer(prompt='', section_build=True, section=st.session_state.section_build)
            st.rerun()
        if st.button("6.Get Financial Highlights", use_container_width=True, key="finance_btn"):
            if not st.session_state.company_name:
                with st.chat_message("assistant"):
                    st.session_state.history.append({"q": f"5.Get Financial Highlights", "a": "Please select a company in the sidebar before asking a question."})
                
                st.rerun()
            else:
                st.session_state.section_build = "GENERATE FINANCIAL HIGHLIGHTS"
                stream_answer(prompt='', section_build=True, section=st.session_state.section_build)
            st.rerun()
        if st.button("7.Get Capital Structure", use_container_width=True, key="capital_btn"):
            if not st.session_state.company_name:
                with st.chat_message("assistant"):
                    st.session_state.history.append({"q": f"6.Get Capital Structure", "a": "Please select a company in the sidebar before asking a question."})
                
                st.rerun()
            else:
                st.session_state.section_build = "GENERATE CAPITAL STRUCTURE"
                stream_answer(prompt='', section_build=True, section=st.session_state.section_build)
            st.rerun()
    

# =====================================================

# after session-state defaults, before rendering history
companies = st.session_state.get("companies_name") or []

if not st.session_state.greeted:
    if companies:  # only greet when list is ready
        with st.chat_message("assistant"):
            _ , names = get_companies()
            st.session_state.history.append({"a":f"{greeting_1}\n\n" + "\n".join(f"- {n}" for n in names)})
            # st.markdown(
            #     f"{greeting_1}\n\n" + "\n".join(f"- {n}" for n in names)
            # )
        st.session_state.greeted = True
    else:
        with st.chat_message("assistant"):
            st.write("Hey, welcome! Loading the list of companies…")
        # Optional: auto-refresh soon after to pick up the list when it arrives
        # st.rerun()  # modern API to rerun script if you detect it's ready

    st.session_state.greeted = True
# =====================================================

client = get_aoai_client()

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
