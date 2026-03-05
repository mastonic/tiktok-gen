#!/bin/bash
set -e

# 1. Verification
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Erreur : Dossiers non trouvés."
    exit 1
fi

# 2. IP Auto
VPS_IP=$(curl -s ifconfig.me)

# 3. Charger Clés
if [ -f ".env.local" ]; then
    source .env.local || true
fi

# 4. Config
echo "⚙️  Configuration IP Directe (FORCE HTTP)"
read -p "Domaine principal [${FRONTEND_DOMAIN:-$VPS_IP}]: " NEW_FRONT
FRONTEND_DOMAIN=${NEW_FRONT:-${FRONTEND_DOMAIN:-$VPS_IP}}

read -p "Domaine API [${BACKEND_DOMAIN:-$VPS_IP}]: " NEW_BACK
BACKEND_DOMAIN=${NEW_BACK:-${BACKEND_DOMAIN:-$VPS_IP}}

read -p "Port API [${BACKEND_PORT:-5656}]: " NEW_PORT
BACKEND_PORT=${NEW_PORT:-${BACKEND_PORT:-5656}}

# 5. Clés API
read -p "Enter GEMINI_API_KEY [${GEMINI_API_KEY:-vide}]: " NEW_GEMINI
GEMINI_API_KEY=${NEW_GEMINI:-$GEMINI_API_KEY}
read -p "Enter FAL_KEY [${FAL_KEY:-vide}]: " NEW_FAL
FAL_KEY=${NEW_FAL:-$FAL_KEY}

# 6. FORCE HTTP URL (Pas de HTTPS pour l'IP)
VITE_API_URL="http://${BACKEND_DOMAIN}:${BACKEND_PORT}"

# 7. Génération .env
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
GEMINI_API_KEY=$GEMINI_API_KEY
FAL_KEY=$FAL_KEY
PYTHONUNBUFFERED=1
EOT

cat <<EOT > .env.local
FRONTEND_DOMAIN=$FRONTEND_DOMAIN
BACKEND_DOMAIN=$BACKEND_DOMAIN
BACKEND_PORT=$BACKEND_PORT
GEMINI_API_KEY=$GEMINI_API_KEY
FAL_KEY=$FAL_KEY
EOT

# 8. Relance
echo "🏗️  Relance en mode HTTP..."
docker compose down || true
docker compose up --build -d

echo "----------------------------------------------------------------"
echo "✅ DEPLOYEMENT OK !"
echo "👉 Dashboard : http://$FRONTEND_DOMAIN:3000"
echo "📡 API URL   : $VITE_API_URL"
echo "----------------------------------------------------------------"
