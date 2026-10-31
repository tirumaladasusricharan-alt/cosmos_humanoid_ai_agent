param (
    [string]$Target = "+917780538869"
)

# ── 1. Native C# Utilities for Window Management & Mouse Clicking ────────────
$nativeCode = @"
using System;
using System.Runtime.InteropServices;

public class PhoneLinkHelper {
    [DllImport("user32.dll")]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    [DllImport("user32.dll")]
    public static extern bool SetCursorPos(int X, int Y);

    [DllImport("user32.dll")]
    public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);

    public const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
    public const uint MOUSEEVENTF_LEFTUP   = 0x0004;

    public static void ClickAt(int x, int y) {
        SetCursorPos(x, y);
        System.Threading.Thread.Sleep(80);
        mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, UIntPtr.Zero);
        System.Threading.Thread.Sleep(80);
        mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, UIntPtr.Zero);
    }

    public static void HoverAt(int x, int y) {
        SetCursorPos(x, y);
        System.Threading.Thread.Sleep(120);
    }
}
"@
Add-Type -TypeDefinition $nativeCode

# ── 2. Minimize COSMOS Overlay so Phone Link gets full screen & focus ────────
try {
    $cosmosHwnd = [PhoneLinkHelper]::FindWindow($null, "COSMOS_OVERLAY_ROOT")
    if ($cosmosHwnd -and $cosmosHwnd -ne [IntPtr]::Zero) {
        [PhoneLinkHelper]::SetWindowPos($cosmosHwnd, [IntPtr](-2), 0, 0, 0, 0, 0x0001 -bor 0x0002)
        [PhoneLinkHelper]::ShowWindow($cosmosHwnd, 6) # SW_MINIMIZE
    }
} catch {}

# ── 3. Parse Target ─────────────────────────────────────────────────────────
$cleanDigits = $Target -replace '[^\d]', ''
$isPhoneNumber = ($cleanDigits.Length -ge 7) -and (($Target -replace '[\d\s\-\+\(\)]', '').Length -eq 0)

# If Target is Boss's name, treat digits as Boss's phone number too
if ($Target -like "*charan*" -or $Target -like "*boss*" -or $Target -eq "my phone" -or $Target -eq "me") {
    $cleanDigits = "7780538869"
    $isPhoneNumber = $true
}

# Launch Phone Link
Start-Process "ms-phone:"
Start-Sleep -Milliseconds 800

$wshell = New-Object -ComObject WScript.Shell
$null = $wshell.AppActivate("Phone Link")
Start-Sleep -Milliseconds 400

# ── 4. Load UI Automation Assemblies ─────────────────────────────────────────
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms

# ── 5. Primary Action: Dial Number OR Search Contact ─────────────────────────
$callTriggered = $false
$sw = [System.Diagnostics.Stopwatch]::StartNew()

while ($sw.ElapsedMilliseconds -lt 9000 -and -not $callTriggered) {
    # Check if "Call on PC" dialog is already active
    $callDialog = [PhoneLinkHelper]::FindWindow($null, "Call on PC")
    if ($callDialog -and $callDialog -ne [IntPtr]::Zero) {
        Write-Host "[COSMOS] 'Call on PC' popup active and calling '$Target'!"
        $callTriggered = $true
        break
    }

    $null = $wshell.AppActivate("Phone Link")
    Start-Sleep -Milliseconds 300

    # ── PATH A: Phone Number Dialing ─────────────────────────────────────────
    if ($isPhoneNumber) {
        # Type the digits into the dialpad
        Write-Host "[COSMOS] Typing digits $cleanDigits into Phone Link dialer..."
        $wshell.SendKeys($cleanDigits)
        Start-Sleep -Milliseconds 400
        $wshell.SendKeys("{ENTER}")
        Start-Sleep -Milliseconds 500

        # Check if Call on PC appeared
        $callDialog = [PhoneLinkHelper]::FindWindow($null, "Call on PC")
        if ($callDialog -and $callDialog -ne [IntPtr]::Zero) {
            $callTriggered = $true
            break
        }
    }

    # ── PATH B: Contact Name Search & Click ──────────────────────────────────
    # Focus the Search contacts box via Ctrl+E
    $wshell.SendKeys("^e")
    Start-Sleep -Milliseconds 200
    $wshell.SendKeys("^a")
    Start-Sleep -Milliseconds 100

    $searchTerm = if ($isPhoneNumber) { $cleanDigits } else { $Target }
    $wshell.SendKeys($searchTerm)
    Start-Sleep -Milliseconds 450
    $wshell.SendKeys("{DOWN}")
    Start-Sleep -Milliseconds 150
    $wshell.SendKeys("{ENTER}")
    Start-Sleep -Milliseconds 400

    $callDialog = [PhoneLinkHelper]::FindWindow($null, "Call on PC")
    if ($callDialog -and $callDialog -ne [IntPtr]::Zero) {
        $callTriggered = $true
        break
    }

    # ── PATH C: UI Automation Contact Row & Call Button Click ────────────────
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $allApps = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
    $phoneApp = $null

    foreach ($app in $allApps) {
        $n = $app.Current.Name
        $c = $app.Current.ClassName
        if ($n -like "*Phone Link*" -or $n -like "*Your Phone*" -or ($c -eq "ApplicationFrameWindow" -and $n -like "*Phone*")) {
            $phoneApp = $app
            break
        }
    }

    if ($phoneApp) {
        # Search all buttons in Phone Link for any Call button
        $allBtns = $phoneApp.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Button
        )))

        foreach ($b in $allBtns) {
            $bn = $b.Current.Name
            $bi = $b.Current.AutomationId
            if (($bn -eq "Call" -or $bn -like "Call *" -or $bi -like "*call*" -or $bi -like "*dial*") -and ($bn -notlike "*End*" -and $bn -notlike "*Cancel*")) {
                try {
                    $inv = $b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
                    if ($inv) {
                        $inv.Invoke()
                        $callTriggered = $true
                        Write-Host "[COSMOS] Triggered Call button: $bn"
                        break
                    }
                } catch {}

                $bRect = $b.Current.BoundingRectangle
                if ($bRect -and $bRect.Width -gt 0) {
                    [PhoneLinkHelper]::ClickAt([int]($bRect.X + $bRect.Width/2), [int]($bRect.Y + $bRect.Height/2))
                    $callTriggered = $true
                    Write-Host "[COSMOS] Clicked Call button coordinate ($($bRect.X), $($bRect.Y))"
                    break
                }
            }
        }
    }

    Start-Sleep -Milliseconds 400
}

Write-Host "[COSMOS] Call sequence completed for '$Target'. Triggered: $callTriggered"
