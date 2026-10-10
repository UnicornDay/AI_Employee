#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Employee: Kai - Autonomous Quantitative & Fundamental Equity Analyst
-----------------------------------------------------------------------
Role:
1. Executes RSI and Bollinger Bands skills daily (Mon-Fri) for ASX portfolio:
   TLX.AX, COH.AX, SUN.AX, CSL.AX.
2. Every Thursday at 5:00 PM: Combines daily technical indicators with the
   buffett-analyzer skill to generate a comprehensive Holistic Equity Report.
3. Maintains a rolling 4-week activity log to prevent unbounded file growth.
4. Operates 100% zero-touch and headless via pythonw.exe.
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, timedelta

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "quant_employee_activity.log")
REPORT_DAILY_MD = os.path.join(BASE_DIR, "quant_daily_report.md")
REPORT_DAILY_TXT = os.path.join(BASE_DIR, "quant_daily_report.txt")
REPORT_HOLISTIC_MD = os.path.join(BASE_DIR, "weekly_holistic_equity_report.md")
REPORT_HOLISTIC_TXT = os.path.join(BASE_DIR, "weekly_holistic_equity_report.txt")

# Skill Script Paths (bundled tools directory takes priority for portability)
LOCAL_TOOLS_DIR = os.path.join(BASE_DIR, "tools")
RSI_SCRIPT = os.path.join(LOCAL_TOOLS_DIR, "rsi_backtest.py")
if not os.path.exists(RSI_SCRIPT):
    RSI_SCRIPT = os.path.expanduser(r"~/.gemini/config/skills/rsi/scripts/rsi_backtest.py")

BB_SCRIPT = os.path.join(LOCAL_TOOLS_DIR, "bbands_backtest.py")
if not os.path.exists(BB_SCRIPT):
    BB_SCRIPT = os.path.expanduser(r"~/.gemini/config/skills/bb/scripts/bbands_backtest.py")

BUFFETT_SCRIPT = os.path.join(LOCAL_TOOLS_DIR, "buffett_analyzer.py")
if not os.path.exists(BUFFETT_SCRIPT):
    BUFFETT_SCRIPT = os.path.expanduser(r"~/.gemini/config/skills/buffett-analyzer\scripts\buffett_analyzer.py")

DEFAULT_TICKERS = ["TLX.AX", "COH.AX", "SUN.AX", "CSL.AX"]
DEFAULT_PERIOD = "5y"
LOG_RETENTION_DAYS = 28  # 4 weeks rolling retention


def prune_rolling_log(log_path: str, days: int = LOG_RETENTION_DAYS):
    """Retain only the last 4 weeks of log entries to control file size."""
    if not os.path.exists(log_path):
        return
    cutoff = datetime.now() - timedelta(days=days)
    retained_lines = []
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("[") and len(line) >= 21 and line[20] == "]":
                    try:
                        ts = datetime.strptime(line[1:20], "%Y-%m-%d %H:%M:%S")
                        if ts >= cutoff:
                            retained_lines.append(line)
                    except ValueError:
                        retained_lines.append(line)
                else:
                    retained_lines.append(line)
        with open(log_path, "w", encoding="utf-8") as f:
            f.writelines(retained_lines)
    except Exception as e:
        print(f"Log pruning warning: {e}", file=sys.stderr)


