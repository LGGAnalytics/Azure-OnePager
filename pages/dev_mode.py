#06 dev app.py
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
# ---- import-safe defaults (so functions don't crash on import) ----
k = 100
ts = 200
cs = 8000
web_mode = False
reasoning_effort = "medium"
verbosity = "medium"
do_stream = False

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



# =====================================================
# -------- UI wrapper (NEW) --------
def main():

    with st.sidebar:
        mode = st.session_state.theme
        toggle_label = "White Mode" if mode == "dark" else "Dark Mode"
        if st.button(toggle_label, use_container_width=True, key="theme_toggle"):
            st.session_state.theme = "light" if mode == "dark" else "dark"
            st.rerun()
        st.markdown("---")

    with st.sidebar.expander("GPT settings", expanded=True):
        global k, ts, cs, web_mode, reasoning_effort, verbosity, do_stream 
        k = st.slider("Top-K chunks", 40, 100, 200)
        st.write('How many notes are fetched; higher finds more, risks clutter.')
        ts = st.slider("Max Text Recall Size", 40, 200, 400)
        st.write('Maximum text pulled per note; larger gives context, may distract.')
        cs = st.slider("Max Chars in Context Given to AI ", 500, 15000, 30000)
        st.write('Hard limit the model reads; everything must fit underneath.')
        web_mode = st.checkbox("Activate web search for Profile Creation", value=False)
        reasoning_effort = st.selectbox("Reasoning effort", ["minimal","low","medium","high"], index=2)
        verbosity = st.selectbox("Verbosity", ["low","medium","high"], index=1)
        do_stream = st.checkbox("Stream responses (UI only)", value=False)
        # save_toggle = st.checkbox("Auto-save last answer to Blob", value=False)
        # model_mod = st.checkbox("Use o3 in chat. Defined standard is GPT5.", value=False)
        # model_profile_mod = st.checkbox("Use GPT5 to create Company Profile. Defined standard is o3", value=False)

    with st.sidebar.expander("Recommended Questions", expanded=False):
        st.write('This section display a few ideas of questions to interact with the chatbot')
        st.write('Intructions: ')
        st.write('1. Select the first question to list company names')
        st.write("2. Inform the chatbot that you will be working with that company, like: 'Lets use the company company_name'")
        suggestions = [
            "Give me a list of company names available with annual report.",
            "Find any mentions of ESG strategy in the reports.",
            "Can you tell me the revenue for latest annual report",
            "What is the revenue growth of the company in the last two years",
            "What risks does the company highlight the most in the latest report?",
        ]
        for i, s in enumerate(suggestions):
            if st.button(s, key=f"sb_sugg_{i}", use_container_width=True):
                st.session_state.pending_prompt = s
                st.rerun()

    with st.sidebar.expander("Script Mod", expanded=False):
        st.title("Define system script:")
        st.write('Sets behavior, tone, safety; high-level rules the model follows.')
        st.session_state.sys_message_mod = st.text_area(
            "System", value=st.session_state.sys_message_mod, key="sys_ta"
        )
        st.title("Define developer script:")
        st.write('App-specific instructions and tools; override user phrasing when conflicting.')
        st.session_state.dev_message_mod = st.text_area(
            "Developer", value=st.session_state.dev_message_mod, key="dev_ta"
        )
        st.title("Define Company Profile script:")
        st.session_state.profile_mod = st.text_area(
            "Profile", value= st.session_state.profile_mod , key="pro_ta"
        )
        st.title("Define Company Profile Web script:")
        st.session_state.profile_mod_web = st.text_area(
            "Profile Web", value= st.session_state.profile_mod_web , key="prow_ta"
        )


    with st.sidebar.expander("Actions", expanded=False):
        st.write('List of possible actions by chat:')
        st.write('1. Create company profile.')
        st.write("To activate it you have to write: 'Create company profile of company_name with latest report'")
        st.write('2. Web Search')
        st.write("In order to activate this function, state clearly in the request 'use web search'")
        st.write('3. New Companies')
        st.write("This function allows you to add new data to the database. Use it by 'add company (companyNumber)', it needs to be the companyNumber of Company House.")
        st.write('Features in development:')
        st.write('1. Feed new file through chat to system')
        st.write('2. Generate Company Profile PowerPoint')

    with st.sidebar.expander("Feed Your PDF", expanded=False):
        # Allow one or more PDFs
        pdf_files = st.file_uploader(
            "Upload PDF file(s)",
            type=["pdf"],
            accept_multiple_files=True,
            key="pdf_uploader",
            help="Drop one or more PDF annual reports here.",
        )

        colA, colB = st.columns(2)
        with colA:
            run = st.button("Run ingestion", use_container_width=True, key="ingest_btn")
        with colB:
            clear = st.button("Clear PDFs", use_container_width=True, key="clear_pdfs")


        if run:
            if not pdf_files:
                st.warning("Please upload at least one PDF before running ingestion.")
            else:
                # Build bytes + names tuples for OCR engine
                files_bytes: Tuple[bytes, ...] = tuple(f.getvalue() for f in pdf_files)   # UploadedFile behaves like BytesIO. :contentReference[oaicite:3]{index=3}
                files_names: Tuple[str,  ...] = tuple(f.name for f in pdf_files)          # Filename via .name. :contentReference[oaicite:4]{index=4}

                # Run your OCR engine (synchronous here)
                chain, chain_src, timings = ocr_engine_cached_multi(files_bytes, files_names)
                st.session_state.ocr_chain = chain
                st.session_state.ocr_chain_with_sources = chain_src
                st.session_state.ocr_timings = timings

                # Flip flag, clear chat, set banner, and rerun
                st.session_state.pdf_mod = True
                st.session_state.history = []  # wipe prior chat so the banner is first
                st.session_state.just_ingested = True
                st.session_state.just_ingested_msg = "Your file have been ingested. Im ready for questions!"
                st.rerun()  # immediately rerun after ingestion. :contentReference[oaicite:5]{index=5}


        if clear and st.session_state.pdf_mod:
            # Reset everything related to PDF mode
            st.session_state.pdf_mod = False
            st.session_state.ocr_chain = None
            st.session_state.ocr_chain_with_sources = None
            st.session_state.ocr_timings = None
            st.session_state.history = []
            st.rerun()






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
    typed = st.chat_input(placeholder, key="dev_mode_chat")
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
# output_placeholder = st.empty()
# apply_theme(st.session_state.theme)
# if __name__ == "__main__":
#     main()
def render(**kwargs):
    # Use the real UI from this page
    return main()