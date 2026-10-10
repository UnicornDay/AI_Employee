@echo off
setlocal
schtasks /delete /tn "CSL_Daily_News_Briefing" /f
echo.
echo =========================================================================
echo Daily news briefing task has been stopped and removed.
echo =========================================================================
pause
