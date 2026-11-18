@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo 🚀 Antigravity Vision Studio (Full-Stack) 실행기
echo ========================================================

start "" "C:\Program Files\Python314\pythonw.exe" "%~dp0run_vision_studio.pyw"

echo [✓] 비전 스튜디오가 백그라운드에서 실행되었습니다.
