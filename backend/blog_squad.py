"""
blog_squad.py — BlogSquad CrewAI
Génère 5 articles de blog SEO-optimisés + JSON Bento Box d'affiliation
à partir du Top 5 des concepts vidéo produits par la VideoSquad.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from crewai import Agent, Task, Crew, Process, LLM
from pydantic import BaseModel, Field

# Setup logs
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# STRUCTURED OUTPUT — AffiliateStrategist
# ─────────────────────────────────────────────

class AffiliateTool(BaseModel):
    """Un outil d'affiliation recommandé pour la Bento Box."""
    name: str = Field(..., description="Nom commercial de l'outil (ex: ElevenLabs)")
    category: str = Field(..., description="Catégorie (ex: Voice IA, Video Gen, Cloud)")
    description: str = Field(..., description="Phrase d'accroche de 1 ligne max")
    cta: str = Field(..., description="Texte du bouton (ex: Tester Gratuitement)")
    affiliate_link_placeholder: str = Field(..., description="Slug du lien (ex: elevenlabs_affiliate)")
    gradient: str = Field(default="from-cyan-400 to-emerald-400")
    relevance_score: int = Field(..., ge=1, le=10, description="Score de pertinence 1-10")

class BentoBoxData(BaseModel):
    """JSON complet pour le composant React BentoBox."""
    article_title: str
    article_slug: str
    tools: List[AffiliateTool]
    seo_tags: List[str] = Field(..., description="3-5 tags SEO extraits du contenu")

# ─────────────────────────────────────────────
# LLM Helper
# ─────────────────────────────────────────────

def _get_llm(model: str = "openai/gpt-4o-mini") -> LLM:
    api_key = os.environ.get("OPENAI_API_KEY")
    return LLM(model=model, api_key=api_key)


def _slugify(text: str) -> str:
    """Transforme un titre en slug de fichier propre."""
    slug = text.lower().strip()
    slug = re.sub(r"[àáâãäå]", "a", slug)
    slug = re.sub(r"[èéêë]", "e", slug)
    slug = re.sub(r"[ìíîï]", "i", slug)
    slug = re.sub(r"[òóôõö]", "o", slug)
    slug = re.sub(r"[ùúûü]", "u", slug)
    slug = re.sub(r"[ç]", "c", slug)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:60]


# ─────────────────────────────────────────────
# BLOG SQUAD CLASS
# ─────────────────────────────────────────────

