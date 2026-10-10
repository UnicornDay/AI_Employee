#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Buffett Fundamental Analyzer Skill
----------------------------------
Evaluates equities through the lens of Warren Buffett's value investing criteria:
- Economic Moat & Pricing Power (ROE, Operating Margin, Profit Margin)
- Balance Sheet Strength (Debt-to-Equity, Liquidity)
- Cash Generation (Free Cash Flow)
- Valuation Discipline (P/E, P/B, EV/EBITDA, Dividend Yield)
"""

import sys
import json
import argparse
import yfinance as yf
import pandas as pd
import numpy as np

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def analyze_stock(ticker: str) -> dict:
    """Analyze a single stock against Warren Buffett fundamental criteria."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}

    # Extract metrics safely
    company_name = info.get("shortName") or info.get("longName") or ticker
    current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
    market_cap = info.get("marketCap")
    
    trailing_pe = info.get("trailingPE")
    forward_pe = info.get("forwardPE")
    price_to_book = info.get("priceToBook")
    ev_to_ebitda = info.get("enterpriseToEbitda")
    
    roe = info.get("returnOnEquity")
    roa = info.get("returnOnAssets")
    operating_margin = info.get("operatingMargins")
    profit_margin = info.get("profitMargins")
    
    debt_to_equity = info.get("debtToEquity")
    if debt_to_equity is not None and debt_to_equity > 10:  # yfinance often reports as percentage e.g. 85 for 0.85
        debt_to_equity = debt_to_equity / 100.0

    current_ratio = info.get("currentRatio")
    quick_ratio = info.get("quickRatio")
    
    free_cashflow = info.get("freeCashflow")
    operating_cashflow = info.get("operatingCashflow")
    
    dividend_yield = info.get("dividendYield")
    if dividend_yield is not None and dividend_yield > 1.0:
        dividend_yield = dividend_yield / 100.0
    payout_ratio = info.get("payoutRatio")

    # Score against Buffett Pillars (Max 8 points)
    score = 0
    checks = []

    # 1. High ROE (> 15%)
    if roe is not None and roe >= 0.15:
        score += 1
        checks.append(("ROE >= 15%", True, f"{roe:.1%}"))
    else:
        checks.append(("ROE >= 15%", False, f"{roe:.1%}" if roe is not None else "N/A"))

    # 2. Strong Operating Margin (> 15%)
    if operating_margin is not None and operating_margin >= 0.15:
        score += 1
        checks.append(("Operating Margin >= 15%", True, f"{operating_margin:.1%}"))
    else:
        checks.append(("Operating Margin >= 15%", False, f"{operating_margin:.1%}" if operating_margin is not None else "N/A"))

    # 3. Solid Net Profit Margin (> 10%)
    if profit_margin is not None and profit_margin >= 0.10:
        score += 1
        checks.append(("Profit Margin >= 10%", True, f"{profit_margin:.1%}"))
    else:
        checks.append(("Profit Margin >= 10%", False, f"{profit_margin:.1%}" if profit_margin is not None else "N/A"))

    # 4. Conservative Debt/Equity (<= 0.8)
    if debt_to_equity is not None and debt_to_equity <= 0.80:
        score += 1
        checks.append(("Debt/Equity <= 0.80", True, f"{debt_to_equity:.2f}"))
    else:
        checks.append(("Debt/Equity <= 0.80", False, f"{debt_to_equity:.2f}" if debt_to_equity is not None else "N/A"))

    # 5. Healthy Liquidity (Current Ratio >= 1.2)
    if current_ratio is not None and current_ratio >= 1.20:
        score += 1
        checks.append(("Current Ratio >= 1.20", True, f"{current_ratio:.2f}"))
    else:
        checks.append(("Current Ratio >= 1.20", False, f"{current_ratio:.2f}" if current_ratio is not None else "N/A"))

    # 6. Positive Free Cash Flow
    if free_cashflow is not None and free_cashflow > 0:
        score += 1
        checks.append(("Positive Free Cash Flow", True, f"${free_cashflow/1e6:,.1f}M"))
    else:
        checks.append(("Positive Free Cash Flow", False, f"${free_cashflow/1e6:,.1f}M" if free_cashflow is not None else "N/A"))

    # 7. Reasonable Valuation (Forward P/E <= 25 or Trailing P/E <= 25)
    pe_val = forward_pe or trailing_pe
    if pe_val is not None and pe_val <= 25 and pe_val > 0:
        score += 1
        checks.append(("Valuation (P/E <= 25)", True, f"{pe_val:.1f}x"))
    else:
        checks.append(("Valuation (P/E <= 25)", False, f"{pe_val:.1f}x" if pe_val is not None else "N/A"))

    # 8. Shareholder Return (Positive Dividend Yield with Payout < 80%)
    if dividend_yield is not None and dividend_yield > 0.015:
        if payout_ratio is None or payout_ratio <= 0.80:
            score += 1
            checks.append(("Sustainable Dividend Yield > 1.5%", True, f"{dividend_yield:.2%}"))
        else:
            checks.append(("Sustainable Dividend Yield > 1.5%", False, f"{dividend_yield:.2%} (High Payout)"))
    else:
        checks.append(("Sustainable Dividend Yield > 1.5%", False, f"{dividend_yield:.2%}" if dividend_yield is not None else "0%"))

    # Moat / Grade classification
    if score >= 7:
        grade = "A (Wide Moat / Prime Buffett Franchise)"
    elif score >= 5:
        grade = "B (Strong Quality Compounder)"
    elif score >= 3:
        grade = "C (Moderate Quality / Cyclical Moat)"
    else:
        grade = "D (Speculative / Stretched Financials)"

    return {
        "ticker": ticker,
        "company_name": company_name,
        "current_price": current_price,
        "market_cap": market_cap,
        "trailing_pe": trailing_pe,
        "forward_pe": forward_pe,
        "price_to_book": price_to_book,
        "ev_to_ebitda": ev_to_ebitda,
        "roe": roe,
        "roa": roa,
        "operating_margin": operating_margin,
        "profit_margin": profit_margin,
        "debt_to_equity": debt_to_equity,
        "current_ratio": current_ratio,
        "free_cashflow": free_cashflow,
        "dividend_yield": dividend_yield,
        "payout_ratio": payout_ratio,
        "buffett_score": score,
        "max_score": 8,
        "grade": grade,
        "checks": checks
    }


