Get-NetTCPConnection -LocalPort 8080, 8765 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe' or Name = 'python.exe'" |
Where-Object {
    $_.CommandLine -like "*cosmos_server.py*" -or $_.CommandLine -like "*jarvis_popup.py*"
} |
ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force
}

Start-Sleep -Seconds 1
Start-Process -FilePath ".\.venv\Scripts\pythonw.exe" -ArgumentList "cosmos_server.py" -WorkingDirectory "$PSScriptRoot" -WindowStyle Hidden
