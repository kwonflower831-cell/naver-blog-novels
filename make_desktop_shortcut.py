import os
import shutil
from pathlib import Path

# 1. Permanent storage setup
src_html = Path(r"C:\Users\kwonf\.gemini\antigravity\brain\c285795c-7c15-43e5-b14b-c9be4328a60d\antigravity_vision_studio.html")
dest_dir = Path(r"D:\사용자\storyops\vision_studio")
dest_dir.mkdir(parents=True, exist_ok=True)
dest_html = dest_dir / "Antigravity_Vision_Studio.html"

shutil.copy2(src_html, dest_html)
print(f"Copied HTML to: {dest_html}")

# 2. Create desktop shortcut via PowerShell COM object
desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
shortcut_path = desktop / "Antigravity Vision Studio.lnk"
chrome_exe = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
html_url = f"file:///{dest_html.as_posix()}"

ps_script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{chrome_exe}"
$Shortcut.Arguments = '--app="{html_url}"'
$Shortcut.WorkingDirectory = "{dest_dir}"
$Shortcut.Description = "Antigravity Vision Studio"
$Shortcut.IconLocation = "{chrome_exe}, 0"
$Shortcut.Save()
"""

ps_file = dest_dir / "create_shortcut.ps1"
ps_file.write_text(ps_script, encoding="utf-8")

import subprocess
res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps_file)], capture_output=True, text=True)
print("PowerShell exit code:", res.returncode)
if res.stderr:
    print("Stderr:", res.stderr)

if shortcut_path.exists():
    print(f"SUCCESS: Shortcut created at {shortcut_path}")
else:
    print("FAILED to create shortcut")
