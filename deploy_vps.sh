#!/bin/bash

# ==============================================================================
# iM-System: MASTER VPS Deployment Script (FINAL URL FIX)
# ==============================================================================

set -e

# 1. Verification des fichiers
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Erreur : Dossiers non trouvés."
    exit 1
fi

# 2. Demander l'IP du VPS automatiquement
VPS_IP=$(curl -s ifconfig.me)
echo "🌐 Adresse IP détectée : $VPS_IP"

# 3. Charger les configurations existantes
if [ -f ".env.local" ]; then
    echo "📂 Récupération de la configuration existante..."
    while IFS='=' read -r key value; do
        if [[ ! $key =~ ^# && -n $key ]]; then
            export "$key=$value"
        fi
    done < .env.local
fi

# 4. Configuration Réseau et Domaines
echo ""
echo "⚙️  Configuration Réseau & Domaines"
echo "----------------------------------------------------------------"
read -p "Domaine principal [${FRONTEND_DOMAIN:-$VPS_IP}]: " NEW_FRONT
FRONTEND_DOMAIN=${NEW_FRONT:-${FRONTEND_DOMAIN:-$VPS_IP}}

read -p "Domaine API [${BACKEND_DOMAIN:-$VPS_IP}]: " NEW_BACK
BACKEND_DOMAIN=${NEW_BACK:-${BACKEND_DOMAIN:-$VPS_IP}}

read -p "Port API [${BACKEND_PORT:-5656}]: " NEW_PORT
BACKEND_PORT=${NEW_PORT:-${BACKEND_PORT:-5656}}

# NETTOYAGE : Enlever les http:// ou https:// si l'utilisateur les a collés
FRONTEND_DOMAIN=$(echo $FRONTEND_DOMAIN | sed -e 's|^[^/]*//||')
BACKEND_DOMAIN=$(echo $BACKEND_DOMAIN | sed -e 's|^[^/]*//||')

# 5. Clés API
echo ""
echo "🔑 Configuration des Clés API"
read -p "Enter GEMINI_API_KEY [${GEMINI_API_KEY:-vide}]: " NEW_GEMINI
GEMINI_API_KEY=${NEW_GEMINI:-$GEMINI_API_KEY}
read -p "Enter FAL_KEY [${FAL_KEY:-vide}]: " NEW_FAL
FAL_KEY=${NEW_FAL:-$FAL_KEY}

# 6. Détermination de l'URL API (CORRECTION ICI)
if [[ $BACKEND_DOMAIN =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    # Mode IP : HTTP OBLIGATOIRE sur port spécifique
    VITE_API_URL="http://${BACKEND_DOMAIN}:${BACKEND_PORT}"
else
    # Mode Domaine : HTTPS via Traefik
    VITE_API_URL="https://${BACKEND_DOMAIN}"
fi

# 7. Génération des fichiers .env
echo "📝 Génération de la configuration..."

# .env global (Utilisé par docker-compose)
cat <<EOT > .env
FRONTEND_DOMAIN=$FRONTEND_DOMAIN
BACKEND_DOMAIN=$BACKEND_DOMAIN
VITE_API_URL=$VITE_API_URL
TRAEFIK_NETWORK=n8n_default
EOT

# .env frontend (Crucial pour Vite)
cat <<EOT > frontend/.env
VITE_API_URL=$VITE_API_URL
EOT

# .env backend
cat <<EOT > backend/.env
GEMINI_API_KEY=$GEMINI_API_KEY
FAL_KEY=$FAL_KEY
PYTHONUNBUFFERED=1
EOT

# Sauvegarde pour la prochaine fois
cat <<EOT > .env.local
FRONTEND_DOMAIN=$FRONTEND_DOMAIN
BACKEND_DOMAIN=$BACKEND_DOMAIN
BACKEND_PORT=$BACKEND_PORT
GEMINI_API_KEY=$GEMINI_API_KEY
FAL_KEY=$FAL_KEY
EOT

# 8. Relance PROPRE
echo "🏗️  Relance des services..."
docker compose down || true
docker compose up --build -d

echo "----------------------------------------------------------------"
echo "✅ DEPLOYEMENT TERMINE !"
echo "----------------------------------------------------------------"
echo "👉 Dashboard : http://$FRONTEND_DOMAIN:3000"
echo "📡 API URL   : $VITE_API_URL"
echo "----------------------------------------------------------------"
