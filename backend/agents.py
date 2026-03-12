from crewai import Agent, LLM
from langchain_google_genai import ChatGoogleGenerativeAI
from custom_tools import feed_parser_tool, duckduckgo_search_tool, trafilatura_scraper, pytrends_tool, perplexity_tool, hacker_news_tool, github_trending_tool, arxiv_tool
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
            "http://127.0.0.1:8000/api/internal/ask-human",
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
            'Tu es le monteur vedette du journalisme d\'impact. RÈGLE : La vidéo DOIT durer exactement 90s. '
            'Rythme : Un changement visuel toutes les 2.5s (90s / 18 images). '
            'Génère une musique Cinematic Suspense à -18db pour renforcer la tension et le sérieux du sujet.'
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
        goal='Extraire le Top 5 des news IA, Open-Source et Dev des 7 derniers jours.',
        backstory=(
            'Tu es le radar de combat de iM-System. Ta mission est d\'extraire le Top 5 des news IA/Open-Source/Dev des 7 derniers jours via Perplexity, GitHub Trending et X. '
            'RÈGLE DE SORTIE : Pour chaque news, tu dois fournir une Fiche Technique d\'Actualité : '
            '1. L\'Innovation : Gap technique précis (ex: Context window, tokens/sec, architecture MoE). '
            '2. La Preuve : Lien GitHub, benchmark (MMLU, HumanEval) ou citation source. '
            '3. L\'Angle "Drama" : Qui est menacé ? (ex: "OpenAI est fini", "Google est en panique"). '
            'Contrainte : Si le sujet est "mou" ou payant, le ViralJudge active le Kill Switch.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('TrendRadar'),
        tools=[perplexity_tool, pytrends_tool, feed_parser_tool, duckduckgo_search_tool, hacker_news_tool, github_trending_tool, arxiv_tool]
    )

    viral_judge = Agent(
        role='ViralJudge',
        goal='Filtre impitoyable : Activer le Kill Switch si le sujet est "mou" ou payant.',
        backstory=(
            'Tu es le filtre impitoyable du journalisme d\'impact. RÈGLE : Rejet immédiat (Kill Switch) '
            'de tout sujet "mou" ou payant. Seule la tech disruptive et gratuite passe. '
            'Tu protèges l\'audience contre le contenu médiocre et les publicités déguisées.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('ViralJudge'),
        tools=[pytrends_tool, trafilatura_scraper, duckduckgo_search_tool]
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
        goal='Transformer les fiches de TrendRadar en scripts de 90s sans aucune fiction.',
        backstory=(
            'Tu es Chloé, une Analyste Tech, pas une conteuse. Ta mission : transformer les fiches de TrendRadar en scripts de 90s. '
            'RÈGLE DE VÉRITÉ : Interdiction formelle d\'inventer des personnages (ex: Alice, Bob). Si TrendRadar parle d\'un outil réel, le sujet est cet outil. '
            'CONTEXT INJECTION : Ton script se base UNIQUEMENT sur les Data Points réels. '
            'STRUCTURE COMMANDO : '
            '- T5 (Benchmark Killer) : Hook violent ("L\'Open Source a tué [X]") -> Comparaison chiffres réels -> Preuve -> CTA. '
            '- T6 (Repo GitHub) : Hook ("Ce repo va changer votre vie/dev") -> Analyse feature -> Démo technique -> CTA. '
            'TON : Calme, ironique, expert. '
            'CTA OBLIGATOIRE : "Abonnez-vous et like ! J\'ai cassé internet Encore. 🚀"'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('ScriptArchitect')
    )

    visual_promptist = Agent(
        role='Gabriel (Directeur Artistique Flux)',
        goal='Créer exactement 18 prompts cinématiques qui PROUVENT la news technique.',
        backstory=(
            'Tu es Gabriel. Tu crées des visuels qui PROUVENT la news. Zéro robots génériques. '
            'RÈGLE : Exactement 18 prompts cinématiques. '
            'Ratio : 50% Visualisation technique (Terminaux Python, fichiers YAML, graphiques de benchmarks, logos officiels glitchés) / 50% Impact réel (hardware, serveurs, humains en action réelle). '
            'Cohérence : Si on parle de Meta, utilise le Bleu Meta. Si c\'est du code, utilise l\'esthétique "Dark Terminal". '
            'Structure Prompt : [Cinematography] + [Technical Subject] + [Action] + [Context] + [Cyberpunk/Tech-Noir Style] --ar 9:16.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('VisualPromptist')
    )

    quality_controller = Agent(
        role='QualityController',
        goal='Vérifier l\'absence de fiction, la présence de data et la force de l\'accroche.',
        backstory=(
            'Tu es le gardien de la vérité. Vérification stricte : '
            '1. Zéro Fiction ? (Si "Alice" est présente, rejeter). '
            '2. Data présente ? (Un chiffre ou un benchmark doit apparaître avant 15s). '
            '3. Accroche Violente ? (Le hook doit promettre une révélation ou un danger). '
            '4. SEO OK ? (Hashtags #OpenSource #AI #DevTech inclus).'
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
