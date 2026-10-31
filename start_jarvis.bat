@echo off
set "TARGET_DIR=%~dp0Jarvis_Setup_Package"
if not exist "%TARGET_DIR%\cosmos_server.py" set "TARGET_DIR=%~dp0"

cd /d "%TARGET_DIR%"

:: Terminate any stale processes on ports 8080 & 8765 silently
powershell -NoProfile -WindowStyle Hidden -Command "Get-NetTCPConnection -LocalPort 8080, 8765 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }; Get-Process python, pythonw -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*cosmos_server.py*' -or $_.CommandLine -like '*jarvis_popup.py*' } | Stop-Process -Force -ErrorAction SilentlyContinue" >nul 2>&1
timeout /t 1 /nobreak >nul 2>&1

:: Launch Unified COSMOS 3D Humanoid Server silently in background via pythonw.exe
start "" "%TARGET_DIR%\.venv\Scripts\pythonw.exe" "%TARGET_DIR%\cosmos_server.py"

exit
