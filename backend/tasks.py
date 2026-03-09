from crewai import Task
from agents import ask_human_in_loop
import datetime

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
            f"Fais une recherche exhaustive sur le Web et via des flux RSS (Reddit /r/LocalLLMs, GitHub Trending) "
            f"pour identifier les 5 MEILLEURS sujets TikTok actuels correspondant au thème : {focus_topic}. "
            f"Aujourd'hui nous sommes le {now}. Essaie de trouver des actualités de ces dernières 24-48h. "
            f"Cherche impérativement les mots clés: Free, Open Source, Self-hosted, No-cost clone. "
            f"CONSIGNE DE RECHERCHE STRICTE: Outil web strict -> pas plus de 3 mots par recherche (ex: 'LLM open source', 'github trends'). "
            f"Fournis une liste de 5 sujets avec : Nom, URL, et 'Killer Feature'."
        ),
        expected_output="Une liste structurée de 5 sujets open source trouvés avec Nom, URL, et Killer Feature pour chacun.",
        agent=trend_radar
    )

    task_filter = Task(
        description=(
            "À partir de la liste des 5 sujets fournis par TrendRadar, sélectionne l'unique sujet le plus 'Killer' pour la vidéo. "
            "Vérifie qu'il est 100% gratuit en cherchant la page de prix (pricing) via l'URL. "
            "Si la gratuité est avérée, valide-le. "
            "SI LE PRIX EST FLOU OU SI TU AS LE MOINDRE DOUTE : formule que tu as besoin de l'aide de l'humain."
        ),
        expected_output="Rapport de viabilité et de gratuité du sujet. Indication claire si le modèle de prix est validé ou s'il bloque le process.",
        agent=viral_judge
    )

    tasks = [task_scout, task_filter]

    # Optional Commando Strategy Task
    if commando_mode:
        task_growth_strategy = Task(
            description=(
                "Analyse le sujet sélectionné et définis le 'HOOK' (l'accroche) le plus violent possible pour TikTok. "
                "Ta mission est de hacker l'attention en 1.5 seconde. "
                "Donne des instructions précises à ScriptArchitect pour que le script soit une machine à vues."
            ),
            expected_output="Une stratégie de hook (visuel + texte) agressive pour maximiser le watchtime.",
            agent=growth_commander
        )
        tasks.append(task_growth_strategy)

    task_scoring = Task(
        description=(
            "À partir des rapports précédents, attribue un score de R.O.I (Retour Sur Investissement) sur 100. "
            "Plus l'outil remplace un abonnement cher (ex: ChatGPT Plus, Midjourney, ElevenLabs), plus le score s'approche de 100."
        ),
        expected_output="Un score /100 justifié par un paragraphe expliquant l'économie réalisée par l'abonnement évité.",
        agent=monetization_scorer
    )
    tasks.append(task_scoring)

    # Dynamic CTA based on mode
    cta = "J'ai cassé Internet... encore. Alors abonne-toi et mets un cœur pour ne rien rater !" if commando_mode else "J'ai cassé Internet... encore."
    task_scripting = Task(
        description=(
            f"En utilisant le sujet, la 'Killer Feature' (et la stratégie de hook si disponible), écris un script TikTok narratif en français d'exactement 30 secondes. "
            "Adopte ton ton 'iM' unique : calme, posé, direct, et avec une touche d'ironie hautaine. "
            "Identifie 3 mots-clés dans le texte qui expriment le coeur de la valeur (ex: GRATUIT, LOCAL, INFINI) et mets-les TOUT EN MAJUSCULES. "
            f"La toute dernière ligne de ton script DOIT ÊTRE EXACTEMENT : '{cta}'"
        ),
        expected_output="Un script TikTok complet, avec les 3 mots clés EN MAJUSCULES, et la signature exacte à la fin.",
        agent=script_architect
    )
    tasks.append(task_scripting)

    task_visuals = Task(
        description=(
            "À partir du script validé par ScriptArchitect, rédige EXACTEMENT 7 prompts en ANGLAIS pour FLUX.1. "
            "Chaque prompt DOIT suivre ce format précis : "
            "'Raw cinematic shot, 35mm film grain, hyper-realistic, [CONTENU DE LA SCÈNE ICI], natural environmental lighting, soft bokeh background, highly detailed textures, shot on Arri Alexa, color graded, shallow depth of field, 8k resolution.' "
            "IMPORTANT : Les 7 images doivent raconter une HISTOIRE COHÉRENTE. Le sujet, les couleurs et l'ambiance doivent être constants du début à la fin. "
            f"Prends en compte que l'actualité est le {now}. "
            "Structure : 1(Hook), 2-4(Story/Explication), 5-6(Demo/Action), 7(Final/Logo)."
        ),
        expected_output="Une suite cohérente de 7 prompts cinématiques en anglais racontant une histoire visuelle complète.",
        agent=visual_promptist
    )
    tasks.append(task_visuals)

    # Optional Distribution Task
    if commando_mode:
        task_distribution = Task(
            description=(
                "Crée la 'Caption' TikTok parfaite (description + hashtags) pour ce script. "
                "Utilise un Hook textuel en première ligne, des émojis stratégiques, et mélange 5 hashtags de niche et 2 hashtags larges."
            ),
            expected_output="Une description TikTok optimisée SEO et viralité avec hashtags.",
            agent=tiktok_distributor
        )
        tasks.append(task_distribution)

    task_review = Task(
        description=(
            "Relis le script, les prompts de visuals (et la caption si disponible). Vérifie les éléments critiques: "
            f"1. Le script a-t-il exactement la phrase de fin requise ? ({cta}) "
            "2. Y a-t-il bien 3 mots en MAJUSCULES pour le montage vidéo ? "
            "3. Y a-t-il exactement 7 prompts visuels en anglais avec le style imposé ? \n\n"
            "RÉCUPÉRATION BLOG: Récupère également la liste des 5 sujets initiaux pour le blog.\n\n"
            "Si tout est validé, approuve le lancement en production finale."
        ),
        expected_output=(
            "Un bloc JSON contenant :\n"
            "- 'titre', 'script', 'score_roi', 'mots_cles' (string), 'image_prompts' (list), 'tiktok_caption' (string, if any), 'statut_validation' (bool)\n"
            "- 'top_5_concepts': une liste d'objetsissue du scouting initial pour le blog.\n"
            "Tu dois IMPÉRATIVEMENT renvoyer la réponse FORMATÉE EN JSON VALIDE DANS UN BLOC ```json ... ```."
        ),
        agent=quality_controller
    )
    tasks.append(task_review)

    return tasks

    return [task_scout, task_filter, task_scoring, task_scripting, task_visuals, task_review]
