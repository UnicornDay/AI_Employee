$workingDir = $PSScriptRoot
$scriptPath = Join-Path $workingDir "daily_news_summary.py"

$pythonwCandidates = @(
    "$env:LOCALAPPDATA\Programs\Python\Python313\pythonw.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\pythonw.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\pythonw.exe"
)
$pythonExe = "pythonw.exe"
foreach ($cand in $pythonwCandidates) {
    if (Test-Path $cand) { $pythonExe = $cand; break }
}

$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "$scriptPath"
$trigger = New-ScheduledTaskTrigger -Daily -At "16:30"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "CSL_Daily_News_Briefing" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "Task CSL_Daily_News_Briefing successfully registered to run daily at 16:30!"
