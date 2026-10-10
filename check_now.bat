@echo off
setlocal
cd /d "%~dp0"

echo ==========================================================
echo Asking Ava to check CSL.AX price right now...
echo ==========================================================

py ai_employee.py --once

echo.
echo ==========================================================
echo Check completed! Recorded in CSL_AX_prices.csv and employee_activity.log
echo ==========================================================
pause
