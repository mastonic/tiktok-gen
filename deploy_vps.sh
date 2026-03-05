#!/bin/bash

# ==============================================================================
# iM-System: MASTER VPS Deployment Script (FULL REMEMBER MODE)
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

# 3. Charger les configurations existantes si elles existent
if [ -f ".env.local" ]; then
    echo "📂 Récupération de la configuration existante..."
    # On source le fichier pour charger les variables en mémoire
    # On utilise un pipe while pour éviter les problèmes de caractères spéciaux
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

read -p "Réseau Traefik [${TRAEFIK_NETWORK:-n8n_default}]: " NEW_NET
TRAEFIK_NETWORK=${NEW_NET:-${TRAEFIK_NETWORK:-n8n_default}}

# 5. Clés API
echo ""
echo "🔑 Configuration des Clés API"
echo "----------------------------------------------------------------"
read -p "Enter GEMINI_API_KEY [${GEMINI_API_KEY:-vide}]: " NEW_GEMINI
GEMINI_API_KEY=${NEW_GEMINI:-$GEMINI_API_KEY}

read -p "Enter FAL_KEY [${FAL_KEY:-vide}]: " NEW_FAL
FAL_KEY=${NEW_FAL:-$FAL_KEY}

read -p "Enter OPENAI_API_KEY [${OPENAI_API_KEY:-vide}]: " NEW_OPENAI
OPENAI_API_KEY=${NEW_OPENAI:-$OPENAI_API_KEY}

read -p "Enter VEO_API_KEY [${VEO_API_KEY:-vide}]: " NEW_VEO
VEO_API_KEY=${NEW_VEO:-$VEO_API_KEY}

read -p "Enter HF_TOKEN [${HF_TOKEN:-vide}]: " NEW_HF
HF_TOKEN=${NEW_HF:-$HF_TOKEN}

read -p "Enter ELEVENLABS_API_KEY [${ELEVENLABS_API_KEY:-vide}]: " NEW_ELEVEN
ELEVENLABS_API_KEY=${NEW_ELEVEN:-$ELEVENLABS_API_KEY}

# 6. Détermination de l'URL API (HTTPS si domaine, HTTP si IP)
if [[ $BACKEND_DOMAIN =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    # C'est une IP
    VITE_API_URL="http://$BACKEND_DOMAIN:8000"
else
    # C'est un domaine
    VITE_API_URL="https://$BACKEND_DOMAIN"
fi

# 7. Génération de la configuration
echo ""
echo "📝 Génération des fichiers .env..."

# .env global pour Docker Compose
cat <<EOT > .env
FRONTEND_DOMAIN=$FRONTEND_DOMAIN
BACKEND_DOMAIN=$BACKEND_DOMAIN
VITE_API_URL=$VITE_API_URL
TRAEFIK_NETWORK=$TRAEFIK_NETWORK
EOT

# .env frontend
cat <<EOT > frontend/.env
VITE_API_URL=$VITE_API_URL
EOT

# .env backend
cat <<EOT > backend/.env
GEMINI_API_KEY=$GEMINI_API_KEY
OPENAI_API_KEY=$OPENAI_API_KEY
FAL_KEY=$FAL_KEY
VEO_API_KEY=$VEO_API_KEY
HF_TOKEN=$HF_TOKEN
ELEVENLABS_API_KEY=$ELEVENLABS_API_KEY
PYTHONUNBUFFERED=1
EOT

# Sauvegarder absolument TOUT dans .env.local pour la prochaine fois
cat <<EOT > .env.local
FRONTEND_DOMAIN=$FRONTEND_DOMAIN
BACKEND_DOMAIN=$BACKEND_DOMAIN
TRAEFIK_NETWORK=$TRAEFIK_NETWORK
GEMINI_API_KEY=$GEMINI_API_KEY
OPENAI_API_KEY=$OPENAI_API_KEY
FAL_KEY=$FAL_KEY
VEO_API_KEY=$VEO_API_KEY
HF_TOKEN=$HF_TOKEN
ELEVENLABS_API_KEY=$ELEVENLABS_API_KEY
EOT

# 8. Création des dossiers storage
mkdir -p backend/media
touch backend/db.sqlite3
chmod -R 777 backend/media
chmod 666 backend/db.sqlite3

# 9. Relance PROPRE
echo "🏗️  Relance des services avec Docker Compose..."
docker compose down || true
docker compose up --build -d

echo "----------------------------------------------------------------"
echo "✅ CONFIGURATION TERMINEE !"
echo "----------------------------------------------------------------"
echo "🌐 Interface : $VITE_API_URL (si domaine) ou http://$FRONTEND_DOMAIN:3000 (si IP)"
echo "📡 Backend   : $VITE_API_URL"
echo "----------------------------------------------------------------"
