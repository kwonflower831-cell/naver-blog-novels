import os
import sys
import time
import shutil
import urllib.request
import subprocess
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def sync_studio_to_storyops():
    storyops_dir = Path(r"D:\사용자\storyops\vision_studio")
    html_src = BASE_DIR / "Antigravity_Vision_Studio.html"
    if storyops_dir.exists() and html_src.exists():
        try:
            shutil.copy2(str(html_src), str(storyops_dir / "Antigravity_Vision_Studio.html"))
        except Exception:
            pass

def is_server_running(url="http://localhost:8080/api/novels"):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VisionStudioLauncher"})
        with urllib.request.urlopen(req, timeout=1.0) as res:
            return res.status == 200
    except Exception:
        return False

def start_server():
    if is_server_running():
        return True

    python_exe = sys.executable
    if "python.exe" in python_exe.lower():
        cand = python_exe.lower().replace("python.exe", "pythonw.exe")
        if os.path.exists(cand):
            python_exe = cand

    server_script = BASE_DIR / "vision_studio_server.py"
    creation_flags = 0x00000008 if sys.platform == "win32" else 0  # DETACHED_PROCESS

    subprocess.Popen(
        [python_exe, str(server_script)],
        cwd=str(BASE_DIR),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags,
    )

    for _ in range(30):
        if is_server_running():
            return True
        time.sleep(0.15)

    return is_server_running()

def open_ui():
    chrome_paths = [
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for cp in chrome_paths:
        if os.path.exists(cp):
            try:
                subprocess.Popen([cp, "--app=http://localhost:8080"])
                return
            except Exception:
                pass
    webbrowser.open("http://localhost:8080")

def main():
    try:
        sync_studio_to_storyops()
        start_server()
        open_ui()
    except Exception as e:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Antigravity Vision Studio", f"실행 중 오류가 발생했습니다:\n{e}")
        except Exception:
            pass

if __name__ == "__main__":
    main()