class BlogSquad:
    """
    Squad CrewAI dédiée à la production de contenu blog + affiliation.
    Prend en entrée une liste de concepts vidéo (Top 5) et génère :
    - 1 article Markdown de 600 mots par concept
    - 1 JSON BentoBox d'affiliation structuré par article
    - 1 fichier .md sauvegardé dans /blog/posts/
    """

    BLOG_POSTS_DIR = Path(__file__).parent / "blog" / "posts"

    def __init__(self, model: str = "openai/gpt-4o-mini"):
        self.llm = _get_llm(model)
        self.BLOG_POSTS_DIR.mkdir(parents=True, exist_ok=True)
        self._build_agents()

    def _build_agents(self):
        """Instancie les 2 agents réutilisables."""

        self.content_transmuter = Agent(
            role="ContentTransmuter",
            goal=(
                "Tu es l'expert rédactionnel de l'iM-System. Ta mission est de rédiger un article de blog 'Dark Tech' "
                "ultra-captivant au format Markdown pur."
            ),
            backstory=(
                "Tu es le ContentTransmuter, l'expert rédactionnel d'élite de l'iM-System. Ton style est expert, futuriste, "
                "et percutant. Tu refuses la médiocrité et les structures répétitives.\n\n"
                "RÈGLE DE SURVIE : Tu as l'interdiction formelle d'utiliser des titres génériques.\n"
                "TON ET STYLE : Expert, futuriste. Tu écris des paragraphes ultra-courts (3 lignes max) pour une lecture mobile laser.\n"
                "STRUCTURE : Manifesto, Guide étape par étape, ou Étude de cas technique. Change de structure à chaque article."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.affiliate_strategist = Agent(
            role="AffiliateStrategist",
            goal=(
                "Analyser un article de blog sur un outil tech et sélectionner les 2-3 meilleurs "
                "outils d'affiliation à insérer dans la Bento Box de la page. "
                "Produire un JSON strict conforme au schéma Pydantic BentoBoxData."
            ),
            backstory=(
                "Tu es un expert en monétisation de contenu digital. Tu connais parfaitement les programmes "
                "d'affiliation des outils IA : ElevenLabs, Luma AI, Flux.1 (Fal.ai), Hetzner, RunPod, Replicate. "
                "Tu choisis les outils pertinents en fonction du contenu de l'article, jamais au hasard. "
                "RÈGLE : Tu renvoies UNIQUEMENT le JSON valide, rien d'autre."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def _build_tasks(self, concept: Dict[str, Any], is_winner: bool = False) -> tuple[Task, Task]:
        """Crée les 2 tâches pour un concept donné."""
        concept_title = concept.get("titre", concept.get("title", str(concept)))
        concept_summary = concept.get("killerfeature", concept.get("summary", concept_title))
        category = concept.get("category", "IA Générative")
        slug = _slugify(concept_title)

        video_tag = "[INSERT_VIDEO_PLAYER]" if is_winner else ""
        see_also = "" if is_winner else "\n\n## 🎥 Voir aussi\nDécouvrez notre dernière vidéo virale du jour sur le dashboard !"

        # Template more flexible to allow unique headers while preserving frontmatter
        TEMPLATE_STRUCTURE = f"""---
title: "[CHOISIS UN TITRE ULTRA-PERCUTANT ICI]"
excerpt: "[Résumé court et percutant de l'article pour la carte du blog (max 160 caractères, optimisé SEO)]"
cover_image: "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&q=80&w=1200"
category: "{category}"
---

# [MÊME TITRE QUE CI-DESSUS]

> **Note de l'Expert :** [Rédige ici un conseil d'expert percutant de 1-2 phrases spécifiquement sur cet outil.]

{video_tag}

[CONSTRUIS ICI TON ARTICLE : MANIFESTE, GUIDE OU ÉTUDE DE CAS]
[UTILISE DES H2 ET H3 UNIQUES ET DES PARAGRAPHES COURTS]
[INCLUE IMPÉRATIVEMENT UN TABLEAU DE COMPARAISON OU UNE LISTE TECHNIQUE]

[INSERT_BENTO_BOX_1]

[FIN DE L'ARTICLE AVEC CONCLUSION ET CTA]{see_also}"""

        task_write = Task(
            description=(
                f"Rédige un article de blog complet sur ce concept : '{concept_title}'.\n"
                f"Killer Feature / Angle : {concept_summary}\n\n"
                "⚠️ RÈGLE DE SURVIE : INTERDICTION DU PLAN PAR DÉFAUT ⚠️\n"
                "Il est formellement interdit d'utiliser ces titres (H2, H3) :\n"
                "❌ 'L'idée derrière le buzz', 'Comment nous avons automatisé la production', "
                "'Les alternatives et pourquoi celle-ci gagne', 'Conclusion', 'Introduction'.\n\n"
                "DIRECTIVES DE RÉDACTION :\n"
                "- Titres (H2, H3) : Ils DOIVENT inclure des éléments spécifiques au sujet et ressembler à des titres de magazines Tech.\n"
                "- Header : Commence par le titre H1, suivi du bloc Note de l'Expert.\n"
                "- Affiliation : Insère le tag [INSERT_BENTO_BOX_1] naturellement après le premier paragraphe ou premier H2.\n"
                "- Paragraphes : Ultra-courts (3 lignes max).\n"
                "- Ton : Expert, futuriste, Dark Tech.\n\n"
                f"STRUCTURE À RESPECTER :\n\n{TEMPLATE_STRUCTURE}\n\n"
                "FORMAT DE SORTIE : Markdown pur uniquement, sans texte superflu autour."
            ),
            expected_output="L'article Markdown complet avec des titres contextuels et la structure Dark Tech.",
            agent=self.content_transmuter
        )

        task_monetize = Task(
            description=(
                "Analyse attentivement l'article rédigé par le ContentTransmuter (fourni en contexte). "
                "Identifie les 2 outils d'affiliation les plus pertinents parmi : "
                "ElevenLabs (voice), Luma AI (video gen), Fal.ai/Flux.1 (image gen), Hetzner (cloud VPS), "
                "RunPod (GPU cloud), Replicate (API ML), DigitalOcean (hosting).\n\n"
                f"Titre de l'article : {concept_title}\n"
                f"Slug : {slug}\n\n"
                "Produis le JSON BentoBoxData STRICT avec ces champs :\n"
                "- article_title : titre complet\n"
                "- article_slug : le slug fourni ci-dessus\n"
                "- seo_tags : 3-5 tags SEO issus du contenu (liste de strings)\n"
                "- tools : liste de 2 objets avec id (\"tool_1\", \"tool_2\"), name, category, description (1 ligne), cta, affiliate_link_placeholder, gradient, relevance_score\n\n"
                "IMPORTANT : Renvoie UNIQUEMENT un bloc ```json ... ``` valide. "
                "Les 'id' des tools DOIVENT être exactement 'tool_1' et 'tool_2' pour correspondre aux balises AffiliateBento."
            ),
            expected_output=(
                "Un bloc ```json valide avec 'article_title', 'article_slug', 'seo_tags', et 'tools' (2 items avec id='tool_1' et id='tool_2'). "
                "Gradients valides : 'from-cyan-400 to-emerald-400', 'from-violet-500 to-fuchsia-500', 'from-amber-400 to-orange-500'."
            ),
            agent=self.affiliate_strategist,
            context=[task_write]
        )

        return task_write, task_monetize

    def save_to_markdown(self, article_markdown: str, bento_data: dict, concept_title: str) -> Path:
        """
        Sauvegarde l'article + le JSON Bento Box dans /blog/posts/<slug>.md
        Le frontmatter vient de l'article généré par l'agent (il l'a déjà inclus).
        On injecte juste le JSON bento_data en appendice pour le rendu React.
        """
        slug = bento_data.get("article_slug") or _slugify(concept_title)
        file_path = self.BLOG_POSTS_DIR / f"{slug}.md"

        # Nettoyage de l'output de l'agent (enlever les blocs ```markdown ... ```)
        cleaned = article_markdown.strip()
        # Supprime ```markdown au début et ``` à la fin
        cleaned = re.sub(r'^```(?:markdown)?\n', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'\n```$', '', cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        # Si l'agent a déjà produit le frontmatter (commence par ---), on respecte son output.
        # Sinon on en génère un minimal.
        if cleaned.startswith("---"):
            article_body = cleaned
        else:
            # Frontmatter de secours
            seo_tags = bento_data.get("seo_tags", [])
            tags_yaml = "\n".join([f'  - "{t}"' for t in seo_tags])
            import datetime
            fallback_fm = f"""---
title: "{bento_data.get('article_title', concept_title)}"
excerpt: "{concept_title} — découvrez cet outil open source incontournable."
cover_image: "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&q=80&w=1200"
category: "IA Générative"
slug: "{slug}"
date: "{datetime.datetime.now().strftime('%Y-%m-%d')}"
tags:
{tags_yaml}
---
"""
            article_body = fallback_fm + article_markdown.strip()

        # Appendice JSON — lu par le server-side renderer React pour les BentoBox
        bento_appendix = f"""

<!-- AFFILIATE_BENTO_DATA
```json
{json.dumps(bento_data, ensure_ascii=False, indent=2)}
```
-->
"""
        full_content = article_body + bento_appendix

        file_path.write_text(full_content, encoding="utf-8")
        logger.info(f"✅ Blog post saved: {file_path}")
        return file_path

    def run(self, top5_concepts: List[Dict[str, Any]]) -> List[Dict]:
        """
        Lance la BlogSquad sur chaque concept du Top 5.
        Retourne la liste des résultats [{slug, file_path, bento_data}, ...]
        """
        results = []

        for i, concept in enumerate(top5_concepts):
            concept_title = concept.get("titre", concept.get("title", f"Concept {i+1}"))
            logger.info(f"📝 [BlogSquad] Processing concept {i+1}/{ len(top5_concepts)}: {concept_title}")

            try:
                # The first concept in top5_concepts is usually the video winner
                is_winner = (i == 0)
                task_write, task_monetize = self._build_tasks(concept, is_winner=is_winner)

                crew = Crew(
                    agents=[self.content_transmuter, self.affiliate_strategist],
                    tasks=[task_write, task_monetize],
                    process=Process.sequential,
                    verbose=True
                )

                output = crew.kickoff()
                raw_result = str(output)

                # Extract article markdown (from task_write output)
                article_md = ""
                # CrewAI returns the last task output by default; we need task_write's output
                if hasattr(output, 'tasks_output') and len(output.tasks_output) >= 1:
                    article_md = str(output.tasks_output[0].raw)
                else:
                    # Fallback: extract from raw
                    article_md = raw_result

                # Extract BentoBox JSON (from task_monetize)
                bento_data = {}
                json_match = re.search(r'```json\s*(.*?)\s*```', raw_result, re.DOTALL | re.IGNORECASE)
                if json_match:
                    try:
                        bento_data = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse bento JSON for concept: {concept_title}")

                # Validate with Pydantic if possible
                if bento_data:
                    try:
                        validated = BentoBoxData(**bento_data)
                        bento_data = validated.model_dump()
                    except Exception as e:
                        logger.warning(f"Pydantic validation warning: {e}")

                # Ensure required fields
                if not bento_data.get("article_slug"):
                    bento_data["article_slug"] = _slugify(concept_title)
                if not bento_data.get("article_title"):
                    bento_data["article_title"] = concept_title

                # Save to file
                file_path = self.save_to_markdown(article_md, bento_data, concept_title)

                results.append({
                    "concept": concept_title,
                    "slug": bento_data.get("article_slug"),
                    "file_path": str(file_path),
                    "bento_data": bento_data,
                    "success": True
                })
                logger.info(f"✅ Blog post {i+1} completed: {file_path.name}")

            except Exception as e:
                logger.error(f"❌ BlogSquad error on concept '{concept_title}': {e}")
                results.append({
                    "concept": concept_title,
                    "slug": _slugify(concept_title),
                    "error": str(e),
                    "success": False
                })

        return results


# ─────────────────────────────────────────────
# TEST / CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv

    load_dotenv()
    env_path = Path(__file__).parent.parent / ".env.local"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    # Exemple de Top 5 pour test
    test_concepts = [
        {
            "titre": "Open WebUI — ChatGPT Gratuit et Local",
            "killerfeature": "Interface web pour Ollama. Zéro abonnement, tourne sur ton laptop."
        },
        {
            "titre": "Coolify — Héberge tout sans Heroku",
            "killerfeature": "PaaS self-hosted. Postgres, Redis, apps Docker en 1 clic."
        },
    ]

    squad = BlogSquad()
    results = squad.run(test_concepts)

    for r in results:
        if r["success"]:
            print(f"✅ {r['slug']} → {r['file_path']}")
        else:
            print(f"❌ {r['concept']} → {r['error']}")
