# --- env & path ---
import sys, pathlib, io, time, os
from dotenv import load_dotenv

load_dotenv()
repo_root = pathlib.Path.cwd().parent  # keep your original assumption
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# --- engine ---
from engines.engine import HybridEngine

pdf_path = repo_root / "engines" / "report.pdf"
with open(pdf_path, "rb") as f:
    pdf_bytes = io.BytesIO(f.read())

print(f"[DEBUG] Loading file: {pdf_path.name}, size={len(pdf_bytes.getbuffer())} bytes")
engine = HybridEngine()
engine.add_file(pdf_bytes, pdf_path.name)
print("[DEBUG] Running engine.main() ...")
engine.main()
print("[DEBUG] Engine build complete ✅")

# --- prompts & graph wiring ---
from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from engines.calc_prompt import calc_routing_system, Capital_Structure_Calculations

system_msg = (
    calc_routing_system
    + "\n\n"
    + Capital_Structure_Calculations
    + "\n\nIf pdf_search returns NO_MATCH, call web_search once; "
      "if web_search returns WEB_NO_RESULTS, say so and stop."
)

memory = MemorySaver()

class State(TypedDict):
    messages: Annotated[list, add_messages]

# --- tools ---
from openai import OpenAI
print("[DEBUG] OPENAI key present:", bool(os.getenv("OPENAI_API_KEY")))

@tool
def pdf_search(query: str) -> str:
    """Retrieve top snippets from the indexed PDFs for a query."""
    print(f"[DEBUG] pdf_search called with query: {query}")
    try:
        docs = engine.hybrid.get_relevant_documents(query)
        print(f"[DEBUG] Retrieved {len(docs)} docs from engine.hybrid")
    except Exception as e:
        print(f"[ERROR] pdf_search failed: {e}")
        return "NO_MATCH"
    if not docs:
        print("[DEBUG] No documents found for query")
        return "NO_MATCH"

    results = []
    for i, d in enumerate(docs[:3]):
        src = d.metadata.get("source", "unknown")
        text = (d.page_content or "").strip().replace("\n", " ")[:300]
        results.append(f"[{src}] {text}")
        print(f"[DEBUG] Snippet {i+1} from {src}: {text[:60]}...")
    output = "\n---\n".join(results)
    print(f"[DEBUG] Returning {len(results)} snippets")
    return output

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

@tool
def calc_script(data: str) -> str:
    """Stub for financial calculations tool."""
    print(f"[DEBUG] calc_script called with data: {data}")
    return "CALC_NOT_IMPLEMENTED"

tools = [pdf_search, web_search, calc_script]
print(f"[DEBUG] Registered tools: {[t.name for t in tools]}")
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools)
print("[DEBUG] LLM initialized and tools bound")

def chatbot(state: State) -> State:
    print(f"[DEBUG] Chatbot invoked with {len(state['messages'])} messages")
    ai_msg = llm_with_tools.invoke(state["messages"])
    print(f"[DEBUG] Chatbot produced message: {ai_msg}")
    return {"messages": [ai_msg]}

builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", tools_condition)
builder.add_edge("tools", "chatbot")
builder.add_edge("chatbot", END)
graph = builder.compile(checkpointer=memory)
print("[DEBUG] Graph compiled successfully ✅")

# --- runner ---
def ask(graph, msg: str, system_message: str) -> None:
    """Send one question and print route + last reply."""
    cfg = {"configurable": {"thread_id": f"cli-{int(time.time())}"}}
    state = {"messages": [
        {"role": "system", "content": system_message},
        {"role": "user", "content": msg},
    ]}
    out = graph.invoke(state, cfg)

    tools_called = []
    for m in out["messages"]:
        add = getattr(m, "additional_kwargs", None)
        if add and add.get("tool_calls"):
            tools_called += [tc.get("name") or (tc.get("function") or {}).get("name") for tc in add["tool_calls"]]
    route = (
        "CALC" if "calc_script" in tools_called
        else "WEB" if "web_search" in tools_called
        else "PDF" if "pdf_search" in tools_called
        else "NONE"
    )
    print(f"\nROUTE: {route} | TOOLS: {tools_called or '[]'}")
    print("\nASSISTANT:\n", out["messages"][-1].content)

if __name__ == "__main__":
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print("Usage: python run_pdf.py \"<your question>\"")
        sys.exit(0)

    # Debug retrieval step
    docs = engine.hybrid.get_relevant_documents(question)
    print(f"[DEBUG] Retrieved {len(docs)} docs")
    for d in docs[:3]:
        print("---")
        print(d.page_content[:300])

    
    ask(graph, question, system_msg)

