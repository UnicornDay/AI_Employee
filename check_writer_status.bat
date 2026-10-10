@echo off
setlocal
cd /d "%~dp0"

echo =========================================================================
echo Rowan: Autonomous Market Opportunity Hunter and Investment Essayist
echo =========================================================================
echo.
powershell -Command "$task = Get-ScheduledTask -TaskName 'Rowan_Daily_Medium_Writer' -ErrorAction SilentlyContinue; if ($task) { $info = Get-ScheduledTaskInfo -TaskName 'Rowan_Daily_Medium_Writer'; Write-Host '[Status] Task is REGISTERED in Windows Task Scheduler'; Write-Host ('  State: ' + $task.State); Write-Host ('  Last Run: ' + $info.LastRunTime); Write-Host ('  Next Run: ' + $info.NextRunTime); Write-Host ('  Last Result: ' + $info.LastTaskResult); } else { Write-Host '[Status] Task is NOT currently registered in Task Scheduler.'; Write-Host '  Run START_WRITER_AUTOMATION.bat to enable the morning schedule.'; }"

echo.
echo -------------------------------------------------------------------------
echo Morning Review Queue (REVIEW_QUEUE.md):
echo -------------------------------------------------------------------------
if exist "REVIEW_QUEUE.md" (
    powershell -Command "Get-Content 'REVIEW_QUEUE.md' | Select-Object -First 30"
) else (
    echo No review queue generated yet. Run RUN_WRITER_NOW.bat to generate one now.
)

echo.
echo -------------------------------------------------------------------------
echo Recent Activity Log (Last 8 Lines):
echo -------------------------------------------------------------------------
if exist "writer_employee_activity.log" (
    powershell -Command "Get-Content 'writer_employee_activity.log' -Tail 8"
) else (
    echo No activity log found yet.
)

echo.
echo =========================================================================
echo Review full draft at: latest_medium_draft.md (or copy from latest_medium_draft.txt)
echo =========================================================================
pause
