#!/bin/bash

# ==============================================================================
# iM-System: MASTER VPS Deployment Script (IP DIRECT MODE)
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

# 3. Clés API
echo "🔑 Configuration des Clés API"
read -p "Enter GEMINI_API_KEY: " GEMINI_API_KEY
read -p "Enter FAL_KEY: " FAL_KEY

# 4. Génération de la configuration (IP DIRECTE)
echo "📝 Génération de la configuration IP..."

# .env global
cat <<EOT > .env
FRONTEND_DOMAIN=$VPS_IP
BACKEND_DOMAIN=$VPS_IP
VITE_API_URL=http://$VPS_IP:8000
TRAEFIK_NETWORK=n8n_default
EOT

# .env frontend (pour être sûr que Vite le voit)
cat <<EOT > frontend/.env
VITE_API_URL=http://$VPS_IP:8000
EOT

# .env backend
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

# 6. Relance PROPRE (On expose les ports 3000 et 8000)
echo "🏗️  Relance des services sur les ports 3000 et 8000..."
docker compose down || true
docker compose up --build -d

echo "----------------------------------------------------------------"
echo "✅ DEPLOYEMENT IP DIRECT REUSSI !"
echo "----------------------------------------------------------------"
echo "👉 Dashboard : http://$VPS_IP:3000"
echo "📡 API       : http://$VPS_IP:8000"
echo "----------------------------------------------------------------"
echo "ATTENTION : Utilise bien l'URL http://$VPS_IP:3000 (pas de HTTPS)"
echo "----------------------------------------------------------------"
