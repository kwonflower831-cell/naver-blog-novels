import http.server
import socketserver
import os
import shutil
import urllib.request
from pathlib import Path

SERVE_DIR = Path(r"D:\사용자\storyops\vision_studio")
index_file = SERVE_DIR / "index.html"
studio_file = SERVE_DIR / "Antigravity_Vision_Studio.html"

# Ensure index.html exists
if studio_file.exists():
    shutil.copy2(studio_file, index_file)

PORT = 8080
LOCAL_IP = "172.30.1.97"
MOBILE_URL = f"http://{LOCAL_IP}:{PORT}/"

print("Mobile URL:", MOBILE_URL)

# Download QR code image to artifact dir
artifact_dir = Path(r"C:\Users\kwonf\.gemini\antigravity\brain\c285795c-7c15-43e5-b14b-c9be4328a60d")
qr_path = artifact_dir / "mobile_qr.png"
qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=350x350&data={MOBILE_URL}"

try:
    urllib.request.urlretrieve(qr_api_url, str(qr_path))
    print(f"QR code saved to: {qr_path}")
except Exception as e:
    print(f"Error downloading QR: {e}")
