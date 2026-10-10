@echo off
setlocal
cd /d "%~dp0"

echo =========================================================================
echo Asking Rowan to scan the market, hunt opportunities, test, and write...
echo =========================================================================
echo.

py writer_employee.py --run-now

echo.
echo =========================================================================
echo Done! Review queue generated at: REVIEW_QUEUE.md
echo Full draft saved to: latest_medium_draft.md (and drafts/ archive)
echo =========================================================================
pause
