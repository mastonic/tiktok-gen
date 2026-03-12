from crewai import Task
from agents import ask_human_in_loop
import datetime
from models import AgentOutcome, VisualPrompts, TikTokMetadata

from database import SessionLocal, ScriptInbox

def create_tasks(*args, run_type="matin", commando_mode=False):
    now = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
    if run_type == "matin":
        focus_topic = "News IA, Outils gratuits, Nouveautés LLMs"
    else:
        focus_topic = "Tutoriels techniques IA, Automatisation, Nouveaux agents IA Open-Source"
    
    # 💥 Machine à Cash : Prevent Topic Loops 💥
    recent_titles = []
    try:
        db = SessionLocal()
        recent_scripts = db.query(ScriptInbox).order_by(ScriptInbox.id.desc()).limit(15).all()
        recent_titles = [s.title for s in recent_scripts if s.title]
        db.close()
    except Exception as e:
        pass
        
    recent_context = ""
    if recent_titles:
        recent_context = f"\n\n🚨 STRATÉGIE MACHINE À CASH - RÈGLE D'OR 🚨\nTU DOIS ABSOLUMENT IGNORER LES SUJETS SUIVANTS DÉJÀ TRAITÉS : {', '.join(recent_titles)}.\nTROUVE DE TOUTES NOUVELLES OPPORTUNITÉS, NE RÉPÈTE JAMAIS CEUX-LÀ !"
        
    # Unpack agents
    if commando_mode:
        trend_radar, viral_judge, tech_utility_expert, script_architect, visual_promptist, quality_controller, tiktok_distributor, growth_commander = args
    else:
        trend_radar, viral_judge, tech_utility_expert, script_architect, visual_promptist, quality_controller = args

    task_scout = Task(
        description=(
            f"Ta mission 'TrendHunter' est d'identifier les 5 sujets IA/Tech les plus chauds des dernières 24h via TikTok Creative Center, Google Trends et Perplexity. "
            f"Aujourd'hui nous sommes le {now}. Focus : {focus_topic}. {recent_context}\n"
            "Identifie les recherches en hausse de >100% et croise-les avec AnswerThePublic pour trouver le Hook parfait."
        ),
        expected_output="Top 5 sujets explosifs avec Nom, URL, Killer Feature et Hook stratégique.",
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
            "Analyse en profondeur la technologie : architecture, avantages tech, points négatifs et axes d'amélioration. "
            "Rassemble des éléments pour une histoire ou une expérience utilisateur marquante avec cet outil. "
            "INTERDICTION de parler d'argent ou d'abonnement."
        ),
        expected_output="Analyse technique complète (Avantages, Inconvénients, Storytelling technique).",
        agent=tech_utility_expert
    )
    tasks.append(task_scoring)

    # Exact CTA restricted by user
    cta = "Abonnez-vous et like ! J'ai cassé internet Encore."
    task_scripting = Task(
        description=(
            "Rédige un script TikTok narratif d'EXACTEMENT 90 à 100 secondes. "
            "Structure obligatoire : 1. Hook. 2. Storytelling technique/histoire vécue. 3. Avantages, Inconvénients et détails techniques réels. "
            f"Signature FINALE IMPÉRATIVE : {cta}. "
            "INTERDICTION FORMELLE de parler d'argent."
        ),
        expected_output="Un script TikTok technique et narratif long avec le CTA demandé.",
        agent=script_architect
    )
    tasks.append(task_scripting)

    task_visuals = Task(
        description=(
            "Crée exactement 18 prompts cinématiques en anglais pour FLUX. "
            "Raconte une histoire visuelle cohérente pour un format LONG de 90 secondes (1 clip de 5s par prompt)."
        ),
        expected_output="Exactly 18 cinematically consistent image prompts.",
        agent=visual_promptist,
        context=[task_scripting], # Connect to script
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
