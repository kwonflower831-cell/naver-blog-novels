import re

html_path = r"C:\Users\kwonf\.gemini\antigravity\brain\c285795c-7c15-43e5-b14b-c9be4328a60d\antigravity_vision_studio.html"
with open(html_path, "r", encoding="utf-8") as f:
    text = f.read()

matches = re.findall(r'(?:src|href)=["\']([^"\']+\.(?:mp4|png|jpg|jpeg|webm))["\']', text, re.IGNORECASE)
print("Referenced media files:")
for m in set(matches):
    print(" -", m)
