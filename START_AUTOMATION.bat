@echo off
setlocal
cd /d "%~dp0"

echo =========================================================================
echo Setting up Automatic CSL.AX Stock Price Logging (Every 30 Minutes)
echo =========================================================================
echo.

set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe
if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=pythonw.exe
)

:: Create scheduled task that runs completely invisibly every 30 minutes
schtasks /create /tn "CSL_Auto_Price_Logger" /tr "\"%PYTHON_EXE%\" \"%~dp0ai_employee.py\" --once" /sc minute /mo 30 /f

echo.
echo Performing initial check right now...
"%PYTHON_EXE%" "%~dp0ai_employee.py" --once

echo.
echo =========================================================================
echo ALL DONE! AUTOMATION IS ACTIVE.
echo.
echo - Windows will run this automatically every 30 minutes in the background.
echo - You DO NOT need to keep any window open.
echo - You DO NOT need to touch your screen.
echo - Your prices are saved directly in: csl_price_log.txt
echo =========================================================================
echo.
pause
