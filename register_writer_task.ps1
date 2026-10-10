# PowerShell script to register Rowan_Daily_Medium_Writer in Windows Task Scheduler
# Executes writer_employee.py headlessly with pythonw.exe every morning at 07:00 AM.

$workingDir = $PSScriptRoot
$scriptPath = Join-Path $workingDir "writer_employee.py"

$pythonwCandidates = @(
    "$env:LOCALAPPDATA\Programs\Python\Python313\pythonw.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\pythonw.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\pythonw.exe"
)
$pythonwExe = "pythonw.exe"
foreach ($cand in $pythonwCandidates) {
    if (Test-Path $cand) { $pythonwExe = $cand; break }
}

$action = New-ScheduledTaskAction -Execute $pythonwExe -Argument "`"$scriptPath`"" -WorkingDirectory $workingDir
$trigger = New-ScheduledTaskTrigger -Daily -At "07:00"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "Rowan_Daily_Medium_Writer" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "=========================================================================="
Write-Host " [OK] Task 'Rowan_Daily_Medium_Writer' successfully registered!"
Write-Host " Cadence: Daily every morning at 07:00 AM (Zero-touch, headless pythonw.exe)"
Write-Host " Target Script: $scriptPath"
Write-Host " Working Directory: $workingDir"
Write-Host " Output: drafts/ and latest_medium_draft.md"
Write-Host "=========================================================================="
