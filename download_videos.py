import requests
import os

# --- CONFIGURATION ---
VPS_IP = "85.31.239.237"
API_URL = f"http://{VPS_IP}:5656"
DOWNLOAD_DIR = "downloads"

def list_available_videos():
    try:
        print(f"Connexion au VPS ({VPS_IP})...")
        response = requests.get(f"{API_URL}/api/contents")
        if response.status_code != 200:
            print("Erreur: Impossible de récupérer la liste des vidéos.")
            return []
        
        data = response.json()
        ready_videos = [v for v in data if v.get("hasFinalVideo")]
        return ready_videos
    except Exception as e:
        print(f"Erreur de connexion: {e}")
        return []

def download_video(video_data):
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    
    video_url = f"{API_URL}{video_data['finalVideoUrl']}"
    file_name = f"{video_data['id']}_{video_data['title'].replace(' ', '_')}.mp4"
    save_path = os.path.join(DOWNLOAD_DIR, file_name)
    
    print(f"\nTéléchargement de : {video_data['title']}...")
    print(f"URL : {video_url}")
    
    try:
        with requests.get(video_url, stream=True) as r:
            r.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"TERMINE ! Vidéo enregistrée dans : {save_path}")
    except Exception as e:
        print(f"Échec du téléchargement : {e}")

def main():
    print("=== iM System - Video Downloader ===")
    videos = list_available_videos()
    
    if not videos:
        print("Aucune vidéo terminée n'est disponible pour le moment sur le VPS.")
        return

    print("\nVidéos disponibles :")
    for i, v in enumerate(videos):
        print(f"[{i + 1}] {v['title']} (ID: {v['id']})")
    
    try:
        choice = int(input("\nChoisissez le numéro de la vidéo à télécharger (0 pour annuler) : "))
        if choice == 0:
            print("Annulé.")
            return
        
        if 1 <= choice <= len(videos):
            download_video(videos[choice - 1])
        else:
            print("Choix invalide.")
    except ValueError:
        print("Veuillez entrer un nombre valide.")

if __name__ == "__main__":
    main()
