#!/bin/bash
# Deployment script for saas_module

echo "🚀 Déploiement du module SaaS..."

# 🛠️ Installation des dépendances si nécessaire
if [ -f "requirements.txt" ]; then
    echo "📦 Installation des dépendances..."
    pip install -r requirements.txt
fi

# 🔑 Vérification des clés API
if [ ! -f "../.env.local" ]; then
    echo "⚠️ Attention : .env.local non trouvé dans le répertoire parent."
else
    echo "✅ Environnement local détecté."
fi

# 🏗️ Lancement de Streamlit
echo "🖥️ Lancement du Dashboard..."
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
