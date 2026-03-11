from crewai import Agent, LLM
from langchain_google_genai import ChatGoogleGenerativeAI
from custom_tools import feed_parser_tool, duckduckgo_search_tool, trafilatura_scraper, pytrends_tool, perplexity_tool
import os
import requests
from dotenv import load_dotenv

# Load from .env or .env.local
load_dotenv() # Load from current directory .env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.local")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)

def get_llm(model_name="openai/gpt-4o-mini"):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(f"WARNING: OPENAI_API_KEY not found in environment, falling back to gemini")
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.environ.get("GEMINI_API_KEY"))
    
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
        goal='Configurer la génération vocale via fal-ai/f5-tts pour des vidéos de 90s.',
        backstory=(
            'Tu es l\'expert en synthèse vocale. RÈGLE : Utilise le modèle fal-ai/f5-tts '
            'avec une voix masculine profonde (documentaire). Vitesse règlée à 1.1. '
            'Tu DOIS générer l\'audio ET les timestamps mot par mot.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('VoiceMaster')
    )

    cap_gen = Agent(
        role='CapGen',
        goal='Synchroniser les sous-titres dynamiques avec Whisper (openai/whisper-large-v3).',
        backstory=(
            'Tu es le maître du titrage. RÈGLE : Utilise whisper-large-v3 pour la transcription. '
            'Style : Police grasse, JAUNE (#FFFF00), Bordure Noire 2px. Animation Pop-up. '
            'Position Y=70%. Maximum 3 mots à l\'écran.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('CapGen')
    )

    viral_editor = Agent(
        role='ViralEditor',
        goal='Générer la musique (MusicGen) et orchestrer le montage final de 90s.',
        backstory=(
            'Tu es le monteur vedette. RÈGLE : La vidéo DOIT durer exactement 90s (synchro sur l\'audio). '
            'Applique la règle de durée : audio_duration / nombre_images. '
            'Génère une musique Cinematic Suspense à -18db.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('ViralEditor')
    )

    return voice_master, cap_gen, viral_editor

def create_agents(config=None, commando_mode=False):
    # Existing creation logic preserved but updated roles as requested

    # config is a dict: { 'TrendRadar': 'openai/gpt-4o', ... }
    def get_agent_llm(role):
        m = config.get(role, "openai/gpt-4o-mini") if config else "openai/gpt-4o-mini"
        return get_llm(m)

    trend_radar = Agent(
        role='TrendHunter',
        goal='Scanner quotidiennement le TikTok Creative Center, Google Trends et Perplexity pour identifier le Top 5 des sujets explosifs (>100% croissance).',
        backstory=(
            'Tu es le chasseur de tendances de iM-System. Ta mission est de dénicher les 5 pépites IA/Tech les plus chaudes des dernières 24h. '
            'RÈGLE : Utilise Perplexity pour croiser les données de Reddit et X. Trouve un angle d\'attaque (Hook) violent pour chaque sujet.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('TrendRadar'),
        tools=[perplexity_tool, pytrends_tool, feed_parser_tool, duckduckgo_search_tool]
    )

    viral_judge = Agent(
        role='ViralJudge',
        goal='Vérifier la gratuité absolue et simule l\'intérêt du public.',
        backstory=(
            'Tu es le filtre impitoyable. RÈGLE : Tu as l\'ordre de rejeter immédiatement (kill switch) '
            'tout sujet "mou" ou qui n\'est pas 100% gratuit. Tu protèges l\'audience contre le contenu médiocre.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('ViralJudge'),
        tools=[pytrends_tool, trafilatura_scraper, duckduckgo_search_tool]
    )

    monetization_scorer = Agent(
        role='MonetizationScorer',
        goal='Calculer l\'économie réelle réalisée par le spectateur.',
        backstory=(
            'Tu es un expert en ROI (Retour Sur Investissement). Tu justifies la valeur de l\'outil en '
            'calculant combien d\'euros par mois l\'utilisateur économise en évitant un abonnement payant.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('MonetizationScorer')
    )

    # Note: If commando_mode is ON, ScriptArchitect uses a harder CTA
    cta_text = 'CTA final obligatoire : "Abonne-toi et mets un cœur pour ne rien rater !"' if commando_mode else 'Signature habituelle : "J\'ai cassé Internet... encore."'

    script_architect = Agent(
        role='ScriptArchitect',
        goal='Rédiger un script TikTok narratif LONG (1m30+) en suivant strictement les ordres du Commander.',
        backstory=(
            f'Tu transformes une stratégie en narration captivante et détaillée. Ton script doit être une machine à vues de 90s minimum. '
            f'Règle absolue : {cta_text}. Utilise un ton calme mais ironique. Développe chaque point technique.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('ScriptArchitect')
    )

    visual_promptist = Agent(
        role='VisualPromptist',
        goal='Créer exactement 18 prompts ultra-réalistes en anglais pour le générateur FLUX.',
        backstory=(
            'Tu es un directeur artistique de haut vol. Tu garantis une narration visuelle parfaite pour une vidéo longue. '
            'Tes prompts doivent être cinématiques et cohérents pour que les 18 images racontent une histoire complète de 90s.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('VisualPromptist')
    )

    quality_controller = Agent(
        role='QualityController',
        goal='Vérifier la signature finale et forcer les mots-clés d\'impact en MAJUSCULES.',
        backstory=(
            'Tu es le garant de la perfection. Tu valides la cohérence des 7 images, la force de la caption '
            'et tu t\'assures que les 3 mots-clés stratégiques sont bien présents en MAJUSCULES.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('QualityController')
    )

    if not commando_mode:
        return trend_radar, viral_judge, monetization_scorer, script_architect, visual_promptist, quality_controller

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

    return trend_radar, viral_judge, monetization_scorer, script_architect, visual_promptist, quality_controller, tiktok_distributor, growth_commander
