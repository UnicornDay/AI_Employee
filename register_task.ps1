$workingDir = $PSScriptRoot
$scriptPath = Join-Path $workingDir "ai_employee.py"

$pythonwCandidates = @(
    "$env:LOCALAPPDATA\Programs\Python\Python313\pythonw.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\pythonw.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\pythonw.exe"
)
$pythonExe = "pythonw.exe"
foreach ($cand in $pythonwCandidates) {
    if (Test-Path $cand) { $pythonExe = $cand; break }
}

$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "$scriptPath --once"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "CSL_Auto_Price_Logger" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "Task CSL_Auto_Price_Logger successfully registered to run every 30 minutes for 10 years!"
