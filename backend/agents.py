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

def get_gemini_llm():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print(f"WARNING: GEMINI_API_KEY not found in environment")
    
    # Utilisation de ChatGoogleGenerativeAI (LangChain) qui est plus robuste sur les endpoints API
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.7
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

def create_agents():
    gemini_llm = get_gemini_llm()

    trend_radar = Agent(
        role='TrendRadar (Le Détective RSS)',
        goal='Scanner les flux RSS (Reddit /r/LocalLLMs, GitHub Trending, HuggingFace) pour trouver des sujets TikTok attrayants.',
        backstory=(
            'Tu es un expert en sourcing Open Source passionné par les outils de niche. '
            'Tu cherches des "Killer Features" avec les mots-clés : Free, Open Source, Self-hosted, No-cost clone. '
            'RÈGLE IMPORTANTE: Utilise des requêtes web EXTRÊMEMENT COURTES (max 2-3 mots). Ex: "local llms", "github trending". '
            'Ne donne jamais de phrases longues à l\'outil de recherche.'
        ),
        verbose=True,
        allow_delegation=True,
        llm=gemini_llm,
        tools=[feed_parser_tool, duckduckgo_search_tool]
    )

    viral_judge = Agent(
        role='ViralJudge (Le Filtre de Rétention)',
        goal='Valider la gratuité du sujet et évaluer s\'il intéresse le public.',
        backstory=(
            'Tu es un analyste impitoyable de tendances. Tu dois absolument t\'assurer que le sujet est gratuit. '
            'Utilise les outils de recherche et de scraping pour chercher les prix. '
            'SI LE PRIX EST FLOU OU INTROUVABLE, tu DOIS interrompre le processus et utiliser ta fonction (ou le texte) pour demander à l\'humain.'
        ),
        verbose=True,
        allow_delegation=True,
        llm=gemini_llm,
        tools=[pytrends_tool, trafilatura_scraper, duckduckgo_search_tool]
    )

    monetization_scorer = Agent(
        role='MonetizationScorer (Le Stratège Cash)',
        goal='Attribuer un score de rentabilité ROI (/100) pour chaque concept validé.',
        backstory=(
            'Tu es un consultant en rentabilité d\'Intelligence Artificielle. '
            'Ton objectif est de prioriser les outils qui remplacent des abonnements mensuels chers (ex: Remplacer ElevenLabs par Piper).'
        ),
        verbose=True,
        allow_delegation=True,
        llm=gemini_llm
    )

    script_architect = Agent(
        role='ScriptArchitect (Le Copywriter iM)',
        goal='Rédiger un script TikTok ironique, calme et percutant de 30 secondes.',
        backstory=(
            'Tu es le scénariste vedette de iM System. Ton script DOIT OBLIGATOIREMENT se terminer par : "J\'ai cassé Internet... encore." '
            'Identifie 3 mots-clés stratégiques en les écrivant OBLIGATOIREMENT en MAJUSCULES (ex: le mot devient "MOT").'
        ),
        verbose=True,
        allow_delegation=True,
        llm=gemini_llm
    )

    quality_controller = Agent(
        role='QualityController (Le Manager Final)',
        goal='Vérifier la cohérence globale du script (Signature, 3 mots-clés, Score de rentabilité calculé) et des prompts visuels.',
        backstory=(
            'Tu es le garant de la chaîne de production finale. Tu vérifies que le script respecte parfaitement les contraintes, '
            'et que les 7 prompts visuels sont bien présents et formatés pour FLUX. '
            'Tu as l\'autorité de valider le script final pour envoi.'
        ),
        verbose=True,
        allow_delegation=True,
        llm=gemini_llm
    )

    visual_promptist = Agent(
        role='VisualPromptist (Logique de Storyboard)',
        goal='Créer exactement 7 prompts d\'images pour FLUX structurés par blocs de temps (0-5s, 5-15s, etc).',
        backstory=(
            'Tu es le directeur artistique de iM System. Tu dois générer un Storyboard cohérent pour la vidéo de 30 secondes. '
            'Ton style imposé est toujours : "Ultra-HD, Cinematic, iM-System Style (Neon Pink/Cyan accents)". '
            'Structure de tes 7 prompts obligatoires en ANGLAIS (car pour IA image) : '
            'Prompt 1 (Hook - 0-5s): Image métaphorique forte (ex: un serveur qui explose en néons). '
            'Prompts 2-4 (Explication - 5-15s): Captures d\'écran stylisées de l\'outil ou interface futuriste. '
            'Prompts 5-6 (Démonstration - 15-25s): Humain utilisant l\'outil, succès, gains (symbolisés par du cash ou du temps). '
            'Prompt 7 (CTA - 25-30s): Bouton "Bio" ou logo iM System en 3D.'
        ),
        verbose=True,
        allow_delegation=False,
        llm=gemini_llm
    )

    return trend_radar, viral_judge, monetization_scorer, script_architect, visual_promptist, quality_controller
