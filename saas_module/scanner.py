import os
import json
import sqlite3
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_fixed
from dotenv import load_dotenv

# Load env from parent directory as well
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.local"))

YOUTUBE_API_KEY = os.getenv("GOOGLE_API_KEY")
DB_PATH = os.path.join(os.path.dirname(__file__), "youtube_leads.db")
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def search_youtube():
    if not YOUTUBE_API_KEY:
        print("Error: GOOGLE_API_KEY not found in environment.")
        return []
        
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    
    # AI Tech OR Open Source
    query = '"AI Tech" OR "Open Source"'
    
    # 48 hours ago
    published_after = (datetime.utcnow() - timedelta(hours=48)).isoformat() + "Z"
    
    print(f"🔍 Recherche YouTube lancée (query: '{query}')...")
    try:
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            publishedAfter=published_after,
            maxResults=50,
            order="viewCount"
        )
        response = request.execute()
    except Exception as e:
        print(f"❌ Erreur lors de l'appel API YouTube : {e}")
        raise e
    
    leads = []
    items = response.get("items", [])
    print(f"📺 {len(items)} vidéos trouvées au total. Analyse des statistiques...")
    
    for item in items:
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        try:
            stats_request = youtube.videos().list(
                part="statistics",
                id=video_id
            )
            stats_response = stats_request.execute()
            
            if stats_response["items"]:
                view_count = int(stats_response["items"][0]["statistics"].get("viewCount", 0))
                if view_count > 300000:
                    print(f"✅ Lead valide : {title} ({view_count} vues)")
                    leads.append({
                        "id": video_id,
                        "title": title,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "view_count": view_count,
                        "published_at": item["snippet"]["publishedAt"]
                    })
                else:
                    # Optional: print(f"⏭️ Ignoré (vues insuffisantes) : {title}")
                    pass
        except Exception as e:
            print(f"⚠️ Impossible de récupérer les stats pour {video_id}: {e}")
            
    return leads

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            title TEXT,
            url TEXT,
            view_count INTEGER,
            published_at TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_leads(leads):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    new_leads = []
    for lead in leads:
        cursor.execute("SELECT id FROM leads WHERE id = ?", (lead["id"],))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO leads (id, title, url, view_count, published_at, status)
                VALUES (?, ?, ?, ?, ?, 'EN ATTENTE')
            ''', (lead["id"], lead["title"], lead["url"], lead["view_count"], lead["published_at"]))
            new_leads.append(lead)
    conn.commit()
    conn.close()
    return new_leads

def check_auto_mode():
    if not os.path.exists(SETTINGS_PATH):
        return False
    try:
        with open(SETTINGS_PATH, "r") as f:
            settings = json.load(f)
        return settings.get("auto_mode", False)
    except:
        return False

def run_scanner():
    init_db()
    print(f"\n--- 🚀 SCANNER START: {datetime.now()} ---")
    try:
        all_found_leads = search_youtube()
        if all_found_leads:
            new_leads = save_leads(all_found_leads)
            print(f"📊 Résumé : {len(all_found_leads)} trouvés, {len(new_leads)} nouveaux enregistrés.")
            
            if check_auto_mode() and new_leads:
                print("⚡ Mode Auto activé. Lancement des workers...")
                import worker
                for lead in new_leads:
                    worker.process_video(lead["id"])
            return len(new_leads)
        else:
            print("📭 Aucun lead correspondant aux critères (>300k vues, <48h) n'a été trouvé.")
            return 0
    except Exception as e:
        print(f"💥 FATAL ERROR in run_scanner: {e}")
        raise e
    finally:
        print(f"--- 🏁 SCANNER END: {datetime.now()} ---\n")

if __name__ == "__main__":
    run_scanner()
