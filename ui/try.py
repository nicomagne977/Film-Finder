# simple_vlc_launcher.py

import subprocess
import tempfile
import yt_dlp
import os
import time

# Télécharger
url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
temp_video_path = "/mnt/c/Users/utilisateur/Desktop/UFSC/POO/Film_finder/data/video.mp4"

print("Téléchargement...")
with yt_dlp.YoutubeDL({'format': 'best[height<=480]', 'outtmpl': temp_video_path}) as ydl:
    ydl.download([url])

# Vérifier que le fichier existe
if not os.path.exists(temp_video_path):
    print("❌ Le fichier n'a pas été créé!")
    exit(1)

print(f"✅ Fichier créé: {temp_video_path}")

# Conversion CORRECTE du chemin
# /mnt/c/Users/utilisateur/Desktop/... → C:\Users\utilisateur\Desktop\...
windows_video_path = temp_video_path.replace("/mnt/c/", "C:\\").replace("/", "\\")

print(f"🎵 Chemin Windows: {windows_video_path}")

# Lancer VLC Windows directement
vlc_path = "/mnt/c/Program Files/VideoLAN/VLC/vlc.exe"
print("Lancement VLC Windows...")

# Utiliser Popen au lieu de run pour ne pas bloquer
subprocess.Popen([vlc_path, windows_video_path])
