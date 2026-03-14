import streamlit as st
import json
import os

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "..", "settings.json")

st.set_page_config(page_title="Paramètres", page_icon="⚙️")

st.title("⚙️ Paramètres")

def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        return {"auto_mode": False}
    with open(SETTINGS_PATH, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)

settings = load_settings()

auto_mode = st.toggle("Full-Auto Mode", value=settings.get("auto_mode", False))

if auto_mode != settings.get("auto_mode", False):
    settings["auto_mode"] = auto_mode
    save_settings(settings)
    st.toast(f"Mode Auto {'activé' if auto_mode else 'désactivé'}")

st.write("---")
st.write(f"Fichier de configuration : `{SETTINGS_PATH}`")
