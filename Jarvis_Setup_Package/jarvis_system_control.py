"""Hidden, parameterized PowerShell helpers for Windows application control."""

import base64
import json
import os
import shutil
import subprocess
import sys


_APP_ALIASES = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "firefox": "firefox",
    "spotify": "spotify",
    "vs code": "code",
    "visual studio code": "code",
    "code": "code",
    "word": "winword",
    "microsoft word": "winword",
    "excel": "excel",
    "microsoft excel": "excel",
    "powerpoint": "powerpnt",
    "notepad": "notepad",
    "calculator": "calculator",
    "discord": "discord",
    "slack": "slack",
}

_PROTECTED_PROCESSES = {
    "explorer",
    "svchost",
    "csrss",
    "wininit",
    "winlogon",
    "services",
    "lsass",
    "smss",
    "system",
    "registry",
    "cosmos",
}


def _ps_quote(value):
    return "'" + value.replace("'", "''") + "'"


def _powershell_executable():
    return shutil.which("pwsh") or shutil.which("powershell")


def _run_powershell(script):
    if sys.platform != "win32":
        return False, "Application control is available only on Windows."

    executable = _powershell_executable()
    if not executable:
        return False, "PowerShell could not be found on this system."

    encoded_script = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0

    try:
        result = subprocess.run(
            [
                executable,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-EncodedCommand",
                encoded_script,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=25,
            creationflags=subprocess.CREATE_NO_WINDOW,
            startupinfo=startupinfo,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, "PowerShell did not complete the application request in time."
    except OSError as error:
        return False, f"PowerShell could not run: {error}"

    output = result.stdout.strip()
    if output:
        try:
            response = json.loads(output)
        except json.JSONDecodeError:
            response = None
        if isinstance(response, dict) and "success" in response:
            detail = response.get("message") or response.get("error") or ""
            return bool(response["success"]), str(detail)

    detail = result.stderr.strip() or output or "PowerShell returned no result."
    return False, detail


def open_application(app_name, resolved_target=None):
    """Open one named application without executing arbitrary shell input."""
    app_name = app_name.strip()
    if not app_name:
        return False, "Please specify an application name."

    target = (resolved_target or "").strip()
    script = f"""
$ErrorActionPreference = 'Stop'
$appName = {_ps_quote(app_name)}
$resolvedTarget = {_ps_quote(target)}
$launched = $false
$lastError = ''
if ($resolvedTarget) {{
    try {{
        Start-Process -FilePath $resolvedTarget -ErrorAction Stop
        $launched = $true
    }} catch {{
        $lastError = $_.Exception.Message
    }}
}}
if (-not $launched) {{
    try {{
        Start-Process -FilePath $appName -ErrorAction Stop
        $launched = $true
    }} catch {{
        $lastError = $_.Exception.Message
    }}
}}
if (-not $launched) {{
    try {{
        $escapedName = [WildcardPattern]::Escape($appName)
        $app = Get-StartApps | Where-Object {{ $_.Name -like ("*" + $escapedName + "*") }} | Select-Object -First 1
        if ($app) {{
            Start-Process -FilePath 'explorer.exe' -ArgumentList ("shell:AppsFolder\\" + $app.AppID) -ErrorAction Stop
            $launched = $true
        }}
    }} catch {{
        $lastError = $_.Exception.Message
    }}
}}
if ($launched) {{
    @{{ success = $true; message = '' }} | ConvertTo-Json -Compress
}} else {{
    @{{ success = $false; error = $lastError }} | ConvertTo-Json -Compress
}}
"""
    return _run_powershell(script)


def close_application(app_name, force=False):
    """Close matching application processes while protecting Windows and COSMOS."""
    app_name = app_name.strip()
    if not app_name:
        return False, "Please specify an application name."

    normalized_name = " ".join(app_name.casefold().split())
    process_name = _APP_ALIASES.get(normalized_name, normalized_name)
    process_name = os.path.splitext(process_name)[0].strip()
    if process_name.casefold() in _PROTECTED_PROCESSES:
        return False, f"Closing the protected system process '{process_name}' is blocked."

    force_value = "$true" if force else "$false"
    script = f"""
$ErrorActionPreference = 'Stop'
$processName = {_ps_quote(process_name)}
$forceClose = {force_value}
$protectedNames = @({", ".join(_ps_quote(name) for name in sorted(_PROTECTED_PROCESSES))})
$currentCosmosPid = {os.getpid()}
$currentPowerShellPid = $PID
$pattern = "*" + [WildcardPattern]::Escape($processName) + "*"
$matches = @(Get-Process -Name $pattern -ErrorAction SilentlyContinue | Where-Object {{
    $protectedNames -notcontains $_.ProcessName.ToLowerInvariant() -and
    $_.Id -ne $currentCosmosPid -and
    $_.Id -ne $currentPowerShellPid
}})
if ($matches.Count -eq 0) {{
    @{{ success = $false; error = 'No matching running application was found.' }} | ConvertTo-Json -Compress
    exit
}}
if ($forceClose) {{
    $matches | Stop-Process -Force -ErrorAction SilentlyContinue
}} else {{
    $closeable = @($matches | Where-Object {{ $_.MainWindowHandle -ne 0 }})
    if ($closeable.Count -eq 0) {{
        @{{ success = $false; error = 'No closeable application window was found.' }} | ConvertTo-Json -Compress
        exit
    }}
    foreach ($process in $closeable) {{
        [void]$process.CloseMainWindow()
    }}
    Start-Sleep -Milliseconds 1500
    $stillRunning = @($closeable | Where-Object {{ Get-Process -Id $_.Id -ErrorAction SilentlyContinue }})
    if ($stillRunning.Count -gt 0) {{
        @{{ success = $false; error = 'The application did not close normally. Request a force close to terminate it.' }} | ConvertTo-Json -Compress
        exit
    }}
}}
$remaining = @(Get-Process -Name $pattern -ErrorAction SilentlyContinue | Where-Object {{
    $protectedNames -notcontains $_.ProcessName.ToLowerInvariant() -and
    $_.Id -ne $currentCosmosPid -and
    $_.Id -ne $currentPowerShellPid
}})
if ($remaining.Count -gt 0) {{
    @{{ success = $false; error = 'One or more matching processes are still running.' }} | ConvertTo-Json -Compress
}} else {{
    @{{ success = $true; message = '' }} | ConvertTo-Json -Compress
}}
"""
    return _run_powershell(script)
