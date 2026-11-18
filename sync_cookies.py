import os
import shutil
import glob
from pathlib import Path

src_base = Path(os.environ["LOCALAPPDATA"]) / "Google" / "Chrome" / "User Data"
dst_base = Path(r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile")

print("Checking Local State...")
if (src_base / "Local State").exists():
    shutil.copy2(src_base / "Local State", dst_base / "Local State")
    print("Copied Local State successfully!")

# Check which profile has cookies: Default or Profile 1
for prof in ["Default", "Profile 1"]:
    src_cookies = src_base / prof / "Network" / "Cookies"
    if src_cookies.exists():
        dst_dir = dst_base / "Default" / "Network"
        dst_dir.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src_cookies, dst_dir / "Cookies")
            print(f"Copied Cookies from {prof} to Default/Network/Cookies successfully!")
        except Exception as e:
            print(f"Error copying from {prof}: {e}")
