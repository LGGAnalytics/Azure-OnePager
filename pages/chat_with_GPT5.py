# app.py
import os
import textwrap
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from openai import APIConnectionError
import json
import streamlit as st

from rag import (
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

from profile_agent import profileAgent
from profile_agent_web import profileAgentWeb
from gpts.gpt5_web import WebAgent
from gpts.gpt_assistants import maybe_route_to_action
from azure.blob_functions import companyHouseListAdd
from azure.adf_functions import trigger_function
from azure.search_functions import run_indexer
from gpts.gpt_assistants import question_to_machine
from io import BytesIO
from typing import Tuple
import time
from engines.hybrig_eng_enhanced import HybridEngine
from pages.dev_mode import k, ts, cs, reasoning_effort, verbosity, do_stream


load_dotenv(find_dotenv(), override=True)
# =====================================================
# GPT TOOLS 
# @st.cache_resource(show_spinner=False)
# def ocr_engine_cached_multi(files_bytes: Tuple[bytes, ...], files_names: Tuple[str, ...]):
#     """Multi-file OCR mode via HybridEngine (idempotent + timed)."""
#     pdf_streams = tuple((BytesIO(b), n) for b, n in zip(files_bytes, files_names))
#     engine = HybridEngine(pdf_streams)
#     t0 = time.perf_counter(); engine.main(); build_s = time.perf_counter() - t0
#     timings = getattr(engine, "timings", {})
#     timings["total_build_s"] = build_s
#     return engine.chain, engine.chain_with_sources, timings

# =====================================================

# st.set_page_config(page_title="Oraculum v2", layout="wide")
# st.title("📄 Oraculum v2.1 (Azure Version)")
RUN_UI = os.getenv("RUN_CHAT_UI", "0") == "1"
# -------- Session state --------
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None  # used by sidebar suggestion buttons
if "theme" not in st.session_state:
    st.session_state.theme = "dark"   # default: Dark Mode
if "sys_message_mod" not in st.session_state:
    st.session_state.sys_message_mod = """
        You are a financial analyst. Use ONLY the provided context to answer.
        All the files that you will be working with and PROVIDED in the context are annual reports. The name of the company that own the annual report is in the first page.
        Cite sources using [#] that match the snippet numbers.
        If the answer isn't in the context, say you don't know.
        """
if "dev_message_mod" not in st.session_state:
    st.session_state.dev_message_mod = "Ask about the ingested PDFs…"
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

client = get_aoai_client()

# output_placeholder = st.empty()
# apply_theme(st.session_state.theme)

# =====================================================

# -------- Left sidebar with collapsible sections --------




# ========================================
def check_actions(prompt, client, deployment, k, ts, cs, model_profile) -> bool:

    calls = maybe_route_to_action(prompt, client, deployment)

    if not calls:
        return False

    for call in calls:
        if call.function.name == "create_company_profile":
            args = json.loads(call.function.arguments or "{}")
            company = args.get("companyName") or "(unknown)"

            agent1 = profileAgent(
                company,
                k=k, max_text_recall_size=ts, max_chars=cs,
                model=model_profile, profile_prompt=st.session_state.profile_mod_web
            )

            out_pdf = agent1._rag_answer()

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

def stream_answer(prompt: str):

    agent = WebAgent(
        k=k,
        max_text_recall_size=ts,
        # model=OPENAI_MODEL,
        top=20,
        # max_output_tokens=1200,
        reasoning_effort=reasoning_effort,
        verbosity=verbosity,
        tool_choice="none",
        streaming=do_stream,  # note: UI streaming (see note below)
    )

    answer_text = agent._answer(prompt)

    st.session_state.history.append({"q": prompt, "a": answer_text})

    ph = st.empty()
    if do_stream:
        buf = ""
        for ch in answer_text:
            buf += ch
            ph.write(buf)
            time.sleep(0.008)
    else:
        ph.write(answer_text)

# -------- UI (only if RUN_UI=1) --------
if RUN_UI:
    st.set_page_config(page_title="Oraculum v2", layout="wide")
    st.title("📄 Oraculum v2.1 (Azure Version)")
    apply_theme(st.session_state.theme)
# Render prior turns every run so the conversation persists
    for turn in st.session_state.history:
        with st.chat_message("user"):
            st.write(turn["q"])
        with st.chat_message("assistant"):
            st.write(turn["a"])

    if st.session_state.just_ingested:
        with st.chat_message("assistant"):
            st.write(st.session_state.just_ingested_msg)
        # Reset so it shows only once
        st.session_state.just_ingested = False

# Accept either a typed prompt or an injected one from sidebar suggestions
    placeholder = "Ask a question about your PDFs…" if st.session_state.pdf_mod else "Ask about the ingested PDFs…"
    typed = st.chat_input(placeholder)
    pending = st.session_state.pop("pending_prompt", None)
    prompt = typed or pending

# question = st.text_input("Ask a question about your PDFs:")
# if question:
#     res = st.session_state.ocr_chain_with_sources.invoke(question)
#     st.write(res["response"])

    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

    # if st.session_state.pdf_mod and st.session_state.ocr_chain_with_sources:
    #     # ==== PDF PIPELINE ====
    #     res = st.session_state.ocr_chain_with_sources.invoke(prompt)
    #     answer_text = res.get("response") if isinstance(res, dict) else str(res)

    #     with st.chat_message("assistant"):
    #         st.write(answer_text)

    #     # Persist in chat history so it shows up next rerun
    #     st.session_state.history.append({"q": prompt, "a": answer_text})

        with st.chat_message("assistant"):
            # Try tool routing first
            model_profile = "gpt-5" #if model_profile_mod else "o3"
            if check_actions(
                    prompt, client, AOAI_DEPLOYMENT,
                    k=k, ts=ts, cs=cs, model_profile=model_profile):
                pass
            else:
                stream_answer(prompt)


