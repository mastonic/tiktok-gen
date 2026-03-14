import streamlit as st
import sqlite3
import os
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "youtube_leads.db")

st.set_page_config(page_title="Opportunités YouTube", page_icon="📈")

st.title("📈 Opportunités YouTube")

# Sidebar for controls
with st.sidebar:
    st.header("Actions")
    if st.button("🔍 Lancer le Scanner"):
        with st.status("Recherche de leads sur YouTube...", expanded=True) as status:
            try:
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                from saas_module import scanner
                scanner.run_scanner()
                status.update(label="Scan terminé !", state="complete", expanded=False)
                st.rerun()
            except Exception as e:
                st.error(f"Erreur scanner : {e}")
                status.update(label="Erreur lors du scan", state="error")

def get_leads():
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM leads ORDER BY published_at DESC", conn)
    conn.close()
    return df

leads_df = get_leads()

if not leads_df.empty:
    st.dataframe(leads_df, use_container_width=True)
    
    selected_video_id = st.selectbox("Sélectionnez une vidéo pour générer un Short", leads_df["id"].tolist())
    
    if st.button("Générer la vidéo"):
        st.info(f"Lancement du worker pour la vidéo {selected_video_id}...")
        try:
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from saas_module import worker
            worker.process_video(selected_video_id)
            st.success("Vidéo générée avec succès !")
        except Exception as e:
            st.error(f"Erreur lors de la génération : {e}")
else:
    st.write("Aucune opportunité trouvée pour le moment. Lancez le scanner !")
