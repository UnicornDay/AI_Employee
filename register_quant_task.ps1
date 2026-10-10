# PowerShell script to register Quant_Daily_Technical_Analyst task in Windows Task Scheduler
# Executes quant_employee.py headlessly with pythonw.exe Monday through Friday at 17:00.

$workingDir = $PSScriptRoot
$scriptPath = Join-Path $workingDir "quant_employee.py"

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
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At "17:00"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "Quant_Daily_Technical_Analyst" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "=========================================================================="
Write-Host " [OK] Task 'Quant_Daily_Technical_Analyst' successfully registered!"
Write-Host " Cadence: Monday to Friday at 17:00 (Zero-touch, headless pythonw.exe)"
Write-Host " Workspace: $workingDir"
Write-Host "=========================================================================="
