@echo off
echo =========================================================================
echo Unregistering Rowan_Daily_Medium_Writer task from Task Scheduler...
echo =========================================================================
echo.
powershell -Command "Unregister-ScheduledTask -TaskName 'Rowan_Daily_Medium_Writer' -Confirm:$false -ErrorAction SilentlyContinue; Write-Host '[OK] Task Rowan_Daily_Medium_Writer successfully removed.'"
echo.
pause
