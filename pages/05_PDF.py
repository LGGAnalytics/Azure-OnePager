from io import BytesIO
from typing import Tuple, Annotated, TypedDict
import time
import streamlit as st
import sys, pathlib
from openai import OpenAI


# Ensure repo root is importable
repo_root = pathlib.Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Engine
from engines.engine import HybridEngine

# LangGraph
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

# LangChain
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# Cache builder
# @st.cache_resource(show_spinner=False)  # disable while debugging
def ocr_engine_cached_multi(files_bytes: Tuple[bytes, ...], files_names: Tuple[str, ...]):
    pdf_streams = tuple((BytesIO(b), n) for b, n in zip(files_bytes, files_names))
    engine = HybridEngine(pdf_streams)
    t0 = time.perf_counter(); engine.main(); build_s = time.perf_counter() - t0
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
        if not docs:
            return "NO_MATCH"
        return "\n---\n".join([d.page_content[:500] for d in docs[:3]])
        
        
    
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

    def chatbot(state: State) -> State:
        ai_msg = llm_with_tools.invoke(state["messages"])
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
    st.write("✅ App booted")  # prove we rendered

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

    st.write(
        "Available engines: \n"
        "1. Text Engine (fast, text-only; multi-PDF) \n"
        "2. OCR Engine (hybrid OCR; multi-PDF)\n"
        "Upload one or more PDFs and select an engine."
    )

    pdf_files = st.file_uploader("Upload your PDF(s)", type=["pdf"], accept_multiple_files=True)
    col1, col2 = st.columns(2)
    if col1.button("OCR Engine"):
        st.session_state.update({"ocr_mode": True, "text_engine": False, "processed": False})

    # --- OCR Engine (multi-file) ---
    if st.session_state.get("ocr_mode", False) and pdf_files:
        files_bytes: Tuple[bytes, ...] = tuple(f.getvalue() for f in pdf_files)
        files_names: Tuple[str, ...] = tuple(f.name for f in pdf_files)

        if not st.session_state.get("processed", False):
            with st.spinner("Building OCR (hybrid) index across all PDFs..."):
                try:
                    engine, timings = ocr_engine_cached_multi(files_bytes, files_names)
                    st.session_state.ocr_engine = engine
                    st.session_state.ocr_timings = timings
                    st.session_state.graph = build_graph(engine)
                    if "thread_id" not in st.session_state or not st.session_state.thread_id:
                        import time
                        st.session_state.thread_id = f"ui-{int(time.time())}"
                    st.success("OCR index ready.")
                    st.json(st.session_state.get("ocr_timings", {})) # to be removed later
                    st.write("Texts:", len(engine.texts), "Tables:", len(engine.tables), "Images:", len(engine.images)) # to be removed later
                    st.session_state.processed = True
                except Exception as e:
                    st.error("Build failed")
                    st.exception(e)
                    return

        st.subheader("Timings")
        st.json(st.session_state.get("ocr_timings", {}))

        question = st.text_input("Ask a question about your PDFs:")
        if question:
            state = {
                "messages": [
                    {
                        "role": "system",
                        "content":(
                            "You are a financial assistant. "
                            "For any question about the uploaded PDFs, you must always call the `pdf_search` tool first. "
                            "Only if it returns NO_MATCH may you call `web_search`. "
                            "Use `calc_script` only when a numeric result must be computed from retrieved figures. "
                            "Once you receive tool results, compose a final answer and STOP CALLING TOOLS for this turn. "
                            "If a tool returns NO_MATCH or WEB_NO_RESULTS, state that clearly and STOP."
                           
                            )
                    },
                    {"role": "user", "content": question},
                ]
            }

            try:
                out = st.session_state.graph.invoke(
                    state,
                    {"configurable": {"thread_id": st.session_state.thread_id}}
                    )
                st.write(out["messages"][-1].content)
                st.write("[DEBUG] Assistant reply (first 200 chars):", out["messages"][-1].content[:200])
            except Exception as e:
                err_msg = str(e)
                if ("tool_call_id" in err_msg 
                    or "An assistant message with 'tool_calls'" in err_msg
                    or "did not have response messages" in err_msg):
                    st.warning("⚠️ Session expired. I’ve reset your chat. Please try again.")
                    # Reset the thread so the next run starts clean
                    import time
                    st.session_state.thread_id = f"ui-{int(time.time())}"
                else:
                    st.error("An unexpected error occurred.")
                    st.exception(e)  # optional: log details for yourself



# Streamlit runs the script top-level, but keeping this is fine
if __name__ == "__main__":
    main()
