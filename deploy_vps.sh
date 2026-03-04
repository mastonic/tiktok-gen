#!/bin/bash

# ==============================================================================
# iM-System: MASTER VPS Deployment Script (Git + Docker + Workflows)
# ==============================================================================

set -e

echo "----------------------------------------------------------------"
echo "�� iM-System: Starting FULL VPS Installation"
echo "----------------------------------------------------------------"

# 1. Install Basic Tools (Git, etc.)
echo "📦 Installing system tools..."
sudo apt-get update
sudo apt-get install -y git curl ffmpeg python3 python3-pip

# 2. Handle Git Cloning
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo ""
    echo "📥 Project not found locally. Let's clone it!"
    read -p "Enter your GitHub Repo URL (e.g., https://github.com/user/repo.git): " REPO_URL
    
    if [ -z "$REPO_URL" ]; then
        echo "❌ Error: Repo URL is required to proceed."
        exit 1
    fi

    PROJECT_NAME=$(basename "$REPO_URL" .git)
    echo "Cloning $PROJECT_NAME..."
    git clone "$REPO_URL"
    cd "$PROJECT_NAME"
else
    echo "✅ Project files detected. Skipping clone."
fi

# 3. Install Docker & Docker Compose
echo "🐳 Installing Docker & Compose..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

if ! docker compose version &> /dev/null; then
    sudo apt-get install -y docker-compose-plugin
fi

# 4. Prepare Directories for Persistence
echo "📂 Preparing persistent storage..."
mkdir -p backend/media
touch backend/db.sqlite3
chmod -R 777 backend/media
chmod 666 backend/db.sqlite3

# 5. Collect Configuration & API Keys
echo ""
echo "🔑 Configuration: iM-System Setup"
echo "----------------------------------------------------------------"

read -p "Enter GEMINI_API_KEY: " GEMINI_API_KEY
read -p "Enter OPENAI_API_KEY (optional): " OPENAI_API_KEY
read -p "Enter FAL_KEY: " FAL_KEY
read -p "Enter VEO_API_KEY: " VEO_API_KEY
read -p "Enter HF_TOKEN: " HF_TOKEN
read -p "Enter ELEVENLABS_API_KEY (optional): " ELEVENLABS_API_KEY
read -p "Enter VPS Public IP or Domain (e.g., 123.45.67.89): " VPS_IP

if [ -z "$VPS_IP" ]; then
    echo "❌ Error: VPS IP is mandatory for the Frontend communication."
    exit 1
fi

# 6. Generate Environment Files
echo "📝 Generating .env files..."
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

# 7. Launch System
echo "🏗️ Building and launching Docker containers..."
export VITE_API_URL="http://$VPS_IP:8000"

docker compose down || true
docker compose up --build -d

echo "----------------------------------------------------------------"
echo "✅ TOTAL DEPLOYMENT SUCCESSFUL!"
echo "----------------------------------------------------------------"
echo "📍 Dashboard: http://$VPS_IP:3000"
echo "📡 API:       http://$VPS_IP:8000"
echo ""
echo "Manage your system:"
echo "- Logs:    docker compose logs -f"
echo "- Restart: docker compose restart"
echo "- Stop:    docker compose down"
echo "----------------------------------------------------------------"
