@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo 🚀 Antigravity Vision Studio (Full-Stack) 실행기
echo ========================================================

if exist "D:\사용자\storyops\vision_studio" (
    copy /Y "%~dp0Antigravity_Vision_Studio.html" "D:\사용자\storyops\vision_studio\Antigravity_Vision_Studio.html" >nul
    echo [✓] 바탕화면 바로가기 경로(D:\사용자\storyops\vision_studio)에 최신 스튜디오 동기화 완료!
)

start "Antigravity Vision Studio Server" /min python "%~dp0vision_studio_server.py"
timeout /t 1 /nobreak >nul

if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --app="http://localhost:8080"
) else if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app="http://localhost:8080"
) else (
    start "" "http://localhost:8080"
)

echo [✓] http://localhost:8080 에서 비전 스튜디오가 열렸습니다!
