from production import automate_visual_production
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 trigger_prod.py <script_id>")
        sys.exit(1)
    
    script_id = int(sys.argv[1])
    print(f"Triggering production for script {script_id}...")
    automate_visual_production(script_id)
