import sqlite3, shutil, os

for prof in ['Default', 'Profile 1']:
    cookie_path = rf"C:\Users\kwonf\AppData\Local\Google\Chrome\User Data\{prof}\Network\Cookies"
    if not os.path.exists(cookie_path):
        cookie_path = rf"C:\Users\kwonf\AppData\Local\Google\Chrome\User Data\{prof}\Cookies"
    if os.path.exists(cookie_path):
        temp_path = rf"C:\Users\kwonf\.gemini\antigravity\scratch\cookies_temp.db"
        try:
            shutil.copy2(cookie_path, temp_path)
            conn = sqlite3.connect(temp_path)
            cur = conn.cursor()
            cur.execute("SELECT host_key, name, length(encrypted_value) FROM cookies WHERE host_key LIKE '%naver.com%'")
            rows = cur.fetchall()
            print(f"{prof}: found {len(rows)} naver cookies")
            names = [r[1] for r in rows if 'NID' in r[1]]
            print(f"{prof} NID cookies:", names)
            conn.close()
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            print(f"{prof} error:", e)
