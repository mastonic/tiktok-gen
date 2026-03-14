#!/bin/bash
# Deployment script for saas_module

echo "🚀 Déploiement du module SaaS..."

# 🛠️ Installation des dépendances dans un environnement virtuel
if [ ! -d "venv_saas" ]; then
    echo "🌐 Création de l'environnement virtuel venv_saas..."
    python3 -m venv venv_saas
fi

echo "🔌 Activation de l'environnement virtuel..."
source venv_saas/bin/activate

if [ -f "requirements.txt" ]; then
    echo "📦 Installation des dépendances..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# 🔑 Vérification des clés API
if [ ! -f "../.env.local" ]; then
    echo "⚠️ Attention : .env.local non trouvé dans le répertoire parent."
else
    echo "✅ Environnement local détecté."
    # Export vars from .env.local for streamlit
    export $(grep -v '^#' ../.env.local | xargs)
fi

# 🏗️ Lancement de Streamlit
echo "🖥️ Lancement du Dashboard..."
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
