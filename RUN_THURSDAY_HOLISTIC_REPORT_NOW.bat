@echo off
setlocal
cd /d "%~dp0"
echo ==========================================================
echo Starting Thursday Holistic Equity Synthesis (Kai)
echo Technicals (RSI + BBands) + Fundamentals (Buffett-Analyzer)
echo Watchlist: TLX.AX, COH.AX, SUN.AX, CSL.AX
echo ==========================================================
py "%~dp0quant_employee.py" --tickers TLX.AX COH.AX SUN.AX CSL.AX --period 5y --weekly --force
echo ==========================================================
echo Finished! Check weekly_holistic_equity_report.md
echo ==========================================================
pause
