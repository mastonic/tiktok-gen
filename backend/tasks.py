from crewai import Task
from agents import ask_human_in_loop
import datetime
from models import AgentOutcome, VisualPrompts, TikTokMetadata

def create_tasks(*args, run_type="matin", commando_mode=False):
    now = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
    focus_topic = "News IA, Outils gratuits, Nouveautés LLMs" if run_type == "matin" else "Tutoriels techniques, Self-hosting, Contours d'abonnements"
    
    # Unpack agents
    if commando_mode:
        trend_radar, viral_judge, monetization_scorer, script_architect, visual_promptist, quality_controller, tiktok_distributor, growth_commander = args
    else:
        trend_radar, viral_judge, monetization_scorer, script_architect, visual_promptist, quality_controller = args

    task_scout = Task(
        description=(
            f"Fais une recherche exhaustive pour identifier les outils et news 'Killer' correspondant au thème : {focus_topic}. "
            f"Aujourd'hui nous sommes le {now}. Essaie de trouver des actualités de ces dernières 24-48h. "
            "Objectif : la pépite gratuite (recherche GitHub, Reddit, flux RSS)."
        ),
        expected_output="Une liste structurée de 5 sujets avec Nom, URL, et Killer Feature.",
        agent=trend_radar
    )

    task_filter = Task(
        description=(
            "Vérifie la gratuité absolue des sujets et simule l'intérêt du public. "
            "RÈGLE : Rejeter immédiatement (kill switch) tout sujet 'mou' ou payant. "
            "Si un doute subsiste, demande l'aide de l'humain."
        ),
        expected_output="Rapport de viabilité. Sujet validé ou rejeté.",
        agent=viral_judge
    )

    tasks = [task_scout, task_filter]

    # Optional Commando Strategy Task
    if commando_mode:
        task_growth_strategy = Task(
            description=(
                "Dicte le 'Hook' (l'accroche des 2 premières secondes) le plus violent possible pour ce sujet. "
                "C'est la base de la viralité Commando 10k."
            ),
            expected_output="Une consigne de Hook agressive (texte et visuel).",
            agent=growth_commander
        )
        tasks.append(task_growth_strategy)

    task_scoring = Task(
        description=(
            "Calcule l'économie réelle réalisée par le spectateur en utilisant cet outil gratuit au lieu d'un abonnement payant standard."
        ),
        expected_output="Score de ROI sur 100 et explication de l'économie mensuelle.",
        agent=monetization_scorer
    )
    tasks.append(task_scoring)

    # Dynamic CTA based on mode
    cta = "Abonne-toi et mets un cœur pour ne rien rater !" if commando_mode else "J'ai cassé Internet... encore."
    task_scripting = Task(
        description=(
            "Rédige un script TikTok narratif d'exactement 30s en suivant strictement le Hook du Commander (si présent). "
            f"Signature obligatoire : {cta}. Utilise 3 mots-clés stratégiques en MAJUSCULES."
        ),
        expected_output="Un script TikTok complet avec signature et mots-clés en MAJUSCULES.",
        agent=script_architect
    )
    tasks.append(task_scripting)

    task_visuals = Task(
        description=(
            "Crée exactement 7 prompts cinématiques en anglais pour FLUX. Raconte une histoire visuelle cohérente."
        ),
        expected_output="Exactly 7 cinematically consistent image prompts.",
        agent=visual_promptist,
        output_pydantic=VisualPrompts
    )
    tasks.append(task_visuals)

    # Optional Distribution Task
    if commando_mode:
        task_distribution = Task(
            description=(
                "Génère la description TikTok parfaite avec hashtags stratégiques pour forcer l'algorithme."
            ),
            expected_output="Viral caption and hashtags.",
            agent=tiktok_distributor,
            output_pydantic=TikTokMetadata
        )
        tasks.append(task_distribution)

    task_review = Task(
        description=(
            "Revue finale : vérifie la signature, les MAJUSCULES, la cohérence des visuels et la force de la caption TikTok. "
            "Assemble toutes les données pour la production finale."
        ),
        expected_output="Full agent outcome in JSON format.",
        agent=quality_controller,
        output_pydantic=AgentOutcome
    )
    tasks.append(task_review)

    return tasks
