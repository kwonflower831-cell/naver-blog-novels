import os, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

SRC_USER_DATA = Path(r"C:\Users\kwonf\AppData\Local\Google\Chrome\User Data")
DST_PROFILE = Path(r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-cloned-profile")

if DST_PROFILE.exists():
    try:
        shutil.rmtree(DST_PROFILE)
    except Exception as e:
        print("rmtree error:", e)

DST_PROFILE.mkdir(parents=True, exist_ok=True)

# Copy Local State
shutil.copy2(SRC_USER_DATA / "Local State", DST_PROFILE / "Local State")

# Copy Profile 1 as Default in DST_PROFILE
dst_default = DST_PROFILE / "Default"
dst_default.mkdir(parents=True, exist_ok=True)

# We specifically need Network/Cookies, Preferences, and Login Data
src_prof = SRC_USER_DATA / "Profile 1"

for item in ["Preferences", "Secure Preferences"]:
    f = src_prof / item
    if f.exists():
        shutil.copy2(f, dst_default / item)

net_src = src_prof / "Network"
if net_src.exists():
    net_dst = dst_default / "Network"
    net_dst.mkdir(parents=True, exist_ok=True)
    for f in net_src.iterdir():
        if f.is_file():
            try:
                shutil.copy2(f, net_dst / f.name)
            except Exception as e:
                print(f"Failed copy {f.name}: {e}")

print("Cloned profile structure created.")

try:
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(DST_PROFILE),
            channel="chrome",
            headless=True
        )
        page = ctx.new_page()
        page.goto("https://blog.naver.com/kwonflower58", wait_until="domcontentloaded")
        cookies = ctx.cookies()
        nid = [c['name'] for c in cookies if 'NID' in c['name']]
        print("Cloned profile NID cookies after goto:", nid)
        
        # Test navigation to write page to see if redirected to login
        page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded")
        print("Final URL:", page.url)
        ctx.close()
except Exception as e:
    print("Test error:", e)
