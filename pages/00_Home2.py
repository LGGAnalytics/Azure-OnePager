# app.py
import streamlit as st
import pandas as pd
from datetime import date, datetime
from io import StringIO

st.set_page_config(page_title="Oraculum", layout="wide")

# ------------ Pages --------------

home = st.Page("pages/00_Home2.py", title="Home", icon=":material/home:")
chat      = st.Page("pages/01_Chat_with_GPT5.py",      title="Open Chat",            icon=":material/smart_toy:")
profile   = st.Page("pages/02_Company_Profile.py",     title="Company Profile",      icon=":material/apartment:")
chouse    = st.Page("pages/03_Add_From_Company_House.py", title="Companies House",  icon=":material/account_balance:")
websearch = st.Page("pages/04_Web_Search.py",          title="Web Search",           icon=":material/travel_explore:")
pdf       = st.Page("pages/05_PDF.py",                 title="Chat with your PDF",   icon=":material/picture_as_pdf:")
dev       = st.Page("pages/06_DEV.py",                 title="Developer Mode",       icon=":material/terminal:")
autos     = st.Page("pages/07_Automations.py",         title="Automations",          icon=":material/robot_2:")


# ---------- Utils & State ----------
def init_state():
    if "records" not in st.session_state:
        st.session_state.records = []  # each item: dict with keys below

def to_df(records):
    if not records:
        return pd.DataFrame(columns=["date", "title", "notes", "tag"])
    df = pd.DataFrame(records)
    # Keep nice order and types
    if "date" in df:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    return df[["date", "title", "notes", "tag"]]

init_state()

# ---------- UI ----------
st.title("Oraculum")
st.caption("Developed by LGG Advisors Technologies.")
# --- 1) Welcome ---
# --- CSS to make big, pretty buttons just inside this gallery container ---
st.markdown("""
<style>
    #gallery div.stButton > button {
    width: 100%;
    padding: 1.1rem 1rem;
    border-radius: 1rem;
    font-size: 1.05rem;
    line-height: 1.4;
    height: 5.5rem;
    box-shadow: 0 4px 14px rgba(0,0,0,.08);
    border: 1px solid rgba(0,0,0,.08);
    }
    #gallery div.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 24px rgba(0,0,0,.12);
    }
    #gallery .subtitle {
    margin-top: .25rem;
    opacity: .75;
    font-size: .9rem;
    }
</style>
""", unsafe_allow_html=True)

apps = [
    {"label": "🌐  Open Chat",               "subtitle": "Chat UI and tools",       "page": chat},
    {"label": "🏢  Create Company Profile",  "subtitle": "Create & manage profiles","page": profile},
    {"label": "🏛️  Add from Companies House","subtitle": "Ingest new companies",   "page": chouse},
    {"label": "🔎  Web Search",              "subtitle": "Search + summarize",      "page": websearch},
    {"label": "📕  Chat with Your PDF",      "subtitle": "Ingest + chat",           "page": pdf},
    {"label": "💻  Developer Mode",          "subtitle": "Tweaking + chat",         "page": dev},
    {"label": "🤖  Create Automation",       "subtitle": "Not available yet",       "page": autos},
    ]
st.markdown('<div id="gallery">', unsafe_allow_html=True)
# 2x2 grid
for i in range(0, len(apps), 2):
    cols = st.columns(2)
    for col, app in zip(cols, apps[i:i+2]):
        with col:
            if st.button(app["label"], use_container_width=True):
                # Navigate to a "hidden" page (must exist in /pages)
                st.switch_page(app['page'])
            st.markdown(f'<div class="subtitle">{app["subtitle"]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# pg.run()