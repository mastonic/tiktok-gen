from crewai.flow.flow import Flow, listen, start, router, or_
from pydantic import BaseModel
from typing import List, Optional, Union
import json

from agents import create_agents
from tasks import create_tasks
from crewai import Crew, Process, Task
from models import AgentOutcome, VisualPrompts, TikTokMetadata

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
    
    @start()
    def initialize(self):
        print(f"🚀 Initializing Viral Flow in {self.state.mode.upper()} mode.")
        self.agents_out = create_agents(config=self.state.agent_config, commando_mode=(self.state.mode == "commando"))
        # Distribute agents manually for easier access in listeners
        if self.state.mode == "commando":
            self.trend_radar, self.viral_judge, self.monetization_scorer, self.script_architect, self.visual_promptist, self.quality_controller, self.tiktok_distributor, self.growth_commander = self.agents_out
        else:
            self.trend_radar, self.viral_judge, self.monetization_scorer, self.script_architect, self.visual_promptist, self.quality_controller = self.agents_out

    @listen(initialize)
    def phase_sourcing(self):
        print("📡 Phase 1: Sourcing & Filtering...")
        task_scout = Task(
            description="Identifier les outils et news IA 'Killer' gratuits.",
            expected_output="Top 5 sujets avec Nom, URL et Killer Feature.",
            agent=self.trend_radar
        )
        task_filter = Task(
            description="Kill switch : Vérifier la gratuité et la viralité.",
            expected_output="Rapport de viabilité final.",
            agent=self.viral_judge,
            context=[task_scout]
        )
        
        if self.state.run_id:
            from database import save_agent_message
            save_agent_message(self.state.run_id, "TrendRadar", "ViralJudge", "info", "📡 Sourcing de 5 outils IA 'Killer' en cours...")
        
        crew = Crew(agents=[self.trend_radar, self.viral_judge], tasks=[task_scout, task_filter], verbose=True, max_rpm=30)
        self.state.viability_report = str(crew.kickoff())
        
        if self.state.run_id:
            save_agent_message(self.state.run_id, "ViralJudge", "System", "info", "✅ Viabilité confirmée. Filtrage terminé.")
            
        return "SOURCING_DONE"

    @router(phase_sourcing)
    def strategy_router(self):
        if self.state.mode == "commando":
            return "commando_strategy"
        return "standard_strategy"

    @listen("commando_strategy")
    def phase_hook_commando(self):
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
        print("✍️ Producing Script, ROI and Visuals...")
        task_roi = Task(
            description="Calculer l'économie réelle réalisée par le spectateur.",
            expected_output="Score de ROI /100.",
            agent=self.monetization_scorer
        )
        
        cta = "Abonne-toi et mets un cœur pour ne rien rater !" if self.state.mode == "commando" else "J'ai cassé Internet... encore."
        task_script = Task(
            description=f"Rédiger un script TikTok narratif LONG de 90s minimum (Signature: {cta}).",
            expected_output="Script TikTok narratif simple et détaillé de 90s minimum.",
            agent=self.script_architect,
            context=[task_roi]
        )
        
        task_visuals = Task(
            description="Créer 15 prompts cinématiques pour FLUX.",
            expected_output="Exactly 15 prompts.",
            agent=self.visual_promptist,
            output_pydantic=VisualPrompts,
            context=[task_script]
        )
        
        if self.state.run_id:
            from database import save_agent_message
            save_agent_message(self.state.run_id, "MonetizationScorer", "ScriptArchitect", "info", "💰 Calcul du ROI et des économies potentielles...")
            save_agent_message(self.state.run_id, "ScriptArchitect", "VisualPromptist", "info", "✍️ Rédaction du script TikTok long (90s+)...")
            save_agent_message(self.state.run_id, "VisualPromptist", "QualityController", "info", "🎨 Génération des 15 prompts visuels cohérents...")

        crew = Crew(
            agents=[self.monetization_scorer, self.script_architect, self.visual_promptist],
            tasks=[task_roi, task_script, task_visuals],
            verbose=True,
            max_rpm=30
        )
        self.state.visual_prompts = crew.kickoff().pydantic
        
        if self.state.run_id:
            save_agent_message(self.state.run_id, "VisualPromptist", "System", "success", "✨ Pack créatif terminé (Script 90s + 15 Prompts).")
            
        return "CONTENT_READY"

    @router(phase_content_production)
    def distribution_router(self):
        if self.state.mode == "commando":
            return "commando_distribution"
        return "standard_skip_dist"

    @listen("commando_distribution")
    def phase_tiktok_optimization(self):
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
        self.state.tiktok_metadata = crew.kickoff().pydantic
        
        if self.state.run_id:
            save_agent_message(self.state.run_id, "TikTokDistributor", "System", "success", "🚀 Métadonnées virales prêtes pour la publication.")
            
        return "DISTRIBUTION_READY"

    @listen(or_("standard_skip_dist", phase_tiktok_optimization))
    def phase_quality_control(self):
        print("🛡️ Final Phase: Quality Controller review...")
        task_qa = Task(
            description="Revue finale et assemblage JSON AgentOutcome.",
            expected_output="Final AgentOutcome validated.",
            agent=self.quality_controller,
            output_pydantic=AgentOutcome
        )
        if self.state.run_id:
            from database import save_agent_message
            save_agent_message(self.state.run_id, "QualityController", "System", "info", "🛡️ Revue finale de la qualité et du scoring...")

        crew = Crew(agents=[self.quality_controller], tasks=[task_qa], verbose=True, max_rpm=30)
        self.state.final_outcome = crew.kickoff().pydantic
        
        if self.state.run_id:
            save_agent_message(self.state.run_id, "QualityController", "System", "success", "✅ Validation finale terminée. Prêt pour l'Inbox.")
            
        return "WORKFLOW_COMPLETE"

    @listen(phase_quality_control)
    def finalize(self):
        print("🏁 Flow Complete. Saving state and returning results.")
        return self.state.final_outcome
