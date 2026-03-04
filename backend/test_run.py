import sys
import os

# Ensure the backend directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crewai import Crew, Process
from agents import create_agents
from tasks import create_tasks

def test_run():
    print("🚀 Lancement Local de l'iM System (Test Run)")
    scout, gatekeeper, strategist, copywriter, producer = create_agents()
    
    # Running a 'matin' cycle for testing
    tasks = create_tasks(scout, gatekeeper, strategist, copywriter, producer, run_type="matin")
    
    crew = Crew(
        agents=[scout, gatekeeper, strategist, copywriter, producer],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    
    print("\n\n" + "="*50)
    print("🏆 RÉSULTAT FINAL:")
    print("="*50)
    print(result)

if __name__ == "__main__":
    test_run()