def format_report(results: list) -> str:
    """Format fundamental analysis results into clean Markdown table and summary."""
    lines = []
    lines.append("# Warren Buffett Fundamental Moat Analysis\n")
    lines.append("| Ticker | Company | Price | P/E (Fwd) | ROE | Op Margin | Debt/Eq | FCF | Div Yield | Buffett Score | Moat Grade |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |")

    for r in results:
        if "error" in r:
            lines.append(f"| {r['ticker']} | Error fetching data | — | — | — | — | — | — | — | 0/8 | Error |")
            continue
        
        price_str = f"${r['current_price']:.2f}" if r['current_price'] else "N/A"
        pe_str = f"{r['forward_pe']:.1f}x" if r['forward_pe'] else (f"{r['trailing_pe']:.1f}x" if r['trailing_pe'] else "N/A")
        roe_str = f"{r['roe']:.1%}" if r['roe'] is not None else "N/A"
        op_margin_str = f"{r['operating_margin']:.1%}" if r['operating_margin'] is not None else "N/A"
        de_str = f"{r['debt_to_equity']:.2f}" if r['debt_to_equity'] is not None else "N/A"
        fcf_str = f"${r['free_cashflow']/1e6:,.0f}M" if r['free_cashflow'] is not None else "N/A"
        div_str = f"{r['dividend_yield']:.2%}" if r['dividend_yield'] is not None else "0.0%"
        score_str = f"**{r['buffett_score']}/8**"
        grade_str = r['grade']

        lines.append(f"| **{r['ticker']}** | {r['company_name']} | {price_str} | {pe_str} | {roe_str} | {op_margin_str} | {de_str} | {fcf_str} | {div_str} | {score_str} | {grade_str} |")

    lines.append("\n### Detailed Buffett Checklist Breakdown\n")
    for r in results:
        if "error" in r:
            continue
        lines.append(f"#### {r['ticker']} — {r['company_name']} (Score: {r['buffett_score']}/8 - {r['grade']})")
        for name, passed, val in r['checks']:
            icon = "[PASS]" if passed else "[FAIL]"
            lines.append(f"- {icon} **{name}**: {val}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Buffett Fundamental Value Analyzer")
    parser.add_argument("--tickers", nargs="+", default=["TLX.AX", "COH.AX", "SUN.AX", "CSL.AX"], help="Tickers to evaluate")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    results = [analyze_stock(t) for t in args.tickers]

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        report = format_report(results)
        print(report)


if __name__ == "__main__":
    main()
