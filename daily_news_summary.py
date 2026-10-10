#!/usr/bin/env python3
"""
AI Employee: Ava - Daily Financial News & Market Intelligence Summarizer
-------------------------------------------------------------------------
Role: Autonomous financial analyst employee.
Task: Reads financial news feeds and market performance for CSL.AX (CSL Limited),
      synthesizes them using Gemini 3.6 Flash, and records a clean executive
      briefing into csl_daily_briefing.txt without requiring human interaction.
"""

import os
import sys
import json
import socket
from datetime import datetime, timezone
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

# Network timeouts
socket.setdefaulttimeout(30)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BRIEFING_TXT = os.path.join(BASE_DIR, "csl_daily_briefing.txt")
BRIEFING_MD = os.path.join(BASE_DIR, "csl_daily_briefing.md")

SYMBOL = "CSL.AX"
COMPANY = "CSL Limited"
RSS_URL = "https://news.google.com/rss/search?q=CSL+Limited+ASX+OR+CSL.AX&hl=en-AU&gl=AU&ceid=AU:en"
YAHOO_URL = f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?interval=1m&range=1d"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def fetch_latest_news(limit: int = 8) -> list:
    """Fetch top recent financial news articles for CSL.AX."""
    req = urllib.request.Request(RSS_URL, headers={"User-Agent": USER_AGENT})
    articles = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            root = ET.fromstring(resp.read().decode("utf-8", errors="replace"))
            items = root.findall(".//item")
            for item in items[:limit]:
                title_elem = item.find("title")
                pub_elem = item.find("pubDate")
                link_elem = item.find("link")
                title = title_elem.text if title_elem is not None else "Untitled"
                pub = pub_elem.text if pub_elem is not None else ""
                link = link_elem.text if link_elem is not None else ""
                articles.append({
                    "title": title,
                    "published": pub,
                    "link": link
                })
    except Exception as e:
        print(f"Warning: Could not fetch news RSS: {e}", file=sys.stderr)
    return articles


def fetch_stock_snapshot() -> dict:
    """Fetch day market snapshot from Yahoo Finance."""
    req = urllib.request.Request(YAHOO_URL, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            meta = data.get("chart", {}).get("result", [{}])[0].get("meta", {})
            price = meta.get("regularMarketPrice") or meta.get("fulldayPrice")
            prev_close = meta.get("previousClose") or meta.get("chartPreviousClose") or price
            change = round(price - prev_close, 2) if (price and prev_close) else 0.0
            change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0
            return {
                "price": price,
                "prev_close": prev_close,
                "change": change,
                "change_pct": change_pct,
                "day_high": meta.get("regularMarketDayHigh"),
                "day_low": meta.get("regularMarketDayLow"),
                "volume": meta.get("regularMarketVolume", 0)
            }
    except Exception as e:
        print(f"Warning: Could not fetch stock snapshot: {e}", file=sys.stderr)
        return {}


def generate_ai_briefing(news: list, stock: dict) -> str:
    """Use Gemini 3.6 Flash to synthesize news into an executive briefing."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable not found."

    # Format news items for prompt
    news_lines = []
    for a in news:
        news_lines.append(f"- {a['title']} ({a['published']})")
    news_context = "\n".join(news_lines) if news_lines else "No recent headlines found today."

    stock_context = "Market data unavailable."
    if stock.get("price"):
        stock_context = (
            f"Current Price: ${stock['price']:.2f} AUD | "
            f"Change: {stock['change']:+.2f} ({stock['change_pct']:+.2f}%) | "
            f"Day Range: [${stock.get('day_low', 0):.2f} - ${stock.get('day_high', 0):.2f}] | "
            f"Volume: {stock.get('volume', 0):,}"
        )

    prompt = f"""You are Ava, an executive AI financial analyst employee monitoring CSL Limited (ASX: CSL / CSL.AX).
Today is {datetime.now().strftime("%A, %d %B %Y")}.

Here is the latest market data and financial news:
[Market Snapshot]: {stock_context}

[Recent News Headlines]:
{news_context}

Provide a crisp, professional daily briefing for an executive investor. Include:
1. Executive Summary (2 sentences synthesizing market action and news)
2. Key News & Catalysts (3-4 concise bullet points explaining what happened and why it matters)
3. Market Sentiment & Outlook (Bullish / Neutral / Bearish with a 1-sentence rationale)

Sign off as 'Ava - AI Financial Analyst'. Be factual, concise, and professional."""

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"Error communicating with Gemini AI: {e}"


def record_briefing():
    """Perform full fetch, AI summarization, and log append."""
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_header = datetime.now().strftime("%A, %d %B %Y")

    print(f"[{today_str}] Ava is gathering news and market data for {COMPANY} ({SYMBOL})...")
    news = fetch_latest_news(limit=8)
    stock = fetch_stock_snapshot()

    print(f"[{today_str}] Synthesizing financial briefing with Gemini AI...")
    briefing = generate_ai_briefing(news, stock)

    separator = "=" * 80
    formatted_entry = f"\n{separator}\nDAILY FINANCIAL BRIEFING: {date_header} ({today_str})\n{separator}\n\n{briefing}\n"

    # Append to plain text log
    with open(BRIEFING_TXT, "a", encoding="utf-8") as f:
        f.write(formatted_entry)

    # Append to markdown log
    with open(BRIEFING_MD, "a", encoding="utf-8") as f:
        f.write(f"\n---\n\n## Daily Financial Briefing: {date_header}\n*Generated at {today_str}*\n\n{briefing}\n")

    print(f"[{today_str}] Daily briefing successfully saved to {BRIEFING_TXT}")
    return briefing


def main():
    record_briefing()


if __name__ == "__main__":
    main()
