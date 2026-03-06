from crewai import Task
from agents import ask_human_in_loop
import datetime

def create_tasks(trend_radar, viral_judge, monetization_scorer, script_architect, visual_promptist, quality_controller, run_type="matin"):
    now = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
    focus_topic = "News IA, Outils gratuits, Nouveautés LLMs" if run_type == "matin" else "Tutoriels techniques, Self-hosting, Contours d'abonnements"
    
    task_scout = Task(
        description=(
            f"Fais une recherche exhaustive sur le Web et via des flux RSS (Reddit /r/LocalLLMs, GitHub Trending) "
            f"pour identifier le meilleur sujet TikTok actuel correspondant au thème : {focus_topic}. "
            f"Aujourd'hui nous sommes le {now}. Essaie de trouver une actualité de ces dernières 24-48h. "
            f"Cherche impérativement les mots clés: Free, Open Source, Self-hosted, No-cost clone. "
            f"CONSIGNE DE RECHERCHE STRICTE: Outil web strict -> pas plus de 3 mots par recherche (ex: 'LLM open source', 'github trends'). "
            f"Fournis le Nom, l'URL, et la 'Killer Feature' du sujet."
        ),
        expected_output="Un résumé détaillé avec Nom, URL, et Killer Feature du meilleur sujet open source trouvé.",
        agent=trend_radar
    )

    task_filter = Task(
        description=(
            "À partir du sujet identifié par TrendRadar, vérifie qu'il est 100% gratuit. "
            "Recherche la page de prix (pricing) via l'URL avec l'outil de scraping ou Web Search. "
            "Si la gratuité est avérée, note-le. "
            "SI LE PRIX EST FLOU OU SI TU AS LE MOINDRE DOUTE : utilise tes capacités pour formuler que "
            "tu as besoin de l'aide de l'humain. (Note : Dans un vrai système complexe, tu appellerais une fonction Python, "
            "mais ici documente simplement le statut de prix comme 'Needs_Human_Verification' si douteux)."
        ),
        expected_output="Rapport de viabilité et de gratuité du sujet. Indication claire si le modèle de prix est validé ou s'il bloque le process.",
        agent=viral_judge
    )

    task_scoring = Task(
        description=(
            "À partir des rapports précédents, attribue un score de R.O.I (Retour Sur Investissement) sur 100. "
            "Plus l'outil remplace un abonnement cher (ex: ChatGPT Plus, Midjourney, ElevenLabs), plus le score s'approche de 100."
        ),
        expected_output="Un score /100 justifié par un paragraphe expliquant l'économie réalisée par l'abonnement évité.",
        agent=monetization_scorer
    )

    task_scripting = Task(
        description=(
            "En utilisant le sujet, la 'Killer Feature' et le contexte de rentabilité, écris un script TikTok narratif en français d'exactement 30 secondes (environ 60-75 mots). "
            "Adopte ton ton 'iM' unique : calme, posé, direct, et avec une touche d'ironie hautaine. "
            "Identifie 3 mots-clés dans le texte qui expriment le coeur de la valeur (ex: GRATUIT, LOCAL, INFINI) et mets-les TOUT EN MAJUSCULES. "
            "La toute dernière ligne de ton script DOIT ÊTRE EXACTEMENT : 'J'ai cassé Internet... encore.'"
        ),
        expected_output="Un script TikTok complet, avec les 3 mots clés EN MAJUSCULES, et la signature exacte à la fin.",
        agent=script_architect
    )

    task_visuals = Task(
        description=(
            "À partir du script validé par ScriptArchitect, rédige EXACTEMENT 7 prompts en ANGLAIS pour FLUX.1. "
            "Chaque prompt DOIT suivre ce format précis : "
            "'Raw cinematic shot, 35mm film grain, hyper-realistic, [CONTENU DE LA SCÈNE ICI], natural environmental lighting, soft bokeh background, highly detailed textures, shot on Arri Alexa, color graded, shallow depth of field, 8k resolution.' "
            "IMPORTANT : Les 7 images doivent raconter une HISTOIRE COHÉRENTE. Le sujet, les couleurs et l'ambiance doivent être constants du début à la fin (Visual consistency). "
            f"Prends en compte que l'actualité est le {now}. "
            "Structure : 1(Hook), 2-4(Story/Explication), 5-6(Demo/Action), 7(Final/Logo)."
        ),
        expected_output="Une suite cohérente de 7 prompts cinématiques en anglais racontant une histoire visuelle complète.",
        agent=visual_promptist
    )

    task_review = Task(
        description=(
            "Relis le script fourni par ScriptArchitect ET les prompts de VisualPromptist. Vérifie 4 éléments critiques: "
            "1. Le script a-t-il exactement la phrase de fin requise ? "
            "2. Y a-t-il bien 3 mots en MAJUSCULES pour le montage vidéo ? "
            "3. L'explication de rentabilité de MonetizationScorer est-elle bien implicitement présente ? "
            "4. Y a-t-il exactement 7 prompts visuels en anglais avec le style imposé ? "
            "Si tout est validé, approuve le lancement en production finale."
        ),
        expected_output="Un bloc JSON contenant les clés 'titre', 'script', 'score_roi', 'mots_cles' (chaîne de caractères contenant la liste), 'image_prompts' (une simple liste json de strings), et 'statut_validation' (booléen). Tu dois IMPÉRATIVEMENT renvoyer la réponse FORMATÉE EN JSON VALIDE DANS UN BLOC ```json ... ```.",
        agent=quality_controller
    )

    return [task_scout, task_filter, task_scoring, task_scripting, task_visuals, task_review]
