@echo off
setlocal
cd /d "%~dp0"

echo ==========================================================
echo Registering AI Employee (Ava) into Windows Task Scheduler
echo ==========================================================
echo This will configure Windows to execute Ava every 30 minutes,
echo even if your PC restarts, without you needing to do anything.
echo.

schtasks /create /tn "Ava_CSL_Stock_Monitor" /tr "py.exe \"%~dp0ai_employee.py\" --once" /sc minute /mo 30 /f

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] Windows Task 'Ava_CSL_Stock_Monitor' created successfully!
    echo Ava will trigger every 30 minutes in the background.
    echo You can view the scheduled task in Windows Task Scheduler.
) else (
    echo.
    echo [ERROR] Failed to register scheduled task. If prompted, please run as Administrator.
)

echo ==========================================================
pause
