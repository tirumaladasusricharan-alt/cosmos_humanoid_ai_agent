Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$root = [System.Windows.Automation.AutomationElement]::RootElement
$all = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)

Write-Host "Found $($all.Count) top level windows:"
foreach ($w in $all) {
    try {
        $n = $w.Current.Name
        $c = $w.Current.ClassName
        $procId = $w.Current.ProcessId
        if ($n -or $c) {
            Write-Host "PID: $procId | Cls: '$c' | Name: '$n'"
        }
    }
    catch {}
}

