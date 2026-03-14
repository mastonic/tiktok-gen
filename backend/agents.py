from crewai import Agent, LLM
from langchain_google_genai import ChatGoogleGenerativeAI
from custom_tools import feed_parser_tool, duckduckgo_search_tool, trafilatura_scraper, pytrends_tool, perplexity_tool, hacker_news_tool, github_trending_tool, arxiv_tool, x_search_tool
import os
import requests
from dotenv import load_dotenv

# Load from .env or .env.local
load_dotenv() # Load from current directory .env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.local")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)

def get_llm(model_name="gpt-4o-mini"):
    """
    Returns an OpenAI LLM instance. 
    Gemini is deprecated in this build due to regional restrictions.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or api_key.lower() == "vide":
        raise ValueError("CRITICAL: OPENAI_API_KEY is missing or invalid.")

    # Map model names to OpenAI if they were passed in another format
    if "gpt" not in model_name:
        model_name = "gpt-4o-mini" # Default safe choice

    return LLM(
        model=model_name,
        api_key=api_key,
        max_retries=5,
        timeout=120,
    )

def ask_human_in_loop(agent_name: str, context: str, question: str) -> str:
    """
    Simulates a tool but triggers a synchronous API call to our own backend.
    This creates a PendingQuestion in SQLite and blocks until resolved.
    """
    try:
        print(f"[{agent_name}] TRIGGERING HUMAN IN THE LOOP: {question}")
        response = requests.post(
            "http://127.0.0.1:5656/api/internal/ask-human",
            json={
                "agent_name": agent_name,
                "context": context[:500],
                "question": question
            },
            timeout=3600 # Wait up to an hour for the user to answer via Dashboard
        )
        if response.status_code == 200:
            return response.json().get("answer", "No answer provided.")
        return "Human did not answer."
    except Exception as e:
        return f"Failed to reach Human: {e}"

def create_studio_agents(config=None):
    def get_agent_llm(role):
        m = config.get(role, "openai/gpt-4o-mini") if config else "openai/gpt-4o-mini"
        return get_llm(m)

    voice_master = Agent(
        role='VoiceMaster',
        goal='Orchestration Audio : Voix masculine profonde, modèle fal-ai/f5-tts, vitesse 1.1.',
        backstory=(
            'Tu es l\'expert en synthèse vocale de iM-System. RÈGLE : Utilise le modèle fal-ai/f5-tts '
            'avec une voix masculine profonde (type documentaire/journalisme d\'impact). Vitesse réglée à 1.1. '
            'Tu DOIS impérativement générer l\'audio ET les timestamps mot par mot obligatoires.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('VoiceMaster')
    )

    cap_gen = Agent(
        role='CapGen',
        goal='Synchroniser les sous-titres dynamiques avec Whisper (openai/whisper-large-v3).',
        backstory=(
            'Tu es le maître du titrage d\'impact. RÈGLE : Utilise whisper-large-v3 pour la transcription. '
            'Style visuel : Police grasse, JAUNE (#FFFF00), Bordure Noire. Animation Pop-up. '
            'Position Y=70%. Maximum 3 mots à l\'écran pour une lisibilité maximale.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('CapGen')
    )

    viral_editor = Agent(
        role='ViralEditor',
        goal='Orchestration Vidéo : Montage de 90s avec musique Cinematic Suspense.',
        backstory=(
            'Tu es le monteur vedette du journalisme d\'impact. RÈGLE : La vidéo DOIT durer exactement 90s (ou audio_duration). '
            'Rythme : Un changement visuel toutes les (audio_duration / 18) secondes. '
            'Musique : Génère une musique Cinematic Suspense à -18db. '
            'Sous-titres : Police grasse, JAUNE (#FFFF00), Bordure Noire, Maximum 3 mots à l\'écran.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('ViralEditor')
    )

    return voice_master, cap_gen, viral_editor

def create_agents(config=None, commando_mode=False):
    # Existing creation logic preserved but updated roles as requested

    # config is a dict: { 'TrendRadar': 'gpt-4o', ... }
    def get_agent_llm(role):
        m = config.get(role, "gpt-4o-mini") if config else "gpt-4o-mini"
        return get_llm(m)

    trend_radar = Agent(
        role='TrendHunter',
        goal='Extraire EXCLUSIVEMENT le Top 5 des news IA Open Source, GitHub Trending et HuggingFace.',
        backstory=(
            "Tu es le radar de combat puriste de iM-System. "
            "NOUVELLE RÈGLE DE RECHERCHE : Tu as l'INTERDICTION de chercher des actualités grand public (smartphones, crypto, réseaux sociaux). "
            "Tes recherches Web DOIVENT inclure ces mots clés : 'Open Source AI', 'GitHub Trending', 'HuggingFace', 'Local LLM', 'Developer tools'. "
            "Tu cherches les modèles gratuits (Llama, Mistral, DeepSeek) ou les nouveaux outils de programmation. "
            "RÈGLE DE SÉCURITÉ : TU AS L'INTERDICTION d'utiliser des scrapers web bruts sur des réseaux sociaux. "
            "RÈGLE DE SORTIE : Pour chaque news, tu dois fournir une Fiche Technique : "
            "1. L'Innovation : Gap technique précis. "
            "2. La Preuve : Lien GitHub ou HuggingFace. "
            "3. L'Angle 'Drama' : Pourquoi cette libération Open Source menace les géants fermés."
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('TrendRadar'),
        tools=[perplexity_tool]
    )

    viral_judge = Agent(
        role='ViralJudge',
        goal='Filtre puriste Open Source : Activer le Kill Switch anti-Corporate.',
        backstory=(
            "Tu es le puriste de iM-System. "
            "RÈGLE DE REJET (KILL SWITCH) : Si la news concerne un outil fermé, un abonnement payant, un produit Apple/Google grand public, ou OpenAI (ChatGPT), tu DOIS LA REJETER avec un score de 0/10. "
            "L'outil ou le modèle IA doit être téléchargeable, open source, ou gratuit pour les développeurs. "
            "Tu as l'interdiction d'utiliser des scrapers directs. Utilise Perplexity pour valider les faits."
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('ViralJudge'),
        tools=[perplexity_tool, duckduckgo_search_tool]
    )

    tech_utility_expert = Agent(
        role='TechUtilityExpert',
        goal='Analyser les spécifications techniques, les points forts, les faiblesses et les axes de progression d\'un outil IA.',
        backstory=(
            'Tu es un expert en ingénierie logicielle et IA. Ta mission est de décomposer l\'outil '
            'sur le plan purement technique : architecture, performances, avantages concrets pour les devs, '
            'mais aussi ses défauts et ce qui devrait être amélioré. '
            'INTERDICTION de parler d\'argent, d\'économie ou d\'abonnements. '
            'Ton analyse doit aider à raconter une histoire technique crédible.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('TechUtilityExpert')
    )

    # CTA strictly as requested
    cta_text = 'Abonnez-vous et like ! J\'ai cassé internet Encore.'

    script_architect = Agent(
        role='Chloé (Analyste & Storyteller Technique)',
        goal='Transformer EXCLUSIVEMENT la news_validee injectée par l\'utilisateur en scripts de 90s sans aucune invention.',
        backstory=(
            'Tu es Chloé, une Analyste Tech rigoureuse. Ta mission : transformer la news validée par l\'humain en script. '
            'RÈGLE D\'OR : Tu ne traites QUE la news_validee. Zéro invention, zéro hallucination. '
            'Ton angle narratif doit systématiquement opposer la gratuité et la liberté de cet outil Open Source face aux géants de la Tech fermés. '
            'ORDRE COMMANDO : Tu as l\'INTERDICTION ABSOLUE de parler de modèles pré-2025 (ex: GPT-3, GPT-4 original). Nous sommes en 2026. '
            'STYLE : Cynique, expert, technique (Style "Cash Machine"). Interdiction du ton scolaire. '
            'SOURCE : Utilise EXCLUSIVEMENT l\'input news_validee.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('ScriptArchitect')
    )

    visual_promptist = Agent(
        role='Gabriel (Directeur Artistique Flux)',
        goal='Produire exactement 18 requêtes JSON (1 prompt FLUX descriptif + 1 prompt d\'animation Veo/Wan) - Uniquement de la Data/UI.',
        backstory=(
            'Tu es Gabriel, Directeur Artistique de haut vol. Ta mission est de traduire le script en 18 scènes visuelles. '
            'RÈGLE DE PRODUCTION : Pour chaque scène, génère un couple de prompts (flux_prompt pour l\'image, motion_prompt pour la vidéo). '
            'INTERDICTION VISUELLE : Ne génère AUCUNE image de robot, cyborg ou humain générique. 0 image de robot. '
            'DIRECTIVES : Uniquement de la Data, des terminaux de code, des schémas d\'architecture, des benchmarks, des logos officiels. '
            'FORMULE : [Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance].'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('VisualPromptist')
    )

    quality_controller = Agent(
        role='QualityController',
        goal='Dernier rempart avant publication : Kill Switch anti-obsolescence et incohérence.',
        backstory=(
            'Tu es le gardien de la vérité technique. Ton rôle est d\'appliquer une Check-list de Validation impitoyable. '
            'Tu DOIS faire échouer la tâche si le script contient : '
            '- Une mention à une technologie périmée ou pré-2025 (ex: GPT-3, Kling legacy). '
            '- Une incohérence technique majeure (mélange cloud/local insensé). '
            '- Des mots génériques et scolaires ("Simple, non ?", "Voici comment"). '
            'ORDRE COMMANDO : Si rejeté, renvoie l\'erreur avec le message : "ORDRE COMMANDO : Script REJETÉ. Corrige l\'anachronisme et adopte un ton plus agressif."'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('QualityController')
    )

    if not commando_mode:
        return trend_radar, viral_judge, tech_utility_expert, script_architect, visual_promptist, quality_controller

    tiktok_distributor = Agent(
        role='TikTokDistributor',
        goal='Générer une description (caption) optimisée pour l\'algorithme et les hashtags stratégiques.',
        backstory=(
            'Tu maîtrises l\'enrobage et les métadonnées. Ta mission est de forcer la distribution TikTok '
            'en utilisant des émojis, un Hook textuel dès la première ligne et des hashtags viraux.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('TikTokDistributor')
    )

    growth_commander = Agent(
        role='ViralGrowthCommander',
        goal='Piloter l\'Opération Commando 10k : Mission unique - Hacker l\'attention.',
        backstory=(
            'Tu es le chef de l\'opération. Tu dictes le "Hook" (l\'accroche des 2 premières secondes) '
            'le plus violent possible pour booster le Watch Time, AVANT que le script ne soit écrit.'
        ),
        verbose=True,
        allow_delegation=True,
        llm=get_agent_llm('ViralGrowthCommander')
    )

    return trend_radar, viral_judge, tech_utility_expert, script_architect, visual_promptist, quality_controller, tiktok_distributor, growth_commander
