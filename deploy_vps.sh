#!/bin/bash
set -e

# 1. Verification
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Erreur : Dossiers non trouvés."
    exit 1
fi

# 2. IP Auto
VPS_IP=$(curl -s ifconfig.me)

# 3. Charger Clés existantes
if [ -f ".env.local" ]; then
    # Nettoyage des retours à la ligne Windows possibles
    sed -i 's/\r//' .env.local
    source .env.local || true
fi

# 4. Config
echo "⚙️  Configuration IP Directe (Nettoyage des Ports)"
echo "----------------------------------------------------------------"
read -p "Domaine principal [${FRONTEND_DOMAIN:-$VPS_IP}]: " NEW_FRONT
FRONTEND_DOMAIN=${NEW_FRONT:-${FRONTEND_DOMAIN:-$VPS_IP}}

read -p "Domaine API [${BACKEND_DOMAIN:-$VPS_IP}]: " NEW_BACK
BACKEND_DOMAIN=${NEW_BACK:-${BACKEND_DOMAIN:-$VPS_IP}}

read -p "Port API [${BACKEND_PORT:-5656}]: " NEW_PORT
BACKEND_PORT=${NEW_PORT:-${BACKEND_PORT:-5656}}

# NETTOYAGE CRITIQUE : Enlever protocoles ET ports déjà présents dans les domaines
FRONTEND_DOMAIN=$(echo $FRONTEND_DOMAIN | sed -e 's|^[^/]*//||' -e 's|:.*||')
BACKEND_DOMAIN=$(echo $BACKEND_DOMAIN | sed -e 's|^[^/]*//||' -e 's|:.*||')

# 5. Clés API
read -p "Enter GEMINI_API_KEY [${GEMINI_API_KEY:-vide}]: " NEW_GEMINI
GEMINI_API_KEY=${NEW_GEMINI:-$GEMINI_API_KEY}
read -p "Enter FAL_KEY [${FAL_KEY:-vide}]: " NEW_FAL
FAL_KEY=${NEW_FAL:-$FAL_KEY}

# 6. CONSTRUCTION PROPRE DE L'URL
VITE_API_URL="http://${BACKEND_DOMAIN}:${BACKEND_PORT}"

# 7. Génération .env
echo "📝 Génération de la configuration propre..."

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

# Sauvegarde propre
cat <<EOT > .env.local
FRONTEND_DOMAIN=$FRONTEND_DOMAIN
BACKEND_DOMAIN=$BACKEND_DOMAIN
BACKEND_PORT=$BACKEND_PORT
GEMINI_API_KEY=$GEMINI_API_KEY
FAL_KEY=$FAL_KEY
EOT

# 8. Relance
echo "��️  Relance sur l'URL : $VITE_API_URL"
docker compose down || true
docker compose up --build -d

echo "----------------------------------------------------------------"
echo "✅ DEPLOYEMENT OK ! (Port corrigé)"
echo "👉 Dashboard : http://$FRONTEND_DOMAIN:3000"
echo "📡 API URL   : $VITE_API_URL"
echo "----------------------------------------------------------------"
