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
            f"Ta mission 'TrendHunter' est d'identifier les 5 news les plus impactantes en IA/Open-Source/Dev des 7 DERNIERS JOURS via Perplexity, GitHub Trending et X. "
            f"Aujourd'hui nous sommes le {now}. Focus : {focus_topic}. {recent_context}\n"
            "RÈGLE DE SORTIE (Fiche Technique) :\n"
            "1. Innovation : Gap technique précis (ex: Context window, tokens/sec, architecture MoE).\n"
            "2. La Preuve : Lien GitHub, benchmark (MMLU, HumanEval) ou citation source.\n"
            "3. L'Angle 'Drama' : Qui est menacé ? (ex: 'Ça tue l'abonnement ChatGPT Plus')."
        ),
        expected_output="Top 5 Fiches Techniques d'Actualité (Innovation, Preuve, Drama).",
        agent=trend_radar
    )

    task_pick_best = Task(
        description=(
            "Analyse le Top 5 des news fourni par Luca. Ta mission est de CHOISIR LA MÉILLEURE NEWS (Top 1) "
            "pour une vidéo TikTok de 90s. Analyse le potentiel de rétention, l'intérêt technique et l'angle 'Drama'.\n\n"
            "RÈGLE : Tu ne dois retourner QU'UNE SEULE NEWS, la plus prometteuse."
        ),
        expected_output="La news sélectionnée (Top 1) avec une brève justification de son potentiel viral.",
        agent=viral_judge,
        context=[task_scout]
    )

    task_filter = Task(
        description=(
            "Filtre impitoyable : Vérifie la gratuité absolue et la présence de preuves techniques (Innovation/Preuve/Drama) pour la news suivante : {news_validee}\n\n"
            "RÈGLE : Rejet immédiat (Kill Switch) de tout sujet 'mou' ou payant. Seule la tech disruptive et gratuite passe. "
            "Ce module remplace la 'créativité' par de l'extraction de données pure."
        ),
        expected_output="Rapport de viabilité final. Sujet validé (Data & Zero-Cost OK) ou rejeté par le Kill Switch.",
        agent=viral_judge
    )

    tasks = [task_scout, task_pick_best, task_filter]

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
    cta = "Abonnez-vous et like ! J'ai cassé internet Encore. 🚀"
    task_scripting = Task(
        description=(
            "ORDRE COMMANDO : Transforme la news suivante validée par l'humain en un script TikTok agressif de 90s : {news_validee}\n"
            "CONTRAINTE : Ne traite QUE cette news. Zéro invention. Si la news est 'Kling AI', ne parle pas de 'Sora'.\n"
            "RÈGLE DE TEMPORALITÉ : Interdiction de parler de tech pré-2025. Nous sommes en 2026.\n"
            "STYLE : Cynique, expert, zéro ton scolaire. Pas de 'Simple, non ?'.\n"
            "STRUCTURE : Template 'Le Benchmark Killer' (Hook violent -> Confrontation data -> Chute technique).\n"
            "SOURCE : Ton script doit se baser EXCLUSIVEMENT sur cette news."
        ),
        expected_output="Script TikTok 90s (Style Cash Machine, Zéro Fiction).",
        agent=script_architect,
    )
    tasks.append(task_scripting)

    task_visuals = Task(
        description=(
            "Crée exactement 18 requêtes JSON via la formule Veo 3.1. Chaque requête doit contenir :\n"
            "1. flux_prompt: Prompt descriptif pour l'image statique (FLUX).\n"
            "2. motion_prompt: Prompt d'animation pour la vidéo (Veo/Wan/Kling).\n"
            "INTERDICTION ABSOLUE : Robots, cyborgs, cerveaux filaires, visages humains génériques.\n"
            "REQUIS : Uniquement de la Data, UI, terminaux, code Python, schémas techniques, benchmarks.\n"
            "Ambiance : Tech-Noir / Cyberpunk contrasté."
        ),
        expected_output="18 pairs of (flux_prompt + motion_prompt) strictly following the UI/Data standard.",
        agent=visual_promptist,
        context=[task_scripting],
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
            "Filtre de rejet ultime (Kill Switch) :\n"
            "1. News Obsolète ? (Rejet si pré-2025).\n"
            "2. Incohérence Technique ? (Mélange cloud/local insensé).\n"
            "3. Ton Scolaire ? (Rejet si ton trop descriptif ou faible).\n"
            "Si rejeté, renvoie : 'ORDRE COMMANDO : Script REJETÉ. Corrige l''anachronisme et adopte un ton plus agressif.'"
        ),
        expected_output="Package final validé (Anti-Obsolescence, Rigueur Tech).",
        agent=quality_controller,
        output_pydantic=AgentOutcome
    )
    tasks.append(task_review)

    return tasks
