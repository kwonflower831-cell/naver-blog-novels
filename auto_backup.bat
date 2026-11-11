@echo off
chcp 65001 >nul
title 소설 GitHub 자동 백업
cd /d "C:\Users\kwonf\.gemini\antigravity\scratch\novels"
python auto_backup.py
echo.
echo 창을 닫으려면 아무 키나 누르세요...
pause >nul
