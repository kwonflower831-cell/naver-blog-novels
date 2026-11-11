import os, shutil, subprocess, time, urllib.request, json
from pathlib import Path
from playwright.sync_api import sync_playwright

SRC_USER_DATA = Path(r"C:\Users\kwonf\AppData\Local\Google\Chrome\User Data")
SRC_PROF = SRC_USER_DATA / "Profile 1"
DST_DIR = Path(r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-debug-profile")

if DST_DIR.exists():
    try:
        shutil.rmtree(DST_DIR)
    except Exception as e:
        print("rmtree:", e)

DST_DIR.mkdir(parents=True, exist_ok=True)
DST_DEF = DST_DIR / "Default"
DST_DEF.mkdir(parents=True, exist_ok=True)

# Copy Local State
shutil.copy2(SRC_USER_DATA / "Local State", DST_DIR / "Local State")

# Robocopy Profile 1 to DST_DEF excluding Cache
cmd = f'robocopy "{SRC_PROF}" "{DST_DEF}" /E /XD Cache "Code Cache" GPUCache Service\\ Worker\\CacheStorage /NFL /NDL /NJH /NJS /nc /ns /np'
subprocess.run(cmd, shell=True)

print("Profile copied successfully. Testing Playwright...")

try:
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(DST_DIR),
            channel="chrome",
            headless=True
        )
        page = ctx.new_page()
        page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded")
        time.sleep(3)
        print("Page URL after goto:", page.url)
        cookies = ctx.cookies()
        nids = [c["name"] for c in cookies if "NID" in c["name"]]
        print("NID cookies found:", nids)
        ctx.close()
except Exception as e:
    print("Error:", e)
