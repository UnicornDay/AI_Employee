@echo off
setlocal
cd /d "%~dp0"
echo Registering Quant_Daily_Technical_Analyst with Windows Task Scheduler...
powershell -ExecutionPolicy Bypass -File "%~dp0register_quant_task.ps1"
pause
