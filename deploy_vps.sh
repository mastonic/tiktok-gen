#!/bin/bash
set -e

# 1. Verification
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Erreur : Dossiers non trouvés." exit 1
fi

# 2. Réseau Docker
docker network create n8n_default || true

# 3. IP Auto
VPS_IP=$(curl -s ifconfig.me)

# 4. Charger Clés existantes
if [ -f ".env.local" ]; then
    sed -i 's/\r//' .env.local
    source .env.local || true
fi

# 5. Config
echo "⚙️  Configuration IP Directe"
read -p "Domaine principal (ex: crewai972.xyz) [${FRONTEND_DOMAIN:-$VPS_IP}]: " NEW_FRONT
FRONTEND_DOMAIN=${NEW_FRONT:-${FRONTEND_DOMAIN:-$VPS_IP}}

# Suggest api.domain if frontend is not an IP
SUGGESTED_BACK=${BACKEND_DOMAIN}
if [[ ! $FRONTEND_DOMAIN =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    SUGGESTED_BACK="api.${FRONTEND_DOMAIN}"
fi

read -p "Domaine API (ex: api.crewai972.xyz) [${SUGGESTED_BACK:-$VPS_IP}]: " NEW_BACK
BACKEND_DOMAIN=${NEW_BACK:-${SUGGESTED_BACK:-$VPS_IP}}
read -p "Port API [${BACKEND_PORT:-5656}]: " NEW_PORT
BACKEND_PORT=${NEW_PORT:-${BACKEND_PORT:-5656}}

# Nettoyage
FRONTEND_DOMAIN=$(echo $FRONTEND_DOMAIN | sed -e 's|^[^/]*//||' -e 's|:.*||')
BACKEND_DOMAIN=$(echo $BACKEND_DOMAIN | sed -e 's|^[^/]*//||' -e 's|:.*||')

# 6. Clés API
read -p "Enter OPENAI_API_KEY [${OPENAI_API_KEY:-vide}]: " NEW_OPENAI
OPENAI_API_KEY=${NEW_OPENAI:-$OPENAI_API_KEY}
read -p "Enter GEMINI_API_KEY [${GEMINI_API_KEY:-vide}]: " NEW_GEMINI
GEMINI_API_KEY=${NEW_GEMINI:-$GEMINI_API_KEY}
read -p "Enter FAL_KEY [${FAL_KEY:-vide}]: " NEW_FAL
FAL_KEY=${NEW_FAL:-$FAL_KEY}
read -p "Enter PERPLEXITY_API_KEY [${PERPLEXITY_API_KEY:-vide}]: " NEW_PERPLEXITY
PERPLEXITY_API_KEY=${NEW_PERPLEXITY:-$PERPLEXITY_API_KEY}

# 7. CONSTRUCTION URL
if [[ $BACKEND_DOMAIN =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    VITE_API_URL="http://${BACKEND_DOMAIN}:${BACKEND_PORT}"
else
    VITE_API_URL="https://${BACKEND_DOMAIN}"
fi

# 8. Génération .env
cat <<EOT > .env
FRONTEND_DOMAIN=$FRONTEND_DOMAIN
BACKEND_DOMAIN=$BACKEND_DOMAIN
VITE_API_URL=$VITE_API_URL
TRAEFIK_NETWORK=n8n_default
EOT

cat <<EOT > frontend/.env
VITE_API_URL=$VITE_API_URL
EOT

cat <<EOT > backend/.env
OPENAI_API_KEY=$OPENAI_API_KEY
GEMINI_API_KEY=$GEMINI_API_KEY
FAL_KEY=$FAL_KEY
PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY
PYTHONUNBUFFERED=1
EOT

cat <<EOT > .env.local
FRONTEND_DOMAIN=$FRONTEND_DOMAIN
BACKEND_DOMAIN=$BACKEND_DOMAIN
BACKEND_PORT=$BACKEND_PORT
OPENAI_API_KEY=$OPENAI_API_KEY
GEMINI_API_KEY=$GEMINI_API_KEY
FAL_KEY=$FAL_KEY
PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY
EOT

# 9. Relance
echo "🏗️  Nettoyage et Relance..."
docker compose down || true
# Force removal of frontend/backend images to ensure fresh build
docker rmi im-system-frontend im-system-backend || true
docker compose up --build -d

echo "----------------------------------------------------------------"
echo "✅ DÉPLOYÉ SUR : https://$FRONTEND_DOMAIN"
echo "📡 API SUR : $VITE_API_URL"
echo "----------------------------------------------------------------"