def log(msg: str):
    """Log timestamped message to activity log and stdout, maintaining 4-week window."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{now_str}] [Kai-QuantEmployee] {msg}"
    print(formatted)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception as e:
        print(f"Failed to write to log: {e}", file=sys.stderr)


def run_technical_skill(script_path: str, ticker: str, period: str, chart_path: str) -> dict:
    """Execute RSI or BB skill via subprocess and extract metrics."""
    cmd = [
        sys.executable,
        script_path,
        "--ticker", ticker,
        "--period", period,
        "--save-chart", chart_path,
        "--no-show"
    ]
    
    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = subprocess.CREATE_NO_WINDOW

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
        creationflags=creation_flags
    )
    
    output = result.stdout
    err = result.stderr
    
    if result.returncode != 0:
        log(f"ERROR executing {os.path.basename(script_path)} for {ticker}: {err}")
        return {"success": False, "error": err, "raw_output": output}

    metrics = {
        "success": True,
        "raw_output": output,
        "chart_path": chart_path,
        "trades": "N/A",
        "strategy_return": "N/A",
        "bh_return": "N/A",
        "max_dd": "N/A",
        "sharpe": "N/A",
        "final_equity": "N/A",
        "period_str": "N/A",
        "current_position": "Cash",
        "last_price": "N/A",
        "last_indicator_val": "N/A"
    }

    for line in output.splitlines():
        line_clean = line.strip()
        if line_clean.startswith("Period:"):
            metrics["period_str"] = line_clean.replace("Period:", "").strip()
        elif line_clean.startswith("Trades:"):
            metrics["trades"] = line_clean.replace("Trades:", "").strip()
        elif line_clean.startswith("Strategy return:"):
            metrics["strategy_return"] = line_clean.replace("Strategy return:", "").strip()
        elif line_clean.startswith("Buy & hold return:"):
            metrics["bh_return"] = line_clean.replace("Buy & hold return:", "").strip()
        elif line_clean.startswith("Max drawdown:"):
            metrics["max_dd"] = line_clean.replace("Max drawdown:", "").strip()
        elif line_clean.startswith("Sharpe Ratio:"):
            metrics["sharpe"] = line_clean.replace("Sharpe Ratio:", "").strip()
        elif line_clean.startswith("Final equity:"):
            metrics["final_equity"] = line_clean.replace("Final equity:", "").strip()

    if "Transaction log:" in output:
        tx_lines = [l for l in output.split("Transaction log:")[-1].strip().splitlines() if l.strip()]
        if len(tx_lines) > 1:
            last_line = tx_lines[-1]
            parts = last_line.split()
            if len(parts) >= 4:
                metrics["last_price"] = parts[2]
                metrics["last_indicator_val"] = parts[3]
            if "BUY" in last_line:
                metrics["current_position"] = "Long (Holding)"
            elif "SELL" in last_line:
                metrics["current_position"] = "Cash"

    return metrics


def run_buffett_analyzer(tickers: list) -> list:
    """Execute buffett-analyzer skill to extract fundamental moat metrics."""
    cmd = [
        sys.executable,
        BUFFETT_SCRIPT,
        "--tickers"
    ] + tickers + ["--json"]

    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = subprocess.CREATE_NO_WINDOW

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
        creationflags=creation_flags
    )

    if result.returncode != 0:
        log(f"ERROR executing buffett-analyzer: {result.stderr}")
        return []

    try:
        return json.loads(result.stdout)
    except Exception as e:
        log(f"Failed to parse buffett-analyzer JSON: {e}")
        return []


def generate_holistic_equity_report(technical_data: dict, fundamental_data: list, period: str):
    """Generate weekly holistic report combining technical timing and fundamental quality."""
    now = datetime.now()
    fund_map = {f["ticker"]: f for f in fundamental_data if "ticker" in f}

    lines = []
    lines.append("# Weekly Holistic Equity Intelligence Report")
    lines.append(f"**Autonomous AI Employee**: Kai (Quantitative Technical & Fundamental Analyst)  ")
    lines.append(f"**Execution Timestamp**: {now.strftime('%Y-%m-%d %H:%M:%S')} (Thursday Executive Close)  ")
    lines.append(f"**Coverage Universe**: ASX Core Holdings ({', '.join(DEFAULT_TICKERS)})  ")
    lines.append(f"**Workspace**: `{BASE_DIR}`  ")
    lines.append("\n---\n")

    lines.append("## 1. Executive Summary & Holistic Strategic Matrix\n")
    lines.append("This report synthesizes **14-period RSI momentum**, **20-day Bollinger Bands volatility**, and **Warren Buffett Fundamental Moat analysis** into a unified strategic stance.\n")

    lines.append("| Ticker | Company | Current Price | RSI (14) Stance | BBands Stance | Buffett Moat Score | Holistic Weekly Verdict |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :---: | :--- |")

    for ticker, tech in technical_data.items():
        fund = fund_map.get(ticker, {})
        comp_name = fund.get("company_name", ticker)
        price = f"${fund.get('current_price', 0):.2f}" if fund.get("current_price") else "N/A"
        rsi_stance = tech["RSI"].get("current_position", "N/A")
        bb_stance = tech["BB"].get("current_position", "N/A")
        b_score = f"**{fund.get('buffett_score', 'N/A')}/8**"
        score_num = fund.get("buffett_score", 0)

        # Formulate holistic verdict
        if score_num >= 6:
            if "Long" in rsi_stance or "Long" in bb_stance:
                verdict = "**Strong Buy / Accumulate** (Wide Moat + Favorable Entry)"
            else:
                verdict = "**Core Quality Hold** (Moat Intact, Cash for Dips)"
        elif score_num >= 4:
            if "Long" in rsi_stance:
                verdict = "**Tactical Swing Buy** (Cyclical Moat + Technical Entry)"
            else:
                verdict = "**Neutral / Watch** (Fair Value, Neutral Technicals)"
        else:
            if "Long" in rsi_stance:
                verdict = "**Speculative Momentum** (High Risk, Technical Only)"
            else:
                verdict = "**Avoid / Underperform** (Weak Moat, Stretched Metrics)"

        lines.append(f"| **{ticker}** | {comp_name} | {price} | `{rsi_stance}` | `{bb_stance}` | {b_score} | {verdict} |")

    lines.append("\n---\n")

    lines.append("## 2. Fundamental Moat Analysis (Buffett Criteria)\n")
    lines.append("| Ticker | P/E (Fwd) | ROE | Op Margin | Debt/Eq | Free Cash Flow | Div Yield | Grade |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for ticker in technical_data.keys():
        f = fund_map.get(ticker, {})
        if not f:
            continue
        pe = f"{f.get('forward_pe', 0):.1f}x" if f.get('forward_pe') else "N/A"
        roe = f"{f.get('roe', 0):.1%}" if f.get('roe') is not None else "N/A"
        op_m = f"{f.get('operating_margin', 0):.1%}" if f.get('operating_margin') is not None else "N/A"
        de = f"{f.get('debt_to_equity', 0):.2f}" if f.get('debt_to_equity') is not None else "N/A"
        fcf = f"${f.get('free_cashflow', 0)/1e6:,.0f}M" if f.get('free_cashflow') is not None else "N/A"
        div = f"{f.get('dividend_yield', 0):.2%}" if f.get('dividend_yield') is not None else "0.0%"
        grade = f.get('grade', 'N/A')
        lines.append(f"| **{ticker}** | {pe} | {roe} | {op_m} | {de} | {fcf} | {div} | {grade} |")

    lines.append("\n---\n")

    lines.append("## 3. Detailed Asset Breakdown & Technical Validation\n")
    for ticker, tech in technical_data.items():
        f = fund_map.get(ticker, {})
        lines.append(f"### {ticker} — {f.get('company_name', ticker)}")
        lines.append(f"- **Fundamental Moat Grade**: {f.get('grade', 'N/A')} (Score: {f.get('buffett_score', 'N/A')}/8)")
        lines.append(f"- **RSI (14-Period) Return**: {tech['RSI'].get('strategy_return')} | **Max Drawdown**: {tech['RSI'].get('max_dd')} | **Stance**: `{tech['RSI'].get('current_position')}`")
        lines.append(f"- **Bollinger Bands Return**: {tech['BB'].get('strategy_return')} | **Sharpe Ratio**: {tech['BB'].get('sharpe')} | **Stance**: `{tech['BB'].get('current_position')}`")
        
        rsi_uri = f"file:///{tech['RSI']['chart_path'].replace(os.sep, '/')}"
        bb_uri = f"file:///{tech['BB']['chart_path'].replace(os.sep, '/')}"
        lines.append(f"- **Charts**: [RSI Chart]({rsi_uri}) | [Bollinger Bands Chart]({bb_uri})\n")

    lines.append("---\n*Report generated autonomously by AI Employee Kai. Next scheduled holistic synthesis: Next Thursday at 17:00.*")

    content = "\n".join(lines)
    with open(REPORT_HOLISTIC_MD, "w", encoding="utf-8") as f:
        f.write(content)
    with open(REPORT_HOLISTIC_TXT, "w", encoding="utf-8") as f:
        f.write(content)

    log(f"Successfully generated Weekly Holistic Equity Report: {REPORT_HOLISTIC_MD}")


def execute_routine(tickers: list, period: str, force: bool = False, force_thursday: bool = False):
    """Execute Kai's daily technical routine and conditional Thursday holistic report."""
    now = datetime.now()
    weekday = now.weekday()  # Monday=0, Sunday=6, Thursday=3
    day_name = now.strftime("%A")
    is_thursday = (weekday == 3) or force_thursday

    log(f"=== Starting Routine. Day: {day_name}, Date: {now.strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    # Prune rolling log to 4 weeks
    prune_rolling_log(LOG_FILE, LOG_RETENTION_DAYS)
    log(f"Pruned activity log: Retaining only the last {LOG_RETENTION_DAYS} days (4 weeks) of entries.")

    # Monday-Friday calendar enforcement
    if weekday >= 5 and not force:
        log(f"Today is {day_name} (Weekend). Financial markets are closed. Skipping execution.")
        return

    # 1. Run Daily Technical Skills (RSI + BBands)
    technical_results = {}
    report_sections = [
        f"# Daily Quantitative Intelligence Briefing\n",
        f"**Autonomous AI Employee**: Kai (Quantitative Technical Analyst)  ",
        f"**Execution Timestamp**: {now.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Cadence**: Monday - Friday Daily Market Cycle  ",
        f"**Watchlist**: {', '.join(tickers)}  ",
        f"**Workspace**: `{BASE_DIR}`\n",
        "---\n"
    ]

    for ticker in tickers:
        clean_name = ticker.replace(".", "_").lower()
        log(f"--> Analyzing asset: {ticker}")
        technical_results[ticker] = {}

        # RSI Skill
        rsi_chart = os.path.join(BASE_DIR, f"{clean_name}_rsi.png")
        rsi_res = run_technical_skill(RSI_SCRIPT, ticker, period, rsi_chart)
        technical_results[ticker]["RSI"] = rsi_res
        log(f"[{ticker}] RSI Completed. Return: {rsi_res.get('strategy_return')}, Position: {rsi_res.get('current_position')}")

        # BBands Skill
        bb_chart = os.path.join(BASE_DIR, f"{clean_name}_bb.png")
        bb_res = run_technical_skill(BB_SCRIPT, ticker, period, bb_chart)
        technical_results[ticker]["BB"] = bb_res
        log(f"[{ticker}] BB Completed. Return: {bb_res.get('strategy_return')}, Sharpe: {bb_res.get('sharpe')}, Position: {bb_res.get('current_position')}")

        # Append to Daily Technical Report
        report_sections.append(f"## {ticker} Technical Analysis ({period.upper()})\n")
        report_sections.append("| Metric | 14-Period RSI Strategy | 20-Day Bollinger Bands Strategy | Buy & Hold Benchmark |")
        report_sections.append("| :--- | :--- | :--- | :--- |")
        report_sections.append(f"| **Strategy Return** | **{rsi_res.get('strategy_return')}** | **{bb_res.get('strategy_return')}** | {rsi_res.get('bh_return')} |")
        report_sections.append(f"| **Final Equity ($10k)** | **{rsi_res.get('final_equity')}** | **{bb_res.get('final_equity')}** | — |")
        report_sections.append(f"| **Max Drawdown** | {rsi_res.get('max_dd')} | {bb_res.get('max_dd')} | — |")
        report_sections.append(f"| **Sharpe Ratio** | N/A | **{bb_res.get('sharpe')}** | — |")
        report_sections.append(f"| **Trades Triggered** | {rsi_res.get('trades')} | {bb_res.get('trades')} | 1 |")
        report_sections.append(f"| **Current Stance** | `{rsi_res.get('current_position')}` | `{bb_res.get('current_position')}` | Holding |")
        report_sections.append("")

        rsi_uri = f"file:///{rsi_chart.replace(os.sep, '/')}"
        bb_uri = f"file:///{bb_chart.replace(os.sep, '/')}"
        report_sections.append(f"### Visual Charts Generated")
        report_sections.append(f"- **RSI Indicator**: [{os.path.basename(rsi_chart)}]({rsi_uri})")
        report_sections.append(f"- **Bollinger Bands**: [{os.path.basename(bb_chart)}]({bb_uri})\n")
        report_sections.append("---\n")

    # Save daily technical report
    daily_content = "\n".join(report_sections)
    with open(REPORT_DAILY_MD, "w", encoding="utf-8") as f:
        f.write(daily_content)
    with open(REPORT_DAILY_TXT, "w", encoding="utf-8") as f:
        f.write(daily_content)
    log(f"Daily technical briefing saved to {REPORT_DAILY_MD}")

    # 2. Thursday Holistic Synthesis (Technical + Buffett-Analyzer)
    if is_thursday:
        log("Thursday schedule detected! Invoking buffett-analyzer skill for holistic equity synthesis...")
        fundamental_results = run_buffett_analyzer(tickers)
        if fundamental_results:
            generate_holistic_equity_report(technical_results, fundamental_results, period)
        else:
            log("WARNING: buffett-analyzer did not return data; skipping holistic synthesis.")
    else:
        log(f"Today is {day_name}. Weekly holistic synthesis scheduled for Thursday.")

    # Final prune
    prune_rolling_log(LOG_FILE, LOG_RETENTION_DAYS)
    log("Routine completed successfully. Standing by for next trigger.")


def main():
    parser = argparse.ArgumentParser(description="AI Employee Kai: Quantitative & Fundamental Analyst")
    parser.add_argument("--tickers", nargs="+", default=DEFAULT_TICKERS, help="Watchlist tickers (default: TLX.AX COH.AX SUN.AX CSL.AX)")
    parser.add_argument("--period", default=DEFAULT_PERIOD, help="Lookback period (default: 5y)")
    parser.add_argument("--force", action="store_true", help="Force execution even on weekends")
    parser.add_argument("--weekly", action="store_true", help="Force execution of Thursday weekly holistic report")

    args = parser.parse_args()
    execute_routine(tickers=args.tickers, period=args.period, force=args.force, force_thursday=args.weekly)


if __name__ == "__main__":
    main()
