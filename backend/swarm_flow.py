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
                f"Ta mission 'TrendHunter' est d'identifier les 5 sujets IA/Tech les plus chauds des dernières 24h via TikTok Creative Center, Google Trends et Perplexity. "
                f"Aujourd'hui nous sommes le {now}. Focus : {focus_topic}. {recent_context}\n"
                "Identifie les recherches en hausse de >100% et croise-les avec AnswerThePublic pour trouver le Hook parfait."
            ),
            expected_output="Top 5 sujets explosifs avec Nom, URL, Killer Feature et Hook stratégique.",
            agent=self.trend_radar
        )
        task_filter = Task(
            description="Vérifie la gratuité absolue des sujets. Rejeter immédiatement (kill switch) tout sujet 'mou', payant ou déjà traité.",
            expected_output="Rapport de viabilité final. Sujet validé ou rejeté.",
            agent=self.viral_judge,
            context=[task_scout]
        )
        
        if self.state.run_id:
            save_agent_message(self.state.run_id, "TrendRadar", "ViralJudge", "info", f"📡 Recherche de nouveautés ({self.state.run_type})...")
        
        crew = Crew(agents=[self.trend_radar, self.viral_judge], tasks=[task_scout, task_filter], verbose=True, max_rpm=30)
        self.state.viability_report = str(crew.kickoff())
        
        if self.state.run_id:
            save_agent_message(self.state.run_id, "ViralJudge", "System", "info", "✅ Sujet inédit validé.")
            
        return "SOURCING_DONE"

    @router(phase_sourcing)
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
                "Analyse la puissance technique de l'outil et le gain de productivité concret. "
                "INTERDICTION de parler d'argent ou d'abonnement. Concentre-toi sur l'innovation logicielle."
            ),
            expected_output="Score d'utilité technique sur 100 et explication de la performance.",
            agent=self.tech_utility_expert
        )
        
        cta = "Abonne-toi et mets un cœur pour ne rien rater !" if self.state.mode == "commando" else "J'ai cassé Internet... encore."
        task_script = Task(
            description=(
                f"Rédiger un script TikTok narratif d'EXACTEMENT 90 à 100 secondes (Signature: {cta}). "
                "Le script doit être technique, fascinant et ultra-captivant. "
                "INTERDICTION FORMELLE de parler d'économie numérique ou de gestion de budget."
            ),
            expected_output="Script TikTok technique détaillé d'exactement 90-100 secondes.",
            agent=self.script_architect,
            context=[task_utility]
        )
        
        task_visuals = Task(
            description=(
                "Créer *strictement et exactement* 18 prompts cinématiques en anglais pour le générateur FLUX. "
                "C'est impératif : ni 17, ni 19, mais exactement 18 prompts. "
                "Chaque prompt correspond à une scène de 5 secondes, pour une vidéo totale de 90 secondes (1m30). "
                "Assure une cohérence visuelle parfaite, scénaristique et chronologique entre les 18 scènes, qui doivent se suivre."
            ),
            expected_output="A list of exactly 18 cinematic prompts in English, creating a logical story.",
            agent=self.visual_promptist,
            output_pydantic=VisualPrompts,
            context=[task_script]
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
            description=f"Revue finale et assemblage JSON AgentOutcome. {context_data}",
            expected_output="Final AgentOutcome validated.",
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
