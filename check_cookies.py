import sqlite3
import glob

for f in glob.glob(r'C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile\**\Cookies', recursive=True):
    try:
        conn = sqlite3.connect(f)
        c = conn.cursor()
        c.execute("SELECT host_key, name FROM cookies WHERE host_key LIKE '%naver%'")
        rows = c.fetchall()
        print(f"File: {f}")
        print(f"Total naver cookies: {len(rows)}")
        nid_cookies = [r[1] for r in rows if 'NID' in r[1]]
        print(f"NID cookies: {nid_cookies}")
    except Exception as e:
        print(f"Error {f}: {e}")
