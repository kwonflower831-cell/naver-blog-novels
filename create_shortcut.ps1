$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("C:\Users\kwonf\Desktop\Antigravity Vision Studio.lnk")
$Shortcut.TargetPath = "C:\Program Files\Python314\pythonw.exe"
$Shortcut.Arguments = '"D:\사용자\naver-blog-novels\run_vision_studio.pyw"'
$Shortcut.WorkingDirectory = "D:\사용자\naver-blog-novels"
$Shortcut.Description = "Antigravity Vision Studio (Full-Stack)"
$Shortcut.IconLocation = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe, 0"
$Shortcut.Save()
Write-Host "바탕화면 바로가기 업데이트 완료"
