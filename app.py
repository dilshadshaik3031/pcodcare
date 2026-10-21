"""
PCODCare website.

Run:  streamlit run app.py
"""
import streamlit as st

import style

st.set_page_config(page_title="PCODCare: understand your PCOD risk earlier", page_icon="🌸", layout="wide",
                   initial_sidebar_state="collapsed")
style.apply()

nav = st.navigation([
    st.Page("home.py", title="Home", default=True),
    st.Page("screening.py", title="Risk Check"),
    st.Page("learn.py", title="Learn"),
    st.Page("lifestyle.py", title="Diet & Exercise"),
    st.Page("resources.py", title="Resources"),
    st.Page("about.py", title="About"),
    st.Page("evaluation.py", title="Evaluation"),
], position="hidden")
nav.run()