@echo off
setlocal
schtasks /delete /tn "CSL_Auto_Price_Logger" /f
echo.
echo =========================================================================
echo Automatic CSL logging has been stopped.
echo =========================================================================
pause
