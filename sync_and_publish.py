import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SRC_USER_DATA = Path(r"C:\Users\kwonf\AppData\Local\Google\Chrome\User Data")
SRC_PROF = SRC_USER_DATA / "Profile 1"
DST_PROFILE = Path(r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile")

def is_chrome_running():
    try:
        out = subprocess.check_output('tasklist /fi "IMAGENAME eq chrome.exe"', shell=True, text=True, errors="replace")
        return "chrome.exe" in out.lower()
    except Exception:
        return False

print("Waiting for existing Chrome to close so cookies can be copied...", flush=True)
closed = False
for sec in range(300):
    if not is_chrome_running():
        print("Chrome closed! Proceeding to copy cookies...", flush=True)
        closed = True
        break
    if sec % 10 == 0:
        print(f"Waiting for Chrome to close... ({sec}s elapsed)", flush=True)
    time.sleep(1)

if not closed:
    print("Timed out waiting for Chrome to close.", flush=True)
    sys.exit(1)

time.sleep(1.5)

# Copy Local State and Profile 1
DST_PROFILE.mkdir(parents=True, exist_ok=True)
if (SRC_USER_DATA / "Local State").exists():
    shutil.copy2(SRC_USER_DATA / "Local State", DST_PROFILE / "Local State")

dst_default = DST_PROFILE / "Default"
dst_default.mkdir(parents=True, exist_ok=True)

for item in ["Preferences", "Secure Preferences"]:
    f = SRC_PROF / item
    if f.exists():
        try:
            shutil.copy2(f, dst_default / item)
        except Exception as e:
            print("Pref copy note:", e)

net_src = SRC_PROF / "Network"
if net_src.exists():
    net_dst = dst_default / "Network"
    net_dst.mkdir(parents=True, exist_ok=True)
    for f in net_src.iterdir():
        if f.is_file():
            try:
                shutil.copy2(f, net_dst / f.name)
            except Exception as e:
                print(f"Network copy note ({f.name}):", e)

print("Cookies and profile copied successfully! Starting publisher...", flush=True)

# Run publish_ch9_chrome.py
cmd = [sys.executable, r"C:\Users\kwonf\.gemini\antigravity\scratch\novels\publish_ch9_chrome.py"]
res = subprocess.run(cmd, capture_output=False)
sys.exit(res.returncode)
