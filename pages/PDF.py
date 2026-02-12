# 05 pdf
from io import BytesIO
from typing import Tuple, Annotated, TypedDict
import time
import streamlit as st
import sys, pathlib
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

repo_root = pathlib.Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# now imports from engines.* will work
from engines.prompts4 import system_mod, finance_calculations, section7
from engines.engine import HybridEngine


# Ensure repo root is importable
repo_root = pathlib.Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Engine
from engines.engine import HybridEngine

# LangGraph
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

# LangChain
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from langgraph.prebuilt import ToolNode, tools_condition

# Cache builder
# @st.cache_resource(show_spinner=False)  # disable while debugging
def ocr_engine_cached_multi(files_bytes: Tuple[bytes, ...], files_names: Tuple[str, ...]):
    pdf_streams = tuple((BytesIO(b), n) for b, n in zip(files_bytes, files_names))
    engine = HybridEngine(pdf_streams)
    t0 = time.perf_counter(); engine.main(); build_s = time.perf_counter() - t0
    txts = [engine._el_text(el).lower() for el in getattr(engine, "texts", [])]
    tbls = [engine._el_text(el).lower() for el in getattr(engine, "tables", [])]

    import re
    norm_txts = ["".join(re.findall(r"[a-z0-9]+", t.lower())) for t in txts]
    def has(token):
        return sum(token in s for s in norm_txts)

    # --- D1c: image probe (safe) ---
    imgs = getattr(engine, "images", [])
    st.write("[D1c] images count:", len(imgs))
    
    timings = getattr(engine, "timings", {})
    timings["total_build_s"] = build_s
    return engine, timings

# LangGraph builder
memory = MemorySaver()
class State(TypedDict):
    messages: Annotated[list, add_messages]

def build_graph(engine: HybridEngine):
    @tool
    def pdf_search(query: str) -> str:
        """Retrieve top snippets from the indexed PDFs for a query."""
        docs = engine.hybrid.get_relevant_documents(query)
        st.write(f"[DEBUG] pdf_search query: {query}")
        st.write(f"[DEBUG] Retrieved docs: {len(docs) if docs else 0}")
        st.write(f"[DEBUG] Tables detected: {len(getattr(engine, 'tables', []))}")
        if getattr(engine, "tables", None):
            # show a tiny preview so you know what shape came out
            st.write("[DEBUG] Table preview:", str(engine.tables[0])[:300])
        
        if docs:
            return "\n---\n".join([d.page_content[:500] for d in docs[:3]])
        
        #  Fallback: scan raw extracted text lines (only runs if retrieval missed)
        haystack = [engine._el_text(el) for el in getattr(engine, "texts", []) if el]
        import re
        q_tokens = query.lower().split()
        hits = []
        for line in haystack:
            l = line.strip()
            if not l:
                continue
            if any(tok in l.lower() for tok in q_tokens):
                if re.search(r"\d", l):  # lightly prefer lines with numbers
                    hits.append(l)

        if hits:
            st.write(f"[DEBUG] Fallback hits: {len(hits)}")
            return "\n".join(hits[:6])  # cap results

        return "NO_MATCH"
        
     
        
    @tool
    def web_search(query: str) -> str:
        """Use OpenAI Responses' built-in web_search to fetch up to 3 results.
        Format:
        [web] <title> — <one-line snippet> <url>
        If nothing found or on error, return WEB_NO_RESULTS.
        """
        print(f"[DEBUG] web_search called with query: {query}")
        try:
            client = OpenAI()
            resp = client.responses.create(
                model="gpt-5",
                tools=[{"type": "web_search"}],
                input=(
                    f"Search the web for: {query}\n"
                    "Return up to 3 bullets, each exactly as:\n"
                    "[web] <title> — <one-line snippet> <url>\n"
                    "If nothing is found, return exactly: WEB_NO_RESULTS"
                ),
            )
            text = (getattr(resp, "output_text", "") or "").strip()
            print("[DEBUG] responses output_text len:", len(text))
            if not text:
                return "WEB_NO_RESULTS"
            bullets = [ln.strip() for ln in text.split("\n") if ln.strip().startswith("[web] ")][:3]
            if not bullets:
                return "WEB_NO_RESULTS"
            print(f"[DEBUG] web_search returning {len(bullets)} results")
            return "\n---\n".join(bullets)
        except Exception as e:
            print(f"[ERROR] web_search failed: {e}")
            return "WEB_NO_RESULTS"
    from engines.calc_prompt import calc_routing_system, Capital_Structure_Calculations

    @tool
    def calc_script(data: str) -> str:
        """Financial calculations tool using predefined finance prompts."""
        prompt_text = (
            calc_routing_system
            + "\n\n"
            + Capital_Structure_Calculations
            + "\n\nUser input: " + data
        )
        llm = ChatOpenAI(model="gpt-5")
        resp = llm.invoke(prompt_text)
        return resp.content
    
    tools = [pdf_search, web_search, calc_script]
    llm = ChatOpenAI(model="gpt-5")
    llm_with_tools = llm.bind_tools(tools)

    llm_no_tools = ChatOpenAI(model="gpt-5")

    def chatbot(state: State) -> State:
        ai_msg = llm_with_tools.invoke(state["messages"])
        return {"messages": [ai_msg]}
    def finalize(state: State) -> State:
        # Compose a final answer without tools
        ai_msg = llm_no_tools.invoke(state["messages"])
        return {"messages": [ai_msg]}
    
    builder = StateGraph(State)
    builder.add_node("chatbot", chatbot)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "chatbot")
    builder.add_conditional_edges("chatbot", tools_condition)
    builder.add_edge("tools", "chatbot")                        
    builder.add_edge("chatbot", END)

    return builder.compile(checkpointer=memory)

