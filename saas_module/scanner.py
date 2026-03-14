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
    
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        publishedAfter=published_after,
        maxResults=50,
        order="viewCount"
    )
    response = request.execute()
    
    leads = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        # Get detailed video stats for view count
        stats_request = youtube.videos().list(
            part="statistics",
            id=video_id
        )
        stats_response = stats_request.execute()
        
        if stats_response["items"]:
            view_count = int(stats_response["items"][0]["statistics"].get("viewCount", 0))
            if view_count > 300000:
                leads.append({
                    "id": video_id,
                    "title": item["snippet"]["title"],
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "view_count": view_count,
                    "published_at": item["snippet"]["publishedAt"]
                })
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
    print(f"[{datetime.now()}] Starting YouTube Scanner...")
    all_found_leads = search_youtube()
    if all_found_leads:
        new_leads = save_leads(all_found_leads)
        print(f"Found {len(all_found_leads)} leads, {len(new_leads)} are new.")
        
        if check_auto_mode() and new_leads:
            print("Auto-mode is ON. Triggering worker for new leads...")
            import worker
            for lead in new_leads:
                print(f"Auto-processing video: {lead['id']}")
                worker.process_video(lead["id"])
    else:
        print("No matches found in the last 48h with >300k views.")

if __name__ == "__main__":
    run_scanner()
