#!/bin/bash

# ==============================================================================
# iM-System: MASTER VPS Deployment Script with TRAEFIK Integration (FIXED TLS)
# ==============================================================================

set -e

echo "----------------------------------------------------------------"
echo "🚀 iM-System: Starting VPS Deployment (with Traefik Support)"
echo "----------------------------------------------------------------"

# 1. Verification des fichiers (Clonage si nécessaire)
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "📥 Projet non détecté. Vous devez cloner votre repo d'abord."
    read -p "URL de votre Repo GitHub: " REPO_URL
    git clone "$REPO_URL"
    PROJECT_NAME=$(basename "$REPO_URL" .git)
    cd "$PROJECT_NAME"
fi

# 2. Configuration spécifique à Traefik
echo ""
echo "⚙️  Configuration du Proxy Traefik"
echo "----------------------------------------------------------------"
read -p "Domaine principal (ex: m.srv123.hstgr.cloud): " FRONTEND_DOMAIN
read -p "Domaine API (ex: api.srv123.hstgr.cloud): " BACKEND_DOMAIN
read -p "Réseau Docker utilisé par n8n/traefik (probablement 'n8n_default'): " TRAEFIK_NETWORK
TRAEFIK_NETWORK=${TRAEFIK_NETWORK:-n8n_default}

# 3. Collecte des Clés API
echo ""
echo "🔑 Configuration des Clés API"
read -p "Enter GEMINI_API_KEY: " GEMINI_API_KEY
read -p "Enter OPENAI_API_KEY: " OPENAI_API_KEY
read -p "Enter FAL_KEY: " FAL_KEY
read -p "Enter VEO_API_KEY: " VEO_API_KEY
read -p "Enter HF_TOKEN: " HF_TOKEN
read -p "Enter ELEVENLABS_API_KEY (optional): " ELEVENLABS_API_KEY

# 4. Preparation de la persistence
echo "📂 Preparation du stockage..."
mkdir -p backend/media
touch backend/db.sqlite3
chmod -R 777 backend/media
chmod 666 backend/db.sqlite3

# 5. Generation du fichier .env pour le backend
echo "📝 Generation de .env..."
cat <<EOT > backend/.env
GEMINI_API_KEY=$GEMINI_API_KEY
GOOGLE_API_KEY=$GEMINI_API_KEY
OPENAI_API_KEY=$OPENAI_API_KEY
FAL_KEY=$FAL_KEY
VEO_API_KEY=$VEO_API_KEY
HF_TOKEN=$HF_TOKEN
ELEVENLABS_API_KEY=$ELEVENLABS_API_KEY
PYTHONUNBUFFERED=1
EOT

cp backend/.env .env.local

# 6. Lancement avec Traefik
echo "🏗️  Déploiement via Traefik..."
export FRONTEND_DOMAIN=$FRONTEND_DOMAIN
export BACKEND_DOMAIN=$BACKEND_DOMAIN
export TRAEFIK_NETWORK=$TRAEFIK_NETWORK

# Nous injectons les variables directement dans docker-compose
# On utilise HTTPS pour le frontend si on a un domaine
export VITE_API_URL="https://$BACKEND_DOMAIN"

docker compose down || true
docker compose up --build -d

echo "----------------------------------------------------------------"
echo "✅ DEPLOYEMENT TERMINE AVEC SUCCES!"
echo "----------------------------------------------------------------"
echo "🌐 Dashboard: https://$FRONTEND_DOMAIN"
echo "📡 Backend API: https://$BACKEND_DOMAIN"
echo "----------------------------------------------------------------"