def main():
    st.set_page_config(page_title="Oraculum")
    st.title("Oraculum")
    if st.session_state.get("processed", False):
        st.success("✅ OCR index ready — ask your question below.")
    else:
        st.info("📂 Upload a PDF and click **Build Index (OCR)** to start.")  # prove we rendered

    # Safe init
    defaults = {
        "ocr_mode": False,
        "text_engine": False,
        "processed": False,
        "ocr_engine": None,
        "graph": None,
        "ocr_timings": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ---- Sidebar chat history ----
    if "convos" not in st.session_state:
        st.session_state.convos = {} 
    if "current_cid" not in st.session_state:
        st.session_state.current_cid = None

    import uuid, time

    def _new_chat(title=None):
        cid = str(uuid.uuid4())[:8]
        st.session_state.convos[cid] = {
            "title": title or f"Chat {time.strftime('%H:%M')}",
            "messages": []
        }
        st.session_state.current_cid = cid
        st.session_state["messages"] = []  
        st.session_state["greeted"] = False 


        if not st.session_state.convos:
            _new_chat()

        ids = list(st.session_state.convos.keys())
        titles = [st.session_state.convos[c]["title"] for c in ids]

        sel = st.radio(
            "History",
            options=ids,
            index=ids.index(st.session_state.current_cid) if st.session_state.current_cid in ids else 0,
            format_func=lambda cid: st.session_state.convos[cid]["title"],
            label_visibility="collapsed"
        )

        if sel != st.session_state.current_cid:
            st.session_state.current_cid = sel
            st.session_state["messages"] = st.session_state.convos[sel]["messages"][:]

        if st.button("＋ New chat"):
            _new_chat()
            st.rerun()

    # 🔹 AUTO-GREETING FLAG
    if "greeted" not in st.session_state:
        st.session_state["greeted"] = False
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    # Greetings
    if (not st.session_state["greeted"]) and len(st.session_state["messages"]) == 0:
        st.session_state["messages"].append({
            "role": "assistant",
            "content": (
           "hey! 👋 what can i do for you today?\n– upload a pdf and i’ll analyze it\n– or ask me anything about your document"
            )
        })
        cid = st.session_state.get("current_cid")
        if cid:
            st.session_state.convos[cid]["messages"] = st.session_state["messages"][:]

        st.session_state["greeted"] = True
        
   # ====================== UI LAYOUT  ======================

    # ── Sidebar: Chats + Documents ──
    with st.sidebar:
        # Chats
        st.markdown("### Chats")
        if "convos" not in st.session_state:
            st.session_state.convos = {}
        if "current_cid" not in st.session_state:
            st.session_state.current_cid = None

        import uuid, time
        def _new_chat(title=None):
            cid = str(uuid.uuid4())[:8]
            st.session_state.convos[cid] = {"title": title or f"Chat {time.strftime('%H:%M')}",
                                            "messages": []}
            st.session_state.current_cid = cid
            st.session_state["messages"] = []
            st.session_state["greeted"] = False

        if not st.session_state.convos:
            _new_chat()

        ids = list(st.session_state.convos.keys())
        sel = st.radio(
            "History",
            options=ids,
            index=ids.index(st.session_state.current_cid) if st.session_state.current_cid in ids else 0,
            format_func=lambda cid: st.session_state.convos[cid]["title"],
            label_visibility="collapsed",
        )
        if sel != st.session_state.current_cid:
            st.session_state.current_cid = sel
            st.session_state["messages"] = st.session_state.convos[sel]["messages"][:]

        if st.button("＋ New chat"):
            _new_chat()
            st.rerun()

        st.markdown("---")

        # Documents
        st.markdown("### Documents")
        pdf_files = st.file_uploader("Upload PDF(s)", type=["pdf"], accept_multiple_files=True)

        if st.button("🔎 Build Index (OCR)", use_container_width=True):
            st.session_state["ocr_mode"] = True
            st.session_state["text_engine"] = False

        if st.session_state.get("ocr_mode", False) and pdf_files:
            files_bytes: Tuple[bytes, ...] = tuple(f.getvalue() for f in pdf_files)
            files_names: Tuple[str, ...] = tuple(f.name for f in pdf_files)

            if not st.session_state.get("processed", False):
                msg = st.empty()
                trail = st.empty()

                msg.info("Got it — reading your PDF... running OCR (page 1/N)")
                msg.info("Step: Uploading")
                msg.info("Step: OCR")
                with st.spinner("Running OCR on your PDFs..."):
                    try:
                        engine, timings = ocr_engine_cached_multi(files_bytes, files_names)
                    except Exception as e:
                        trail.text("Uploading → OCR → Indexing → Error")
                        st.error("Build failed"); st.exception(e); st.stop()

                msg.info("Step: Indexing")
                st.session_state.ocr_engine = engine
                st.session_state.ocr_timings = timings
                st.session_state.graph = build_graph(engine)

                if "thread_id" not in st.session_state or not st.session_state.thread_id:
                    st.session_state.thread_id = f"ui-{int(time.time())}"

                # Compact success + summary
                try:
                    eng = st.session_state.ocr_engine
                    first = ""
                    if getattr(eng, "texts", None):
                        first = eng._el_text(eng.texts[0])[:2000].lower()
                    pairs = [
                        (["form 10-k", "10-k", "annual report"], "an annual report (10-K)"),
                        (["10-q", "quarterly report"], "a quarterly report (10-Q)"),
                        (["earnings release", "press release"], "an earnings release"),
                        (["financial statements", "balance sheet", "income statement", "cash flows"], "financial statements"),
                        (["prospectus"], "a prospectus"),
                        (["invoice"], "an invoice"),
                        (["receipt"], "a receipt"),
                        (["contract", "agreement"], "a contract"),
                    ]
                    doc_type = next((label for kws, label in pairs if any(k in first for k in kws)), "a financial document")

                    import re
                    tokens = re.findall(r"[a-z]{4,}", first)
                    stops = set((
                        "the and for with from this that have has into over under our your their "
                        "consolidated company statement report annual quarterly cash flow income "
                        "balance notes management discussion analysis fiscal year quarter page item table figure appendix"
                    ).split())
                    freq = {}
                    for t in tokens:
                        if t in stops: continue
                        freq[t] = freq.get(t, 0) + 1
                    themes = [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:3]]
                    themes_str = ", ".join(themes) if themes else "—"

                    st.success(f"✅ OCR index ready — ask your question.\n\n"
                            f"This looks like {doc_type}. Main themes: {themes_str}.")
                except Exception:
                    st.success("✅ OCR index ready — ask your question.")
                trail.text("📤 Uploading → 🔎 OCR → 🗂️ Indexing → ✅ Ready")

                with st.expander("⚙️ Diagnostics", expanded=False):
                    st.json(st.session_state.get("ocr_timings", {}))
                    st.write("Texts:", len(engine.texts), "Tables:", len(engine.tables), "Images:", len(engine.images))
                st.session_state.processed = True


    # ── Main: Conversation (center) ──
    ready = st.session_state.get("graph") is not None

    # Suggested actions (chips)
    if ready:
        st.markdown("""
        <style>
        .qa-chips .stButton>button {
            border-radius: 9999px; padding: 6px 14px;
            border: 1px solid #D9DEE7; background: #F8FAFF;
            font-weight: 500; box-shadow: none;
        }
        .qa-chips .stButton>button:hover { background: #EEF4FF; border-color: #9BB8FF; }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("**Suggested actions**")
        st.markdown('<div class="qa-chips">', unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("📊 Key figures", key="qa_chip_1"):
                st.session_state["qa_input"] = "What are the key financial figures in this PDF?"
        with c2:
            if st.button("📑 Summary", key="qa_chip_2"):
                st.session_state["qa_input"] = "Summarize the main sections of this filing."
        with c3:
            if st.button("📈 Numbers & metrics", key="qa_chip_3"):
                st.session_state["qa_input"] = "Find important numbers and metrics with their page references."
        with c4:
            if st.button("⚖️ Financial ratios", key="qa_chip_4"):
                st.session_state["qa_input"] = "Calculate financial ratios like profitability, growth, and leverage."
        with c5:
            if st.button("🔍 Compare performance", key="qa_chip_5"):
                st.session_state["qa_input"] = "Compare this company’s performance with recent industry averages."
        st.markdown('</div>', unsafe_allow_html=True)

    # Chat input (simple; keep your existing process)
    chat_area = st.container()
    with st.form("qa_form", clear_on_submit=True):
        question = st.text_input(
            "Ask a question about your PDFs:",
            key="qa_input",
            disabled=not ready,
            placeholder=("Type a message…" if ready else "⬆️ Upload PDFs and click **Build Index (OCR)** to start"),
        )
        submitted = st.form_submit_button("Send", use_container_width=True, disabled=not ready)


    if submitted and question:
        # save user turn
        st.session_state["messages"].append({"role": "user", "content": question})
        cid = st.session_state.get("current_cid")
        if cid:
            st.session_state.convos[cid]["messages"] = st.session_state["messages"][:]

        state = {
            "messages": [
                {
                    "role": "system","content":( system_mod + "\n\n" + finance_calculations+
                    "\n\nTOOL POLICY (PDF-first, capped):\n"
                    "- Always start with `pdf_search` (call it once).\n"
                    "- If the PDF snippets don’t have the needed figures/page-citable details, "
                    "you MAY call `web_search` once (official sources preferred).\n"
                    "- After you have the figures, call `calc_script` once to compute ratios if needed.\n"
                    "- Allowed sequences per turn (max 3 total tool calls):\n"
                    "  1) pdf_search → calc_script\n"
                    "  2) pdf_search → web_search\n"
                    "  3) pdf_search → web_search → calc_script (only if truly necessary)\n"
                    "- After ANY tool call(s), your very next message MUST be the final answer (no more tools).\n"
                    "- Never fabricate numbers. Keep numerals intact (no broken/spaced digits). Cite page numbers or links.\n"
                    "- If both PDF and web fail to provide the needed numbers, say so plainly and stop.\n"
                    ),
                },
                {"role": "user", "content": f"{section7.strip()}\n\n{question}"}
            ]
        }

        try:
            out = st.session_state.graph.invoke(
                state,
                config={"configurable": {"thread_id": st.session_state.thread_id}, 
                 "recursion_limit": 30}
            )
            reply = out["messages"][-1].content
            st.session_state["messages"].append({"role": "assistant", "content": reply})
            cid = st.session_state.get("current_cid")
            if cid:
                st.session_state.convos[cid]["messages"] = st.session_state["messages"][:]
            
        except Exception as e:
            err_msg = str(e)
            if ("tool_call_id" in err_msg 
                or "An assistant message with 'tool_calls'" in err_msg
                or "did not have response messages" in err_msg):
                st.warning("⚠️ Session expired. I’ve reset your chat. Please try again.")
                st.session_state.thread_id = f"ui-{int(time.time())}"
            else:
                st.error("An unexpected error occurred.")
                st.exception(e)
    with chat_area:
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])



# Streamlit runs the script top-level, but keeping this is fine
# if __name__ == "__main__":
#     main()
def render(**kwargs):
    # Use the real UI from this page
    return main()