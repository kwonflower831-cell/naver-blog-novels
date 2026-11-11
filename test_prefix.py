import sqlite3, shutil, os

db_path = r"C:\Users\kwonf\AppData\Local\Google\Chrome\User Data\Profile 1\Network\Cookies"
shutil.copy2(db_path, "temp_c.db")
conn = sqlite3.connect("temp_c.db")
cur = conn.cursor()
cur.execute("SELECT name, substr(encrypted_value, 1, 3) FROM cookies WHERE name in ('NID_AUT', 'NID_SES')")
for r in cur.fetchall():
    print(r[0], r[1])
conn.close()
os.remove("temp_c.db")
