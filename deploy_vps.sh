#!/bin/bash

# ==============================================================================
# iM-System: MASTER VPS Deployment Script (IP DIRECT MODE + API KEY MEMORY)
# ==============================================================================

set -e

# 1. Verification des fichiers
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Erreur : Dossiers non trouvés."
    exit 1
fi

# 2. Demander l'IP du VPS
VPS_IP=$(curl -s ifconfig.me)
echo "🌐 Adresse IP détectée : $VPS_IP"

# 3. Charger les clés existantes si elles existent
if [ -f ".env.local" ]; then
    echo "📂 Récupération des clés existantes depuis .env.local..."
    source .env.local || true
fi

# 4. Clés API (avec valeurs par défaut)
echo "🔑 Configuration des Clés API"
read -p "Enter GEMINI_API_KEY [${GEMINI_API_KEY:-vide}]: " NEW_GEMINI
GEMINI_API_KEY=${NEW_GEMINI:-$GEMINI_API_KEY}

read -p "Enter FAL_KEY [${FAL_KEY:-vide}]: " NEW_FAL
FAL_KEY=${NEW_FAL:-$FAL_KEY}

# 5. Génération de la configuration (IP DIRECTE)
echo "📝 Génération de la configuration IP..."

# .env global
cat <<EOT > .env
FRONTEND_DOMAIN=$VPS_IP
BACKEND_DOMAIN=$VPS_IP
VITE_API_URL=http://$VPS_IP:8000
TRAEFIK_NETWORK=n8n_default
EOT

# .env frontend
cat <<EOT > frontend/.env
VITE_API_URL=http://$VPS_IP:8000
EOT

# .env backend
cat <<EOT > backend/.env
GEMINI_API_KEY=$GEMINI_API_KEY
FAL_KEY=$FAL_KEY
PYTHONUNBUFFERED=1
EOT

# Sauvegarder pour la prochaine fois
cat <<EOT > .env.local
GEMINI_API_KEY=$GEMINI_API_KEY
FAL_KEY=$FAL_KEY
EOT

# 6. Création des dossiers storage
mkdir -p backend/media
touch backend/db.sqlite3
chmod -R 777 backend/media
chmod 666 backend/db.sqlite3

# 7. Relance PROPRE
echo "🏗️  Relance des services..."
docker compose down || true
docker compose up --build -d

echo "----------------------------------------------------------------"
echo "✅ DEPLOYEMENT REUSSI !"
echo "----------------------------------------------------------------"
echo "👉 Dashboard : http://$VPS_IP:3000"
echo "📡 API       : http://$VPS_IP:8000"
echo "----------------------------------------------------------------"
