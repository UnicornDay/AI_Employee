@echo off
echo Unregistering Quant_Daily_Technical_Analyst task...
powershell -Command "Unregister-ScheduledTask -TaskName 'Quant_Daily_Technical_Analyst' -Confirm:$false -ErrorAction SilentlyContinue; Write-Host '[OK] Task Quant_Daily_Technical_Analyst successfully removed.'"
pause
