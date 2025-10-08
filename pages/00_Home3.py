import sys, pathlib, importlib
import streamlit as st
from uuid import uuid4 
from pages.design.dialogues import *
from theme_mod import apply_theme

from pages.design.func_tools import tile
from azure.blob_functions import get_companies


if "history" not in st.session_state:
    st.session_state.history = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "thread_id_pdf" not in st.session_state:               
    st.session_state.thread_id_pdf = str(uuid4())

if "convos" not in st.session_state:
    cid = str(uuid4())
    st.session_state.convos = {cid: {"title": "New chat", "messages": []}}
    st.session_state.current_cid = cid

# ---------- page / theme ----------
apply_theme("light")
st.set_page_config(page_title="Oraculum", layout="wide")

# ---------- default route: open chat ----------
if "active_tile" not in st.session_state or not st.session_state.active_tile:
    st.session_state.active_tile = "chat"  # default landing

# ---------- icons ----------
def ic_search():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="7" stroke="#2563EB" stroke-width="1.6"/><path d="M20 20l-3.5-3.5" stroke="#2563EB" stroke-width="1.6" stroke-linecap="round"/></svg>'

def ic_pdf():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M7 3h7l5 5v13H7z" stroke="#2563EB" stroke-width="1.6"/><path d="M14 3v5h5" stroke="#2563EB" stroke-width="1.6"/></svg>'

def ic_dev():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M8 9l-4 3 4 3M16 9l4 3-4 3" stroke="#2563EB" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def ic_auto():
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3" stroke="#2563EB" stroke-width="1.6"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2" stroke="#2563EB" stroke-width="1.6" stroke-linecap="round"/></svg>'


# ---------- ROW: four tiles ----------
c1, c2, c3, c4 = st.columns(4, gap="small")
with c1: tile("Chat with Your PDF", "Upload reports and analyze", ic_pdf(), "pdf")
with c2: tile("Web Search", "Search the web and summarize", ic_search(), "web")
with c3: tile("Developer Mode", "Access advanced API features", ic_dev(), "dev")
with c4: tile("Create Automation", "Set up automated workflows", ic_auto(), "auto")


# ---------- Chat History----------
with st.sidebar:
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

# ===========================
# CHAT AREA (compact welcome + history)
# ===========================


# show a small one-time welcome *bubble* when conversation is empty
if not messages:  # first time in this chat
    with st.chat_message("assistant"):
        _ , names = get_companies()
        st.markdown(
            f"{greeting_1}\n\n" + "\n".join(f"- {n}" for n in names)
        )
    st.session_state.greeted = True

# render history
for msg in messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# one input at the bottom (single source of truth)
typed = st.chat_input("Type your message here...", key="main_chat")
injected = st.session_state.pop("pending_prompt", None)
query = injected or typed



# ---------- QUICK ACTIONS ----------
if "prefill" not in st.session_state:
    st.session_state.prefill = ""

st.markdown("**Quick actions**")
qa_cols = st.columns(6)


with qa_cols[0]:
    if st.button("🔵 Extract Key Figures", key="qa_figs"):
        st.session_state.prefill = (
            "Can you extract the key financial figures from the uploaded PDF, "
            "including Revenue, Gross Profit, Operating Income, Net Income, EPS, "
            "Cash Flow, Total Assets, and Liabilities?"
        )

with qa_cols[1]:
    if st.button("📑 Summarize Overview", key="qa_overview"):
        st.session_state.prefill = (
            "Can you give me a concise business overview of the company from the PDF? "
            "Please include what the company does, main products/services, geographies, "
            "key business units, and strategy themes."
        )

with qa_cols[2]:
    if st.button("🗞️ Show Recent News", key="qa_news"):
        st.session_state.prefill = (
            "Can you show me recent news (last 90 days) about this company with dates, titles, "
            "short takeaways, and links if possible?"
        )

# --- Felipe’s future actions (not available now) ---
if st.button("📋 List Companies", key="qa_list_companies"):
    st.info("📋 List Companies — not available now")
    _ , names = get_companies()
    with st.chat_message("assistant"):
        st.markdown(
            f"{companies_available}\n\n" + "\n".join(f"- {n}" for n in names)
        )

with qa_cols[4]:
    if st.button("✚ Add Company", key="qa_add_company"):
        st.info("✚ Add Company — not available now")

with qa_cols[5]:
    if st.button("⚙️ Create Profile", key="qa_create_profile"):
        st.info("⚙️ Create Profile — not available now")