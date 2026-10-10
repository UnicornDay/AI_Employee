@echo off
setlocal
cd /d "%~dp0"
echo =========================================================================
echo Registering Rowan_Daily_Medium_Writer with Windows Task Scheduler...
echo =========================================================================
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0register_writer_task.ps1"
echo.
pause
