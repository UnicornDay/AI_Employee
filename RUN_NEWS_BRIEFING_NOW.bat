@echo off
setlocal
cd /d "%~dp0"

echo =========================================================================
echo Asking Ava to read today's financial news and generate a CSL.AX briefing...
echo =========================================================================
echo.

py daily_news_summary.py

echo.
echo =========================================================================
echo Done! Briefing saved to csl_daily_briefing.txt and csl_daily_briefing.md
echo =========================================================================
pause
