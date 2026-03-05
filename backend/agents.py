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

def create_agents(config=None):
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

    script_architect = Agent(
        role='ScriptArchitect',
        goal='Rédiger un script TikTok ironique et percutant de 30 secondes.',
        backstory=(
            'Tu es le scénariste vedette de iM System. Ton script DOIT OBLIGATOIREMENT se terminer par : "J\'ai cassé Internet... encore." '
            'Mets 3 mots-clés stratégiques en MAJUSCULES.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('ScriptArchitect')
    )

    quality_controller = Agent(
        role='QualityController',
        goal='Vérifier la cohérence globale du script et des prompts visuels.',
        backstory='Tu es le garant final. Tu vérifies le respect des contraintes et tu valides.',
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('QualityController')
    )

    visual_promptist = Agent(
        role='VisualPromptist',
        goal='Créer exactement 7 prompts d\'images pour FLUX.',
        backstory=(
            'Tu es directeur artistique. Style : "Ultra-HD, Cinematic, iM-System Style". '
            'Génère 7 prompts en ANGLAIS.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_agent_llm('VisualPromptist')
    )

    return trend_radar, viral_judge, monetization_scorer, script_architect, visual_promptist, quality_controller
