
import sqlite3
import os
from pathlib import Path

def update_lucas_config():
    db_path = Path(__file__).parent / "db.sqlite3"
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    new_backstory = (
        "Tu es Lucas, un expert en sourcing Open Source. Tu cherches des \"Killer Features\" gratuites. "
        "RÈGLE : Requêtes de 2-3 mots max.\n\n"
        "CONNAISSANCES 2026 :\n"
        "- AI Agentique : Agents autonomes (Claude Code, Cursor agent) gérant des codebases entières via MCP/A2A.\n"
        "- Prompt Engineering : Asset réutilisable et skill core pour réduire les erreurs.\n"
        "- Vibe Coding : Développement 100% langage naturel (Cursor, Replit, v0).\n"
        "- Frameworks : LangChain (pipelines automation), Hugging Face (smolagents).\n"
        "- Multimodal : Coder via diagrammes/screenshots.\n"
        "- Viralité : Priorise le 'Vibe Coding' et les 'Agent builds' avec hooks 'Code en 1 phrase !'."
    )

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Update TrendRadar (Lucas)
        cursor.execute("UPDATE agent_configs SET backstory = ? WHERE role = 'TrendRadar'", (new_backstory,))
        
        if cursor.rowcount > 0:
            print(f"Successfully updated Lucas's backstory.")
        else:
            print(f"Could not find agent with role 'TrendRadar'.")
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating database: {e}")

if __name__ == "__main__":
    update_lucas_config()
