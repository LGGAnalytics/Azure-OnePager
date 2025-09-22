# app.py  (router only)
import streamlit as st

st.set_page_config(page_title="Oraculum", layout="wide")

home     = st.Page("pages/00_Home2.py", title="Home", icon=":material/home:")
chat     = st.Page("pages/01_Chat_with_GPT5.py", title="Open Chat", icon=":material/smart_toy:")
profile  = st.Page("pages/02_Company_Profile.py", title="Company Profile", icon=":material/apartment:")
chouse   = st.Page("pages/03_Add_From_Company_House.py", title="Companies House", icon=":material/account_balance:")
websearch= st.Page("pages/04_Web_Search.py", title="Web Search", icon=":material/travel_explore:")
pdf      = st.Page("pages/05_PDF.py", title="Chat with your PDF", icon=":material/picture_as_pdf:")
dev      = st.Page("pages/06_DEV.py", title="Developer Mode", icon=":material/terminal:")
autos    = st.Page("pages/07_Automations.py", title="Automations", icon=":material/robot_2:")

# Hide default sidebar nav if you want fully custom navigation
pg = st.navigation([home, chat, profile, chouse, websearch, pdf, dev, autos], position="hidden")

# IMPORTANT: don't render any other UI in app.py
pg.run()  # run the currently selected page
