@echo off
setlocal
cd /d "%~dp0"
echo ==========================================================
echo Starting On-Demand Quantitative Employee Run (Kai)
echo Watchlist: TLX.AX, COH.AX, SUN.AX, CSL.AX
echo ==========================================================
py "%~dp0quant_employee.py" --tickers TLX.AX COH.AX SUN.AX CSL.AX --period 5y --force
echo ==========================================================
echo Finished! Check quant_daily_report.md and activity logs.
echo ==========================================================
pause
