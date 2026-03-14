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
st.write("Ce module gère la recherche automatique de vidéos virales et la génération de Shorts via IA.")

col1, col2 = st.columns(2)

with col1:
    st.info("### 🔍 Scanner")
    st.write("Rechercher les dernières tendances AI sur YouTube.")
    if st.button("Lancer un scan maintenant"):
        try:
            from saas_module import scanner
            scanner.run_scanner()
            st.success("Scan terminé ! Allez dans 'Opportunités' pour voir les résultats.")
        except Exception as e:
            st.error(f"Erreur : {e}")

with col2:
    st.info("### ⚙️ Automatisation")
    st.write("Actuellement : **Autopilote " + ("ON" if st.session_state.get('auto_mode', False) else "OFF") + "**")
    if st.button("Aller aux réglages"):
        st.switch_page("pages/2_Parametres.py")

if __name__ == "__main__":
    # This file is used for streamlit run saas_module/app.py
    pass
