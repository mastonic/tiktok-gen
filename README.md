# 🚀 iM-System: Viral Video Factory (AI Swarm)

iM-System est une plateforme autonome de génération de vidéos virales (TikTok/Shorts) propulsée par un essaim d'agents IA (CrewAI) et des workflows de production visuelle de pointe.

## 🌟 Fonctionnalités

- **🧠 Multi-Agent Orchestration**: 5 agents spécialisés (TrendRadar, ViralJudge, MonetizationScorer, ScriptArchitect, QualityController) collaborent pour créer du contenu à fort potentiel.
- **🖼️ Workflow de Production Visuelle**:
    - **FLUX.1**: Génération d'images haute fidélité via Fal.ai.
    - **Kling / Luma**: Conversion d'images en clips vidéo cinématiques (5s).
    - **ElevenLabs / gTTS**: Synthèse vocale multilingue.
- **🎬 Assemblage Remotion**: Composition vidéo React-based avec sous-titres dynamiques style "TikTok" et rendu final via FFmpeg.
- **📈 Dashboard Analytics**: Suivi des performances, des coûts et pilotage de l'essaim en temps réel.

## 🏗️ Architecture

- **Backend**: FastAPI (Python 3.11), CrewAI, SQLite, FFmpeg.
- **Frontend**: React (Vite), TailwindCSS, Remotion Player.
- **Deployment**: Docker Compose, VPS Optimized.

---

## 🚀 Déploiement sur VPS (Hostinger, etc.)

Le script `deploy_vps.sh` est un "Master Script" qui peut tout gérer de A à Z, même sur un VPS vide.

### Option A : Déploiement en une étape (Recommandé)
Copiez simplement le script `deploy_vps.sh` sur votre VPS vide et lancez-le :
```bash
bash deploy_vps.sh
```
**Le script va :**
1. Installer **Git**, **FFmpeg**, **Docker** et **Python**.
2. Vous demander l'URL de ce dépôt et le **cloner** automatiquement.
3. Configurer vos clés API (**Gemini, OpenAI, Fal.ai, VEO**, etc.).
4. Lancer les containers via Docker Compose.

### Option B : Déploiement manuel
Si vous avez déjà cloné le projet :
```bash
git clone <votre-repo-url>
cd iM-System
bash deploy_vps.sh
```
Le script détectera les fichiers locaux et passera directement à l'installation des outils et containers.

### 📍 Accès
- **Dashboard**: `http://<VOTRE_IP>:3000`
- **Backend API**: `http://<VOTRE_IP>:8000`

---

## 🛠️ Développement Local

1. Installez les dépendances backend :
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Installez les dépendances frontend :
```bash
cd frontend
npm install
```

3. Lancez le serveur unifié :
```bash
./start_servers.sh
```

---

## 🔑 Clés API Requises
Pour que tous les workflows fonctionnent, assurez-vous de configurer les clés suivantes via le script de déploiement ou un fichier `.env` :
- `GEMINI_API_KEY` (Essaim d'agents)
- `FAL_KEY` (Image / Vidéo / FLUX.1)
- `OPENAI_API_KEY` (Fallback LLM)
- `VEO_API_KEY` (Google Veo)
- `ELEVENLABS_API_KEY` (Voix premium)

---

## 🛡️ License
Projet privé - iM-System.
