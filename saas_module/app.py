import sys
import os

# Add relevant directories to sys.path for robust imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for d in [current_dir, parent_dir]:
    if d not in sys.path:
        sys.path.insert(0, d)

import streamlit as st

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
            import scanner
            scanner.run_scanner()
            st.success("Scan terminé ! Allez dans 'Opportunités' pour voir les résultats.")
        except Exception as e:
            st.error(f"Erreur : {e}")

with col2:
    st.info("### ⚙️ Automatisation")
    st.write("Actuellement : **Autopilote " + ("ON" if st.session_state.get('auto_mode', False) else "OFF") + "**")
    if st.button("Aller aux réglages"):
        st.switch_page("pages/2_Parametres.py")

st.divider()

# Section : Vidéos générées aujourd'hui
st.subheader("🎬 Vidéos générées aujourd'hui")

OUTPUT_DIR = os.path.join(current_dir, "outputs")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

import datetime

# Liste des fichiers MP4 triés par date de création (plus récent d'abord)
videos = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp4")]
videos.sort(key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x)), reverse=True)

if videos:
    cols = st.columns(3)
    for idx, video_file in enumerate(videos):
        video_path = os.path.join(OUTPUT_DIR, video_file)
        ctime = os.path.getmtime(video_path)
        date_str = datetime.datetime.fromtimestamp(ctime).strftime("%H:%M:%S")
        
        # Filtre par jour (optionnel, ici on montre tout l'historique récent)
        with cols[idx % 3]:
            st.video(video_path)
            st.caption(f"🕒 Libéré à {date_str} - `{video_file}`")
else:
    st.write("C'est bien calme ici... Générez votre premier Short depuis l'onglet 'Opportunités' !")

if __name__ == "__main__":
    # This file is used for streamlit run saas_module/app.py
    pass
