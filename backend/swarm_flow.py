from crewai.flow.flow import Flow, listen, start, router, or_
from pydantic import BaseModel
from typing import List, Optional, Union
import json
import sys
from datetime import datetime

from agents import create_agents
from tasks import create_tasks
from crewai import Crew, Process, Task
from models import AgentOutcome, VisualPrompts, TikTokMetadata
from database import save_agent_message, SessionLocal, RunHistory

class SwarmState(BaseModel):
    mode: str = "standard" # "standard" or "commando"
    run_type: str = "matin"
    agent_config: dict = {}
    
    # Collective memory
    sourcing_report: str = ""
    viability_report: str = ""
    hook_strategy: Optional[str] = None
    roi_report: str = ""
    script_content: str = ""
    visual_prompts: Optional[VisualPrompts] = None
    tiktok_metadata: Optional[TikTokMetadata] = None
    final_outcome: Optional[AgentOutcome] = None
    run_id: Optional[str] = None
    fiche_de_choc: Optional[str] = None

class ViralFlow(Flow[SwarmState]):
    
    def _check_cancelled(self):
        """Check if the current run has been cancelled in the database."""
        if not self.state.run_id:
            return False
            
        try:
            db = SessionLocal()
            run = db.query(RunHistory).filter(RunHistory.run_id == self.state.run_id).first()
            is_stopped = run.is_cancelled if run else False
            db.close()
            
            if is_stopped:
                print(f"🛑 [FLOW] Run {self.state.run_id} marked as CANCELLED. Stopping flow.")
                save_agent_message(self.state.run_id, "System", "Flow", "danger", "🛑 Scan arrêté manuellement par l'utilisateur.")
                return True
        except Exception as e:
            print(f"Error checking cancellation status: {e}")
        return False

    @start()
    def initialize(self):
        print(f"🚀 Initializing Viral Flow in {self.state.mode.upper()} mode.")
        self.agents_out = create_agents(config=self.state.agent_config, commando_mode=(self.state.mode == "commando"))
        # Distribute agents manually for easier access in listeners
        if self.state.mode == "commando":
            self.trend_radar, self.viral_judge, self.tech_utility_expert, self.script_architect, self.visual_promptist, self.quality_controller, self.tiktok_distributor, self.growth_commander = self.agents_out
        else:
            self.trend_radar, self.viral_judge, self.tech_utility_expert, self.script_architect, self.visual_promptist, self.quality_controller = self.agents_out

    @listen(initialize)
    def phase_sourcing(self):
        if self._check_cancelled(): return "FLOW_STOPPED"
        print("📡 Phase 1: Sourcing & Filtering...")
        
        # 💥 STRATÉGIE ANTI-BOUCLE (Machine à Cash) 💥
        recent_titles = []
        try:
            db = SessionLocal()
            from database import ScriptInbox
            recent_scripts = db.query(ScriptInbox).order_by(ScriptInbox.id.desc()).limit(15).all()
            recent_titles = [s.title for s in recent_scripts if s.title]
            db.close()
        except Exception as e:
            print(f"Error fetching recent titles: {e}")

        recent_context = ""
        if recent_titles:
            recent_context = f"\n\n🚨 RÈGLE CRITIQUE : TU DOIS IGNORER CES SUJETS : {', '.join(recent_titles)}. TROUVE DU NOUVEAU !"

        now = datetime.now().strftime("%d/%m/%Y")
        # Dynamic focus based on run_type
        if self.state.run_type == "matin":
            focus_topic = "News IA, Outils gratuits, Nouveautés LLMs"
        else:
            focus_topic = "Tutoriels techniques IA, Automatisation, Nouveaux agents IA Open-Source"
        
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
            agent=self.trend_radar
        )
        task_filter = Task(
            description=(
                "Filtre impitoyable. RÈGLE : Rejet immédiat (Kill Switch) de tout sujet 'mou' ou payant. "
                "Seule la tech disruptive et gratuite passe. Ce module remplace la 'créativité' par de l'extraction de données pure."
            ),
            expected_output="Rapport de viabilité final. Sujet validé ou rejeté (Kill Switch).",
            agent=self.viral_judge,
            context=[task_scout]
        )
        
        if self.state.run_id:
            save_agent_message(self.state.run_id, "TrendRadar", "ViralJudge", "info", f"📡 Recherche de nouveautés ({self.state.run_type})...")
        
        crew = Crew(agents=[self.trend_radar, self.viral_judge], tasks=[task_scout, task_filter], verbose=True, max_rpm=30)
        self.state.viability_report = str(crew.kickoff())
        
        if self.state.run_id:
            save_agent_message(self.state.run_id, "ViralJudge", "System", "info", "✅ Sourcing terminé. En attente de validation humaine du Top 5.")
            
        return "SOURCING_DONE"

    @listen("SOURCING_DONE")
    def phase_human_validation(self):
        if self._check_cancelled(): return "FLOW_STOPPED"
        print("🛸 [COMMANDO] Waiting for human validation of the Top 5...")
        from agents import ask_human_in_loop
        question = (
            "Voici le Top 5 des news IA Open Source identifiées par le TrendRadar :\n\n"
            f"{self.state.viability_report}\n\n"
            "Dis-moi laquelle de ces news tu souhaites traiter, ou donne tes instructions personnalisées (ton choix devient la SEULE source de vérité)."
        )
        self.state.fiche_de_choc = ask_human_in_loop("Manager", "Validation humaine du Top 5 News", question)
        
        if self.state.run_id:
            save_agent_message(self.state.run_id, "Manager", "System", "success", f"Choix humain reçu : {self.state.fiche_de_choc[:100]}...")
            
        return "VALIDATION_DONE"

    @router("VALIDATION_DONE")
    def strategy_router(self):
        if self.state.mode == "commando":
            return "commando_strategy"
        return "standard_strategy"

    @listen("commando_strategy")
    def phase_hook_commando(self):
        if self._check_cancelled(): return "FLOW_STOPPED"
        print("🔥 COMMANDO 10K: ViralGrowthCommander dictating Hook...")
        task_hook = Task(
            description="Dicte le Hook viral le plus violent possible avant l'écriture.",
            expected_output="Consigne de Hook agressive.",
            agent=self.growth_commander
        )
        if self.state.run_id:
            from database import save_agent_message
            save_agent_message(self.state.run_id, "ViralGrowthCommander", "ScriptArchitect", "warning", "🔥 Mode Commando : Injection d'un Hook agressif.")
        
        crew = Crew(agents=[self.growth_commander], tasks=[task_hook], verbose=True, max_rpm=30)
        self.state.hook_strategy = str(crew.kickoff())
        return "STRATEGY_READY"

    @listen(or_("standard_strategy", phase_hook_commando))
    def phase_content_production(self):
        if self._check_cancelled(): return "FLOW_STOPPED"
        print("✍️ Producing Script, Tech Utility and Visuals...")
        task_utility = Task(
            description=(
                f"Analyse en profondeur la news technique suivante : {self.state.fiche_de_choc}\n"
                "Architecture, avantages tech, points négatifs et axes d'amélioration. "
                "Rassemble des éléments pour une histoire ou une expérience utilisateur marquante avec cet outil. "
                "INTERDICTION de parler d'argent ou d'abonnement."
            ),
            expected_output="Analyse technique complète (Avantages, Inconvénients, Storytelling technique).",
            agent=self.tech_utility_expert
        )
        
        task_script = Task(
            description=(
                f"ORDRE COMMANDO : Transforme la news suivante en un script TikTok agressif de 90s : {self.state.fiche_de_choc}\n"
                "RÈGLE DE TEMPORALITÉ : Interdiction de parler de tech pré-2025. Nous sommes en 2026. "
                "STYLE : Cynique, expert, zéro ton scolaire. Pas de 'Simple, non ?'. "
                "STRUCTURE : Template 'Le Benchmark Killer' (Hook violent -> Confrontation data -> Chute technique). "
                "SOURCE : Ton script doit se baser EXCLUSIVEMENT sur cette news."
            ),
            expected_output="Script technique 100% Data sans fiction (Style Cash Machine).",
            agent=self.script_architect,
            context=[task_utility]
        )
        
        task_visuals = Task(
            description=(
                "Crée 18 prompts cinématiques via la formule Veo 3.1 : [Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]. "
                "INTERDICTION : Robots, cyborgs, cerveaux filaires. "
                "REQUIS : Terminaux, schémas, benchmarks, logos officiels. "
                "Ambiance : Tech-Noir / Cyberpunk contrasté."
            ),
            expected_output="Exactly 18 prompts following the Veo 3.1 formula (100% Data/UI).",
            agent=self.visual_promptist,
            context=[task_script],
            output_pydantic=VisualPrompts
        )
        
        if self.state.run_id:
            save_agent_message(self.state.run_id, "TechUtilityExpert", "ScriptArchitect", "info", "⚙️ Analyse de la valeur technique et utilitaire...")
            save_agent_message(self.state.run_id, "ScriptArchitect", "VisualPromptist", "info", "✍️ Rédaction du script technique (90s+)...")
            save_agent_message(self.state.run_id, "VisualPromptist", "QualityController", "info", "🎨 Génération des 18 prompts visuels cohérents...")

        crew = Crew(
            agents=[self.tech_utility_expert, self.script_architect, self.visual_promptist],
            tasks=[task_utility, task_script, task_visuals],
            verbose=True,
            max_rpm=30
        )
        result = crew.kickoff()
        
        # Save intermediate outputs to state to prevent QualityController hallucination
        self.state.roi_report = getattr(task_utility.output, 'raw', str(task_utility.output)) if task_utility.output else ""
        self.state.script_content = getattr(task_script.output, 'raw', str(task_script.output)) if task_script.output else ""
        
        if hasattr(result, 'pydantic') and result.pydantic:
            self.state.visual_prompts = result.pydantic
        else:
            print("⚠️ [FLOW] VisualPromptist failed to produce Pydantic output. Using fallback.")
            # Fallback will be handled in main.py or next steps
            placeholder_prompts = [f"Cinematic prompt for scene {i+1} of AI documentary" for i in range(18)]
            self.state.visual_prompts = VisualPrompts(prompts=placeholder_prompts)
        
        if self.state.run_id:
            save_agent_message(self.state.run_id, "VisualPromptist", "System", "success", "✨ Pack créatif terminé (Script 90s + 18 Prompts).")
            
        return "CONTENT_READY"

    @router(phase_content_production)
    def distribution_router(self):
        if self.state.mode == "commando":
            return "commando_distribution"
        return "standard_skip_dist"

    @listen("commando_distribution")
    def phase_tiktok_optimization(self):
        if self._check_cancelled(): return "FLOW_STOPPED"
        print("📈 COMMANDO: TikTokDistributor optimizing Algorithm distribution...")
        task_dist = Task(
            description="Générer description et hashtags optimisés.",
            expected_output="Strategic TikTok Metadata.",
            agent=self.tiktok_distributor,
            output_pydantic=TikTokMetadata
        )
        if self.state.run_id:
            from database import save_agent_message
            save_agent_message(self.state.run_id, "TikTokDistributor", "System", "info", "📈 Optimisation SEO TikTok : Description & Hashtags...")

        crew = Crew(agents=[self.tiktok_distributor], tasks=[task_dist], verbose=True, max_rpm=30)
        result = crew.kickoff()
        if hasattr(result, 'pydantic') and result.pydantic:
            self.state.tiktok_metadata = result.pydantic
        else:
            print("⚠️ [FLOW] TikTokDistributor failed to produce Pydantic output.")
        
        if self.state.run_id:
            save_agent_message(self.state.run_id, "TikTokDistributor", "System", "success", "🚀 Métadonnées virales prêtes pour la publication.")
            
        return "DISTRIBUTION_READY"

    @listen(or_("standard_skip_dist", phase_tiktok_optimization))
    def phase_quality_control(self):
        if self._check_cancelled(): return "FLOW_STOPPED"
        print("🛡️ Final Phase: Quality Controller review...")
        
        # Assemble context so QualityController doesn't hallucinate
        context_data = f"""
Voici le contenu généré par tes collègues. Tu DOIS assembler ce contenu EXACTEMENT sans en inventer un nouveau.
- Outils trouvés (Viability) : {self.state.viability_report[:1000] if self.state.viability_report else 'Aucun'}
- Script final (NE PAS MODIFIER) : {self.state.script_content[:3000] if self.state.script_content else 'Aucun'}
- Prompts d'images générés (DOIVENT RESTER EXACTEMENT CES PROMPTS, y en a {len(self.state.visual_prompts.prompts) if self.state.visual_prompts else 0}) : {self.state.visual_prompts.prompts if self.state.visual_prompts else 'Aucun'}
"""
        task_qa = Task(
            description=(
                "Filtre de rejet ultime (Kill Switch) iM-System V9 :\n"
                "1. News Obsolète ? (Rejet si pré-2025).\n"
                "2. Incohérence Technique ? (Mélange cloud/local insensé).\n"
                "3. Ton Scolaire ? (Rejet si ton trop descriptif ou faible).\n"
                "Si rejeté, renvoie : 'ORDRE COMMANDO : Script REJETÉ. Corrige l''anachronisme et adopte un ton plus agressif.'\n"
                f"Contenu à assembler : {context_data}"
            ),
            expected_output="Package final validé (Anti-Obsolescence, Rigueur Tech).",
            agent=self.quality_controller,
            output_pydantic=AgentOutcome
        )
        if self.state.run_id:
            save_agent_message(self.state.run_id, "QualityController", "System", "info", "🛡️ Revue finale de la qualité et du scoring...")

        crew = Crew(agents=[self.quality_controller], tasks=[task_qa], verbose=True, max_rpm=30)
        result = crew.kickoff()
        if hasattr(result, 'pydantic') and result.pydantic:
            self.state.final_outcome = result.pydantic
        else:
            print("⚠️ [FLOW] QualityControl failed to produce Pydantic outcome.")
        
        if self.state.run_id:
            save_agent_message(self.state.run_id, "QualityController", "System", "success", "✅ Validation finale terminée. Prêt pour l'Inbox.")
            
        return "WORKFLOW_COMPLETE"

    @listen(phase_quality_control)
    def finalize(self):
        if self.state.final_outcome is None:
             print("🏁 Flow stopped or failed earlier.")
             return None
        print("🏁 Flow Complete. Saving state and returning results.")
        return self.state.final_outcome
