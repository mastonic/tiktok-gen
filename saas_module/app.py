import streamlit as st
import os

st.set_page_config(
    page_title="iM-System SaaS Dashboard",
    page_icon="🤖",
    layout="wide"
)

st.sidebar.title("iM-System SaaS")
st.sidebar.info("Module Scanner YouTube + Worker OpenAI")

st.title("Bienvenue sur le Dashboard SaaS")
st.write("Utilisez le menu latéral pour naviguer entre les opportunités et les paramètres.")

if __name__ == "__main__":
    # This file is used for streamlit run saas_module/app.py
    pass
