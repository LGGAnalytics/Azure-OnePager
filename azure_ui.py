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


load_dotenv(find_dotenv(), override=True)
# =====================================================
# GPT TOOLS 
TOOLS = [{
    "type": "function",
    "function": {
        "name": "create_company_profile",
        "description": "Call when the user says something similar to: 'Create a company profile (CompanyName)'. Extract the name inside parentheses.",
        "parameters": {
            "type": "object",
            "properties": {"companyName": {"type": "string"}},
            "required": ["companyName"],
            "additionalProperties": False,
        },
    },
}]
# =====================================================

st.set_page_config(page_title="Oraculum v2", layout="wide")
st.title("📄 Oraculum v2.1 (Azure Version)")

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

with st.sidebar.expander("GPT settings", expanded=True):
    k = st.slider("Top-K chunks", 40, 100, 200)
    st.write('How many notes are fetched; higher finds more, risks clutter.')
    ts = st.slider("Max Text Recall Size", 40, 200, 400)
    st.write('Maximum text pulled per note; larger gives context, may distract.')
    cs = st.slider("Max Chars in Context Given to AI ", 500, 15000, 30000)
    st.write('Hard limit the model reads; everything must fit underneath.')
    web_mode = st.checkbox("Activate web search for Profile Creation", value=False)
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

            if web_mode:
                agent1 = profileAgentWeb(
                    company,
                    k=k, max_text_recall_size=ts, max_chars=cs, tool_choice={"type": "web_search"},
                    model=model_profile, profile_prompt=st.session_state.profile_mod_web
                )
            else:
                agent1 = WebAgent(
                    company,
                    k=k, max_text_recall_size=ts, max_chars=cs,
                    model=model_profile, profile_prompt=st.session_state.profile_mod
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
from gpts.gpt_assistants import question_to_machine

def stream_answer(prompt: str, chunks: int):
    # # 1) Retrieve
    # mode, hits = retrieve_hybrid_enhanced(prompt, k=chunks, max_text_recall_size=ts)

    # # 2) Show sources
    # with st.expander(f"Retrieved snippets / sources — mode: {mode}"):
    #     for i, h in enumerate(hits, 1):
    #         title    = h.get("title")
    #         chunk_id = h.get("chunk_id")
    #         raw_score = h.get("score")
    #         try:
    #             score = float(raw_score) if raw_score is not None else 0.0
    #         except (TypeError, ValueError):
    #             score = 0.0
    #         snippet  = (h.get(TEXT_FIELD) or "")
    #         snippet  = textwrap.shorten(snippet, width=800, placeholder=" ...")
    #         st.markdown(f"**[{i}]** *title:* `{title}` — *chunk_id:* `{chunk_id}` — *score:* {score:.4f}")
    #         st.write(snippet)


    # sys = st.session_state.sys_message_mod
    # ctx = build_context(hits, text_field=TEXT_FIELD, max_chars=cs)

    # messages = [
    #     {"role": "system", "content": sys},
    #     {"role": "user",   "content": f"Question:\n{prompt}\n\nContext snippets (numbered):\n{ctx}"},
    # ]

    # 3 Configure agent
    OPENAI_API_KEY  = os.getenv("FELIPE_OPENAI_API_KEY") 
    opt_user_query = question_to_machine(prompt, OPENAI_API_KEY)

    # 3. Call RAG
    mode, hits = retrieve_hybrid_enhanced(query=opt_user_query, top = 40, k = chunks, max_text_recall_size = ts)
    ctx = build_context(hits)
    # 4. Call model

    user_msg = f"Question:\n{opt_user_query}\n\nContext snippets (numbered):\n{ctx}"
    system_msg = """"

    You are a restructuring analyst focused on identifying companies in financial distress that could be advisory targets for your company. 
    You prepare comprehensive, accurate and full analysis of companies highlighting liquidity issues, debt maturity risks and covenant pressure. 
    You rely on annual reports and financial statements of companies.

    WHEN the information is NOT FOUND in the context, you USE WEB SEARCH

    **Formatting and Editorial Standards**: 
        - Always **cite sources** 
        - Generate complete profile directly in the chat, take your time and don't compress important things 
        - Always write dates in the format "Mmm-yy" (e.g. Jun-24), fiscal years as "FYXX" (e.g. FY24, LTM1H25), and currencies in millions in the format "£1.2m" 
        - Always double-check revenue split 

    """
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user",   "content": user_msg},
    ]
    
    agent = WebAgent(
        k=chunks,
        max_text_recall_size=ts,
        # max_chars=cs,
        model='gpt-5',          # your preconfigured model
        streaming=True
    )

    # 4) Stream the model answer
    # full = agent._answer(question = prompt, stream = True)

    st.markdown("### Answer")
    answer_box = st.empty()
    full = ""

    try:
        with agent.web_openai.responses.stream(
            model=agent.model,
            input=messages,
            tools=[{"type": "web_search"}],
            # tool_choice="auto",
            # max_output_tokens=ts,
            reasoning={"effort": "medium"},
            text={"verbosity": "medium"}
        ) as stream:
            for event in stream:
                if event.type == "response.output_text.delta":
                    piece = event.delta
                    if piece:
                        full += piece
                        answer_box.markdown(full)
                elif event.type == "response.error":
                    raise RuntimeError(str(event.error))
            final = stream.get_final_response()
            if not full:
                # fallback to final assembled text if no deltas arrived
                full = getattr(final, "output_text", "") or ""
                answer_box.markdown(full)
    except APIConnectionError:
        resp = agent.web_openai.responses.create(
            model=agent.model,
            input=messages,
        )
        full = getattr(resp, "output_text", "") or ""
        answer_box.markdown(full)

    # try:
    #     with agent.web_openai.responses.stream(
    #         model=agent.model,
    #         input=responses_input
    #     ) as stream:
    #         for event in stream:
    #             if event.type == "response.output_text.delta":
    #                 piece = event.delta
    #                 if piece:
    #                     full += piece
    #                     answer_box.markdown(full)
    #             elif event.type == "response.error":
    #                 raise RuntimeError(str(event.error))
    #         final = stream.get_final_response()
    #         if not full:
    #             # fallback to final assembled text if no deltas arrived
    #             full = getattr(final, "output_text", "") or ""
    #             answer_box.markdown(full)
    # except APIConnectionError:
    #     resp = agent.web_openai.responses.create(
    #         model=agent.model,
    #         input=responses_input,
    #     )
    #     full = getattr(resp, "output_text", "") or ""
    #     answer_box.markdown(full)

    # 5) Persist in chat history
    st.session_state.history.append({"q": prompt, "a": full})

# Render prior turns every run so the conversation persists
for turn in st.session_state.history:
    with st.chat_message("user"):
        st.write(turn["q"])
    with st.chat_message("assistant"):
        st.write(turn["a"])

# Accept either a typed prompt or an injected one from sidebar suggestions
typed = st.chat_input("Ask about the ingested PDFs…")
pending = st.session_state.pop("pending_prompt", None)
prompt = typed or pending

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        # Try tool routing first
        model_profile = "gpt-5" #if model_profile_mod else "o3"
        if check_actions(
                prompt, client, AOAI_DEPLOYMENT,
                k=k, ts=ts, cs=cs, model_profile=model_profile):
            pass
        else:
            stream_answer(prompt, k)
