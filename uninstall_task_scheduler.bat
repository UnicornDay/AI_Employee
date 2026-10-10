@echo off
setlocal

echo ==========================================================
echo Removing AI Employee (Ava) from Windows Task Scheduler
echo ==========================================================

schtasks /delete /tn "Ava_CSL_Stock_Monitor" /f

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] Scheduled task 'Ava_CSL_Stock_Monitor' successfully removed.
) else (
    echo.
    echo [INFO] Task not found or already removed.
)

echo ==========================================================
pause
