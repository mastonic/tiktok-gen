from crewai import Agent, LLM
from langchain_google_genai import ChatGoogleGenerativeAI
from custom_tools import feed_parser_tool, duckduckgo_search_tool, trafilatura_scraper, pytrends_tool
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
    
    return LLM(model=model_name, api_key=api_key)

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

def create_agents(config=None, commando_mode=False):
    # config is a dict: { 'TrendRadar': 'openai/gpt-4o', ... }
    def get_agent_llm(role):
        m = config.get(role, "openai/gpt-4o-mini") if config else "openai/gpt-4o-mini"
        return get_llm(m)

    trend_radar = Agent(
        role='TrendRadar',
        goal='Scanner les flux RSS et GitHub pour trouver des sujets TikTok sur le self-hosting et l\'IA.',
        backstory=(
            'Tu es un expert en sourcing Open Source. Tu cherches des "Killer Features" gratuites. '
            'RÈGLE : Requêtes de 2-3 mots max.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('TrendRadar'),
        tools=[feed_parser_tool, duckduckgo_search_tool]
    )

    viral_judge = Agent(
        role='ViralJudge',
        goal='Valider la gratuité du sujet et évaluer le potentiel viral.',
        backstory=(
            'Tu es un analyste de tendances. Tu dois absolument t\'assurer que le sujet est gratuit. '
            'SI LE PRIX EST FLOU, écris simplement "Needs_Human_Verification".'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('ViralJudge'),
        tools=[pytrends_tool, trafilatura_scraper, duckduckgo_search_tool]
    )

    monetization_scorer = Agent(
        role='MonetizationScorer',
        goal='Attribuer un score de rentabilité ROI (/100) pour chaque concept.',
        backstory='Tu es un consultant en rentabilité. Calcule le score toi-même sans déléguer.',
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('MonetizationScorer')
    )

    # Note: If commando_mode is ON, ScriptArchitect uses a harder CTA
    cta_text = '"J\'ai cassé Internet... encore. Alors abonne-toi et mets un cœur pour ne rien rater !"' if commando_mode else '"J\'ai cassé Internet... encore."'

    script_architect = Agent(
        role='ScriptArchitect',
        goal='Rédiger un script TikTok ironique et percutant de 30 secondes.',
        backstory=(
            f'Tu es le scénariste vedette de iM System. Ton script DOIT OBLIGATOIREMENT se terminer par : {cta_text} '
            'Mets 3 mots-clés stratégiques en MAJUSCULES.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('ScriptArchitect')
    )

    visual_promptist = Agent(
        role='VisualPromptist',
        goal='Créer exactement 7 prompts d\'images cohérents pour FLUX qui racontent une histoire visuelle.',
        backstory=(
            'Tu es un directeur artistique de haut vol. Ta mission est de traduire le script en une suite logique de 7 images ultra-réalistes. '
            'Chaque prompt doit suivre scrupuleusement ce template : '
            '"Raw cinematic shot, 35mm film grain, hyper-realistic, [TON THÈME ICI, décrit de manière sobre], natural environmental lighting, soft bokeh background, highly detailed textures (skin pores, fabric weave), shot on Arri Alexa, color graded, shallow depth of field, 8k resolution, photorealistic masterpiece, authentic look." '
            'RÈGLE D\'OR : Les 7 images doivent être visuellement cohérentes entre elles pour former une narration fluide (Storytelling visuel).'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('VisualPromptist')
    )

    quality_controller = Agent(
        role='QualityController',
        goal='Vérifier la cohérence globale du script et des prompts visuels.',
        backstory='Tu es le garant final. Tu vérifies le respect des contraintes et tu valides.',
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('QualityController')
    )

    if not commando_mode:
        return trend_radar, viral_judge, monetization_scorer, script_architect, visual_promptist, quality_controller

    tiktok_distributor = Agent(
        role='TikTokDistributor',
        goal='Générer une description TikTok virale et des hashtags stratégiques.',
        backstory=(
            'Tu es un expert en algorithme TikTok. Ta mission est de créer une "Caption" qui maximise le taux de complétion '
            'et le partage. Utilise des émojis, un Hook textuel dès la première ligne, et une liste de 5-7 hashtags '
            '(mélange de niches et de larges).'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('TikTokDistributor')
    )

    growth_commander = Agent(
        role='ViralGrowthCommander',
        goal='Piloter l\'Opération Commando 10k : Maximiser les abonnés en 30 jours.',
        backstory=(
            'Tu es l\'architecte de la croissance agressive. Ton unique obsession est le "Watch Time" et le "Follow Rate". '
            'Tu imposes des Hooks ultra-violents (visuels et textuels) et tu t\'assures que chaque vidéo résout un problème '
            'frustrant pour l\'utilisateur de manière gratuite. Tu ne fais pas de compromis sur la viralité.'
        ),
        verbose=True,
        allow_delegation=True, # Can delegate to refine hooks or scripts
        llm=get_agent_llm('ViralGrowthCommander')
    )

    return trend_radar, viral_judge, monetization_scorer, script_architect, visual_promptist, quality_controller, tiktok_distributor, growth_commander
