import os
import sqlite3
import glob

appdata = os.environ.get("LOCALAPPDATA", "")
chrome_user_data = os.path.join(appdata, "Google", "Chrome", "User Data")

print("Checking Chrome User Data:", chrome_user_data)
for f in glob.glob(os.path.join(chrome_user_data, "**", "Cookies"), recursive=True):
    try:
        # copy to temp to avoid lock
        import shutil
        tmp = f + ".tmp"
        shutil.copy2(f, tmp)
        conn = sqlite3.connect(tmp)
        c = conn.cursor()
        c.execute("SELECT host_key, name FROM cookies WHERE host_key LIKE '%naver%'")
        rows = c.fetchall()
        nid = [r[1] for r in rows if 'NID' in r[1]]
        if nid:
            print(f"Found in {f}: {len(rows)} cookies, NID: {nid}")
        conn.close()
        os.remove(tmp)
    except Exception as e:
        pass
