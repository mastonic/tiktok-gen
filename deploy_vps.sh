#!/bin/bash

# ==============================================================================
# iM-System: MASTER VPS Deployment Script (Traefik Fix)
# ==============================================================================

set -e

# 1. Verification des fichiers
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Erreur : Dossiers non trouvés. Merci de lancer le script dans le dossier du projet."
    exit 1
fi

# 2. Configuration Traefik
echo "⚙️  Configuration Traefik"
read -p "Domaine principal (ex: m.srv1146904.hstgr.cloud): " FRONTEND_DOMAIN
read -p "Domaine API (ex: api.srv1146904.hstgr.cloud): " BACKEND_DOMAIN
read -p "Réseau Traefik (souvent 'n8n_default' ou 'traefik_network'): " TRAEFIK_NETWORK
TRAEFIK_NETWORK=${TRAEFIK_NETWORK:-n8n_default}

# 3. Clés API
echo "🔑 Clés API"
read -p "Enter GEMINI_API_KEY: " GEMINI_API_KEY
read -p "Enter FAL_KEY: " FAL_KEY

# 4. Génération des fichiers de config
echo "📝 Génération de la configuration..."

# .env global pour Docker Compose
cat <<EOT > .env
FRONTEND_DOMAIN=$FRONTEND_DOMAIN
BACKEND_DOMAIN=$BACKEND_DOMAIN
VITE_API_URL=https://$BACKEND_DOMAIN
TRAEFIK_NETWORK=$TRAEFIK_NETWORK
EOT

# .env spécifique au Backend
cat <<EOT > backend/.env
GEMINI_API_KEY=$GEMINI_API_KEY
FAL_KEY=$FAL_KEY
PYTHONUNBUFFERED=1
EOT

cp backend/.env .env.local

# 5. Création des dossiers storage
mkdir -p backend/media
touch backend/db.sqlite3
chmod -R 777 backend/media
chmod 666 backend/db.sqlite3

# 6. Relance PROPRE
echo "🏗️  Relance des services..."
docker compose down || true
docker compose up --build -d

echo "----------------------------------------------------------------"
echo "✅ Mise à jour terminée."
echo "Si le domaine ne marche pas encore, essaie l'IP directement :"
echo "http://$(curl -s ifconfig.me):3000"
echo "----------------------------------------------------------------"
