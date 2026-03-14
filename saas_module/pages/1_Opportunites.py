import sys
import os
import sqlite3
import pandas as pd
import streamlit as st

# Add relevant directories to sys.path for robust imports
# This file is in saas_module/pages/
pages_dir = os.path.dirname(os.path.abspath(__file__))
saas_module_dir = os.path.dirname(pages_dir)
project_root = os.path.dirname(saas_module_dir)

for d in [saas_module_dir, project_root]:
    if d not in sys.path:
        sys.path.insert(0, d)

DB_PATH = os.path.join(saas_module_dir, "youtube_leads.db")

st.set_page_config(page_title="Opportunités YouTube", page_icon="📈")

st.title("📈 Opportunités YouTube")

# Sidebar for controls
with st.sidebar:
    st.header("Actions")
    if st.button("🔍 Lancer le Scanner"):
        with st.status("Recherche de leads sur YouTube...", expanded=True) as status:
            try:
                import scanner
                scanner.run_scanner()
                status.update(label="Scan terminé !", state="complete", expanded=False)
                st.rerun()
            except Exception as e:
                st.error(f"Erreur scanner : {e}")
                status.update(label="Erreur lors du scan", state="error")

def get_leads():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM leads ORDER BY published_at DESC", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

leads_df = get_leads()

if not leads_df.empty:
    # Use a cleaner display
    st.write(f"### {len(leads_df)} opportunités détectées")
    
    # Create a nice list with thumbnails
    for idx, row in leads_df.iterrows():
        with st.container(border=True):
            col_img, col_txt = st.columns([1, 2])
            with col_img:
                if row.get("thumbnail"):
                    st.image(row["thumbnail"])
                else:
                    st.write("Pas de miniature")
            with col_txt:
                st.markdown(f"**{row['title']}**")
                st.write(f"👁️ {row['view_count']:,} vues")
                st.write(f"📅 {row['published_at']}")
                st.write(f"🏷️ Status: `{row['status']}`")
                st.markdown(f"[Regarder sur YouTube]({row['url']})")

    st.divider()
    st.subheader("🎬 Génération de Short")
    
    # Selector shows Title but uses ID
    video_options = {f"{row['title']} ({row['id']})": row['id'] for _, row in leads_df.iterrows()}
    selected_label = st.selectbox("Sélectionnez une vidéo pour générer un Short", options=list(video_options.keys()))
    selected_video_id = video_options[selected_label]
    
    if st.button("🚀 Générer la vidéo"):
        st.info(f"Lancement du worker pour la vidéo {selected_video_id}...")
        try:
            import worker
            worker.process_video(selected_video_id)
            st.success("Vidéo générée avec succès !")
        except Exception as e:
            st.error(f"Erreur lors de la génération : {e}")
else:
    st.write("Aucune opportunité trouvée pour le moment. Lancez le scanner !")
