#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Employee: Rowan - Autonomous Market Opportunity Hunter & Investment Essayist
---------------------------------------------------------------------------------
Workflow:
  AI → scan market → find opportunity/idea → research stocks → test the idea → write article → give it to you → you review/publish

Scope & Cadence:
  - Scans every morning across:
    * ASX & Australian companies
    * Major global stocks (US tech, AI leaders, multinationals)
    * Earnings & financial results disconnects
    * Share-price movements & sudden plunges (e.g. -15% selloffs)
    * Company announcements, M&A, takeovers, and capital raisings
    * Dividend anomalies & yield traps
    * Analyst & investor discussions
    * Economic developments affecting stocks
    * AI-related companies & valuation bubbles
    * Industry-wide co-movements & contagion
  - Identifies unusual or interesting situations:
    1. A stock suddenly falls 15%
    2. A company reports strong earnings but the stock falls
    3. An acquisition changes a company's valuation
    4. A high-dividend stock behaves differently from expected
    5. Several stocks in the same industry move together
    6. An AI company becomes dramatically overvalued
    7. An ASX stock experiences unusual volatility
    8. A market crash creates a historical opportunity
    9. A company's fundamentals improve while its price falls
  - Researches the company, catalyst, and market data via live yfinance and news.
  - Tests the idea quantitatively (14-day RSI, Bollinger Bands, 52-week drawdowns, volume surges, valuation multiples, margin trends).
  - Writes an 800-1,500 word Medium-style deep investment thesis.
  - Packages an Executive Review Dashboard (REVIEW_QUEUE.md) so you can review in 60 seconds and publish.
"""

import os
import sys
import json
import re
import socket
import argparse
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import yfinance as yf

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Global socket timeout
socket.setdefaulttimeout(35)

# Paths and Directory Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DRAFTS_DIR = os.path.join(BASE_DIR, "drafts")
LOG_FILE = os.path.join(BASE_DIR, "writer_employee_activity.log")
TOPIC_HISTORY_FILE = os.path.join(BASE_DIR, "topic_history.json")
LATEST_DRAFT_MD = os.path.join(BASE_DIR, "latest_medium_draft.md")
LATEST_DRAFT_TXT = os.path.join(BASE_DIR, "latest_medium_draft.txt")
REVIEW_QUEUE_MD = os.path.join(BASE_DIR, "REVIEW_QUEUE.md")

# Configuration
LOG_RETENTION_DAYS = 28  # 4 weeks rolling retention
TOPIC_MEMORY_DAYS = 30   # Prevent repeating tickers/topics in last 30 days
PRIMARY_MODEL = "gemini-3.8-flash"
CANDIDATE_MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash"]
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# Watchlist for Quantitative Morning Market Scan
SCAN_WATCHLIST = [
    # ASX Key Movers & Sectors (Mining, Banks, Biotech, Tech, Retail, Energy)
    "BHP.AX", "CBA.AX", "CSL.AX", "WES.AX", "MQG.AX", "FMG.AX", "WDS.AX", "TLS.AX",
    "DRO.AX", "ZIP.AX", "TLX.AX", "COH.AX", "SUN.AX", "PLS.AX", "MIN.AX", "ORG.AX",
    "REA.AX", "XRO.AX", "NXT.AX", "DMP.AX",
    # Global Tech, AI Leaders & US Bellwethers
    "NVDA", "TSLA", "MSFT", "AAPL", "GOOGL", "AMD", "PLTR", "ASML", "SMCI", "ARM",
    "NKE", "BABA", "META", "AMZN", "CELH"
]

# Market & Quantitative Trading News Feeds
MARKET_NEWS_FEEDS = [
    {
        "category": "Quant & Trading Concept Innovations",
        "query": "(\"quantitative trading\" OR \"algorithmic trading\" OR \"statistical arbitrage\" OR \"trading strategy\") (\"backtest\" OR \"alpha\" OR \"indicator\" OR \"machine learning\")",
        "hl": "en-US", "gl": "US", "ceid": "US:en"
    },
    {
        "category": "Volatility & Structural Market Mechanics",
        "query": "(\"volatility squeeze\" OR \"implied volatility\" OR \"order flow\" OR \"liquidity cascade\" OR \"market microstructure\" OR \"momentum breakout\") (trading OR shares)",
        "hl": "en-US", "gl": "US", "ceid": "US:en"
    },
    {
        "category": "ASX Plunges & Movers",
        "query": "ASX (plunge OR slump OR crash OR surge OR \"falls 10%\" OR \"tumbles\" OR \"trading halt\") shares",
        "hl": "en-AU", "gl": "AU", "ceid": "AU:en"
    },
    {
        "category": "Earnings & Results Disconnects",
        "query": "(\"reports earnings\" OR \"profit results\" OR \"earnings beat\" OR guidance) (\"falls\" OR \"tumbles\" OR \"slumps\" OR \"plunges\") (stock OR shares)",
        "hl": "en-US", "gl": "US", "ceid": "US:en"
    },
    {
        "category": "M&A, Takeovers & Capital Raisings",
        "query": "(acquisition OR takeover OR \"capital raising\" OR \"share placement\") (ASX OR \"Wall Street\" OR \"stock\")",
        "hl": "en-AU", "gl": "AU", "ceid": "AU:en"
    },
    {
        "category": "AI Stocks & Valuation Bubbles",
        "query": "(\"AI stock\" OR \"AI company\" OR \"tech valuation\") (overvalued OR bubble OR plunge OR \"multiple compression\")",
        "hl": "en-US", "gl": "US", "ceid": "US:en"
    },
    {
        "category": "Industry Co-Movement & Sector Contagion",
        "query": "(\"sector selloff\" OR \"industry slump\" OR \"miners plunge\" OR \"tech selloff\" OR \"stocks fall together\")",
        "hl": "en-AU", "gl": "AU", "ceid": "AU:en"
    },
    {
        "category": "Fundamentals vs Price Disconnect",
        "query": "(\"strong fundamentals\" OR \"record revenue\" OR \"undervalued\") (\"stock falls\" OR \"share price drops\" OR \"downgrade\")",
        "hl": "en-US", "gl": "US", "ceid": "US:en"
    }
]


def log(msg: str):
    """Log timestamped message to activity log and stdout."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{now_str}] [Rowan-Analyst] {msg}"
    print(formatted)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception as e:
        print(f"Failed writing to log file: {e}", file=sys.stderr)


def prune_rolling_log(log_path: str = LOG_FILE, days: int = LOG_RETENTION_DAYS):
    """Retain only the last 4 weeks of log entries to avoid unbounded file growth."""
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
        print(f"Log pruning error: {e}", file=sys.stderr)


def get_api_key() -> str:
    """Retrieve Gemini API key from environment."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise ValueError("GEMINI_API_KEY environment variable is missing or empty.")
    return key


def call_gemini(prompt: str, system_instruction: str = "", model: str = PRIMARY_MODEL, min_words: int = 0) -> str:
    """Call Google Gemini REST API with robust model fallback and retry handling."""
    import time
    api_key = get_api_key()
    models_to_try = [model] + [m for m in CANDIDATE_MODELS if m != model]

    last_error = None
    for target_model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key}"
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.6,
                "maxOutputTokens": 8192
            }
        }
        if system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
            method="POST"
        )

        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        full_text = "".join(p.get("text", "") for p in parts if "text" in p).strip()
                        if full_text:
                            words = len(full_text.split())
                            if min_words > 0 and words < min_words:
                                raise ValueError(f"Incomplete generation: returned {words} words, expected >= {min_words}.")
                            return full_text
                    raise ValueError("No text returned in Gemini response.")
            except Exception as e:
                last_error = e
                if attempt == 0:
                    time.sleep(3)
                    continue
                log(f"Warning: Model {target_model} failed after retries: {e}. Trying fallback if available...")

    raise RuntimeError(f"All Gemini model calls failed. Last error: {last_error}")


def load_topic_history() -> list:
    """Load historical topics to prevent repetitive articles."""
    if not os.path.exists(TOPIC_HISTORY_FILE):
        return []
    try:
        with open(TOPIC_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            cutoff = (datetime.now() - timedelta(days=TOPIC_MEMORY_DAYS)).strftime("%Y-%m-%d")
            return [t for t in data if t.get("date", "") >= cutoff]
    except Exception as e:
        log(f"Warning loading topic history: {e}")
        return []


def save_topic_history(history: list):
    """Save updated topic history."""
    try:
        with open(TOPIC_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"Warning saving topic history: {e}")


def fetch_rss_feed(feed_cfg: dict, max_items: int = 10) -> list:
    """Fetch news items from Google News RSS for a financial search query."""
    encoded_query = urllib.parse.quote_plus(feed_cfg["query"])
    hl = feed_cfg.get("hl", "en-AU")
    gl = feed_cfg.get("gl", "AU")
    ceid = feed_cfg.get("ceid", "AU:en")
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={ceid}"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    articles = []
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            root = ET.fromstring(resp.read().decode("utf-8", errors="replace"))
            for item in root.findall(".//item")[:max_items]:
                title_elem = item.find("title")
                pub_elem = item.find("pubDate")
                source_elem = item.find("source")
                desc_elem = item.find("description")
                link_elem = item.find("link")

                title = title_elem.text if title_elem is not None else ""
                source = source_elem.text if source_elem is not None else "Financial News"
                pub = pub_elem.text if pub_elem is not None else ""
                link = link_elem.text if link_elem is not None else ""
                desc = desc_elem.text if desc_elem is not None else ""

                clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()
                clean_desc = " ".join(clean_desc.split())[:300]

                if title:
                    articles.append({
                        "category": feed_cfg["category"],
                        "title": title,
                        "source": source,
                        "published": pub,
                        "summary": clean_desc,
                        "link": link
                    })
    except Exception as e:
        log(f"Warning: Failed to fetch feed for '{feed_cfg['category']}': {e}")
    return articles


# ==============================================================================
# STAGE 1: SCAN MARKET (Quantitative Watchlist + Financial News Feeds)
# ==============================================================================

def scan_quantitative_watchlist() -> list:
    """Scan watchlist for price moves, drawdowns, and extreme RSI anomalies."""
    log("Scanning quantitative watchlist for statistical price/volatility anomalies...")
    anomalies = []
    try:
        data = yf.download(SCAN_WATCHLIST, period="6mo", interval="1d", progress=False)["Close"]
        for t in SCAN_WATCHLIST:
            try:
                s = data[t].dropna()
                if len(s) < 20:
                    continue
                cur = float(s.iloc[-1])
                prev_1d = float(s.iloc[-2]) if len(s) >= 2 else cur
                pct_1d = ((cur - prev_1d) / prev_1d) * 100
                
                prev_5d = float(s.iloc[-5]) if len(s) >= 5 else cur
                pct_5d = ((cur - prev_5d) / prev_5d) * 100
                
                # 14-day RSI
                delta = s.diff()
                gain = delta.clip(lower=0).rolling(14).mean()
                loss = (-delta.clip(upper=0)).rolling(14).mean()
                rs = gain / loss.replace(0, np.nan)
                rsi_series = (100 - (100 / (1 + rs)))
                rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0

                # 52-week High Drawdown
                high_52w = float(s.max())
                drawdown = ((cur - high_52w) / high_52w) * 100

                # 20-day Bollinger Bands %B
                sma20 = float(s.rolling(20).mean().iloc[-1])
                std20 = float(s.rolling(20).std().iloc[-1])
                upper_bb = sma20 + (2 * std20)
                lower_bb = sma20 - (2 * std20)
                pct_b = float((cur - lower_bb) / (upper_bb - lower_bb)) if upper_bb != lower_bb else 0.5

                # Flag unusual conditions
                flags = []
                if pct_1d <= -4.0 or pct_5d <= -8.0:
                    flags.append(f"Sharp Drop (1d: {pct_1d:+.1f}%, 5d: {pct_5d:+.1f}%)")
                if pct_1d >= 5.0 or pct_5d >= 10.0:
                    flags.append(f"Sharp Surge (1d: {pct_1d:+.1f}%, 5d: {pct_5d:+.1f}%)")
                if rsi <= 30.0:
                    flags.append(f"Oversold (RSI: {rsi:.1f})")
                elif rsi >= 75.0:
                    flags.append(f"Overbought (RSI: {rsi:.1f})")
                if drawdown <= -30.0:
                    flags.append(f"Deep Drawdown ({drawdown:.1f}% from 52w High)")
                if pct_b <= 0.15:
                    flags.append("Piercing Lower Bollinger Band")
                elif pct_b >= 0.85:
                    flags.append("Piercing Upper Bollinger Band")

                if flags:
                    anomalies.append({
                        "ticker": t,
                        "price": round(cur, 2),
                        "pct_1d": round(pct_1d, 2),
                        "pct_5d": round(pct_5d, 2),
                        "rsi": round(rsi, 1),
                        "pct_b": round(pct_b, 2),
                        "drawdown_52w": round(drawdown, 2),
                        "flags": ", ".join(flags)
                    })
            except Exception:
                continue
    except Exception as e:
        log(f"Warning during quantitative scan: {e}")

    log(f"Identified {len(anomalies)} statistical anomalies across watchlist.")
    return anomalies


def scan_news_anomalies() -> list:
    """Scan market news feeds for corporate and financial anomalies."""
    log("Scanning financial news feeds for earnings, M&A, dividends, and market shocks...")
    news_items = []
    seen = set()
    for cfg in MARKET_NEWS_FEEDS:
        items = fetch_rss_feed(cfg, max_items=8)
        for it in items:
            key = re.sub(r"[^a-zA-Z0-9]", "", it["title"].lower())[:40]
            if key and key not in seen:
                seen.add(key)
                news_items.append(it)
    log(f"Compiled {len(news_items)} financial headlines across 7 anomaly categories.")
    return news_items


# ==============================================================================
# STAGE 2: FIND OPPORTUNITY / IDEA (New Concepts & Innovative Trading Ideas)
# ==============================================================================

def find_opportunity_idea(quant_anomalies: list, news_items: list, history: list, manual_ticker: str = "", manual_concept: str = "") -> dict:
    """
    Select or formulate a cutting-edge TRADING CONCEPT or INNOVATIVE STRATEGY IDEA,
    paired with an empirical test asset from today's market scan.
    Paradigms:
      - VOLATILITY_COMPRESSION: Volatility squeeze (Bollinger inside Keltner / ATR compression)
      - STATISTICAL_ARBITRAGE: Cointegration, spread stationarity, and Ornstein-Uhlenbeck mean-reversion
      - REGIME_DETECTION: Hurst Exponent & volatility clustering to filter market state
      - ORDER_FLOW_MICROSTRUCTURE: Anchored VWAP standard deviation bands & volume absorption
      - ASYMMETRIC_MEAN_REVERSION: Multi-sigma Z-Score divergence beyond naive RSI
      - DUAL_MOMENTUM_ROTATION: Cross-sectional relative strength & sector rotation
      - ML_FEATURE_ENGINEERING: Fractional differentiation & preservation of memory
      - CONVEX_POSITION_SIZING: Dynamic Half-Kelly criterion & volatility targeting
      - CATALYST_PEAD_MOMENTUM: Post-Earnings Announcement Drift & volatility mispricing
    """
    if manual_concept or manual_ticker:
        ticker = manual_ticker.upper() if manual_ticker else (quant_anomalies[0]["ticker"] if quant_anomalies else "CSL.AX")
        concept_title = manual_concept or f"Innovative Quantitative Strategy in {ticker}"
        log(f"Manual input specified: Concept='{manual_concept}', Ticker='{ticker}'")
        return {
            "trading_concept": concept_title,
            "concept_paradigm": "USER_SPECIFIED_CONCEPT",
            "ticker": ticker,
            "company_name": ticker,
            "headline": f"{concept_title}: Testing New Trading Mechanics with {ticker}",
            "core_concept_thesis": f"Explores novel quantitative trading edge ({concept_title}) tested on live market data.",
            "hypothesis": f"Quantitative edge derived from {concept_title} providing asymmetric risk/reward vs benchmark.",
            "search_query": f"{concept_title} quantitative trading strategy backtest python"
        }

    history_entries = [f"- {t.get('trading_concept', t.get('title', ''))} [{t.get('ticker', '')}] ({t.get('date', '')})" for t in history[-10:]]
    history_context = "\n".join(history_entries) if history_entries else "No concepts recorded in recent history."

    quant_text = "\n".join([
        f"• [{a['ticker']}] Price: ${a['price']} | 1d: {a['pct_1d']:+}% | 5d: {a['pct_5d']:+}% | RSI: {a['rsi']} | DD_52w: {a['drawdown_52w']}% | Flags: {a['flags']}"
        for a in quant_anomalies[:15]
    ]) or "No extreme quantitative outliers today."

    news_text = "\n".join([
        f"• [{n['category']}] {n['title']} (Source: {n['source']})"
        for n in news_items[:35]
    ])

    system_prompt = """You are Rowan, an elite autonomous quantitative researcher, algorithmic trader, and top Medium essayist.
You specialize in discovering and explaining NOVEL TRADING CONCEPTS, CUTTING-EDGE STRATEGY IDEAS, and MATHEMATICAL TRADING EDGES for Medium readers (developers, quants, algorithmic traders).
You believe standard retail indicators (plain 14-period RSI, basic moving average crossovers, textbook chart patterns) are commoditized or broken.
Your mission is to formulate and teach modern, innovative trading concepts—combining quantitative theory, behavioral market anomalies, and practical Python backtests."""

    prompt = f"""Review the morning market data, quantitative outliers, and algorithmic research signals:

[RECENTLY EXPLORED CONCEPTS & TICKERS - DO NOT DUPLICATE THESE TOPICS]:
{history_context}

[QUANTITATIVE STATISTICAL ANOMALIES TODAY]:
{quant_text}

[MARKET & QUANTITATIVE NEWS SIGNALS]:
{news_text}

TASK:
Formulate ONE standout NEW TRADING CONCEPT OR INNOVATIVE STRATEGY IDEA to teach your Medium readers today.
Medium readers crave actionable, intellectually stimulating concepts such as:
1. VOLATILITY_COMPRESSION: Volatility squeeze (Bollinger Bands contracting inside Keltner Channels / ATR compression) predicting explosive asymmetric expansion.
2. STATISTICAL_ARBITRAGE: Cointegration, synthetic spread stationarity, and Ornstein-Uhlenbeck mean-reverting pairs.
3. REGIME_DETECTION: Using Hurst Exponent, volatility clustering, or Markov regime switching to dynamically toggle between trend and mean-reversion.
4. ORDER_FLOW_MICROSTRUCTURE: Anchored VWAP standard deviation bands, institutional volume absorption, and liquidity void sweeps.
5. ASYMMETRIC_MEAN_REVERSION: Rolling Z-Score divergence and extreme multi-sigma reversion beyond naive RSI.
6. DUAL_MOMENTUM_ROTATION: Cross-sectional relative strength ranking and regime-filtered momentum rotation across sectors.
7. ML_FEATURE_ENGINEERING: Fractional differentiation (preserving price series memory while achieving stationarity) or meta-labeling.
8. CONVEX_POSITION_SIZING: Dynamic Half-Kelly criterion, volatility targeting, and risk parity at the trade level.
9. CATALYST_PEAD_MOMENTUM: Post-Earnings Announcement Drift (PEAD) and implied vs realized volatility skew.

Pair this concept with ONE standout asset from today's market scan (e.g. {quant_anomalies[0]['ticker'] if quant_anomalies else 'CSL.AX'}) as the empirical test case!

Return your selection strictly as JSON matching this schema:
{{
  "trading_concept": "Concise name of the new trading concept (e.g. 'The Hurst Exponent Regime Filter' or 'The Multi-Sigma Volatility Squeeze Engine')",
  "concept_paradigm": "One of: VOLATILITY_COMPRESSION / STATISTICAL_ARBITRAGE / REGIME_DETECTION / ORDER_FLOW_MICROSTRUCTURE / ASYMMETRIC_MEAN_REVERSION / DUAL_MOMENTUM_ROTATION / ML_FEATURE_ENGINEERING / CONVEX_POSITION_SIZING / CATALYST_PEAD_MOMENTUM",
  "ticker": "Ticker symbol used to empirically test and demonstrate the concept (e.g. MGH.AX, NVDA, BHP.AX, XRO.AX)",
  "company_name": "Full company name of test asset",
  "headline": "Arresting, concept-forward title for Medium readers",
  "core_concept_thesis": "Why this trading concept creates an edge, and why conventional retail indicators fail",
  "hypothesis": "The specific quantitative trading hypothesis to backtest (entry triggers, invalidation, expected payoff)",
  "search_query": "3-5 targeted keywords to research technical context and empirical benchmarks"
}}
Return ONLY raw JSON, with no enclosing code blocks or formatting."""

    raw_response = call_gemini(prompt, system_instruction=system_prompt)
    cleaned = re.sub(r"^```json\s*", "", raw_response.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        data = json.loads(cleaned)
        return data
    except Exception as e:
        log(f"Error parsing opportunity JSON: {e}. Fallback to quantitative volatility concept...")
        fallback_ticker = quant_anomalies[0]["ticker"] if quant_anomalies else "CSL.AX"
        return {
            "trading_concept": "The Asymmetric Volatility Squeeze Breakout",
            "concept_paradigm": "VOLATILITY_COMPRESSION",
            "ticker": fallback_ticker,
            "company_name": fallback_ticker,
            "headline": f"Beyond Naive RSI: How the Volatility Squeeze Engine Trades Breakouts in {fallback_ticker}",
            "core_concept_thesis": "Markets transition cyclically between low volatility compression and explosive expansion.",
            "hypothesis": "Bollinger bandwidth compression inside Keltner channels predicts impending multi-sigma trend expansion.",
            "search_query": f"{fallback_ticker} volatility squeeze trading strategy backtest python"
        }


# ==============================================================================
# STAGE 3: RESEARCH STOCKS (Live Fundamentals, Historical Ratios, Catalyst News)
# ==============================================================================

def research_stock_data(opportunity: dict) -> dict:
    """Fetch deep financial metrics and targeted catalyst reporting."""
    ticker = opportunity.get("ticker", "CSL.AX")
    log(f"Conducting deep stock research for {ticker} via yfinance...")

    stock_metrics = {}
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1y")
        info = t.info or {}

        cur_price = float(hist["Close"].iloc[-1]) if not hist.empty else float(info.get("regularMarketPrice", 0))
        high_52w = float(hist["Close"].max()) if not hist.empty else float(info.get("fiftyTwoWeekHigh", cur_price))
        low_52w = float(hist["Close"].min()) if not hist.empty else float(info.get("fiftyTwoWeekLow", cur_price))
        drawdown = ((cur_price - high_52w) / high_52w) * 100 if high_52w else 0.0

        stock_metrics = {
            "ticker": ticker,
            "company_name": info.get("shortName") or info.get("longName") or opportunity.get("company_name", ticker),
            "sector": info.get("sector", "Equities"),
            "industry": info.get("industry", "General"),
            "currency": info.get("currency", "AUD" if ".AX" in ticker else "USD"),
            "current_price": round(cur_price, 2),
            "high_52w": round(high_52w, 2),
            "low_52w": round(low_52w, 2),
            "drawdown_52w": round(drawdown, 2),
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "price_to_book": info.get("priceToBook"),
            "operating_margins": info.get("operatingMargins"),
            "profit_margins": info.get("profitMargins"),
            "return_on_equity": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
            "free_cashflow": info.get("freeCashflow"),
            "dividend_yield": info.get("dividendYield"),
            "target_mean_price": info.get("targetMeanPrice"),
            "history_df": hist
        }
    except Exception as e:
        log(f"Warning fetching yfinance data for {ticker}: {e}")

    # Gather targeted catalyst news
    search_q = opportunity.get("search_query") or f"{ticker} stock price news"
    log(f"Gathering multi-source reporting for catalyst: '{search_q}'...")
    cfg = {
        "category": "Catalyst Research",
        "query": search_q,
        "hl": "en-AU" if ".AX" in ticker else "en-US",
        "gl": "AU" if ".AX" in ticker else "US",
        "ceid": "AU:en" if ".AX" in ticker else "US:en"
    }
    catalyst_news = fetch_rss_feed(cfg, max_items=8)

    return {
        "metrics": stock_metrics,
        "catalyst_news": catalyst_news
    }


# ==============================================================================
# STAGE 4: TEST THE IDEA (Technical & Fundamental Quantitative Reality Check)
# ==============================================================================

def test_the_idea(opportunity: dict, research: dict) -> dict:
    """
    Execute quantitative audit on the strategy hypothesis:
      - Volatility compression / Bollinger bandwidth
      - Multi-sigma rolling Z-score
      - 14-day RSI (momentum oversold/overbought)
      - ATR (Average True Range) volatility percentage
      - Volume surge ratio (capitulation / absorption test)
      - Valuation & balance sheet sanity check
    Assigns:
      - Opportunity Score (1-10)
      - Strategy Verdict based on the specific concept paradigm
    """
    metrics = research.get("metrics", {})
    hist = metrics.get("history_df", pd.DataFrame())

    log(f"Running quantitative audit on trading concept for {opportunity.get('ticker')}...")

    rsi_14 = 50.0
    pct_b = 0.5
    bb_bandwidth = 0.10
    z_score_20 = 0.0
    vol_ratio = 1.0
    pct_drop_30d = 0.0
    atr_14_pct = 2.0
    sma50_trend = "NEUTRAL"

    if not hist.empty and len(hist) >= 20:
        close = hist["Close"]
        cur = float(close.iloc[-1])
        # RSI
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi_series = (100 - (100 / (1 + rs)))
        rsi_14 = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0

        # Bollinger Bands & Bandwidth
        sma20 = float(close.rolling(20).mean().iloc[-1])
        std20 = float(close.rolling(20).std().iloc[-1]) if float(close.rolling(20).std().iloc[-1]) > 0 else 0.01
        upper_bb = sma20 + (2 * std20)
        lower_bb = sma20 - (2 * std20)
        pct_b = float((cur - lower_bb) / (upper_bb - lower_bb)) if upper_bb != lower_bb else 0.5
        bb_bandwidth = round(float((upper_bb - lower_bb) / sma20), 4) if sma20 > 0 else 0.10
        z_score_20 = round(float((cur - sma20) / std20), 2)

        # ATR 14
        if "High" in hist.columns and "Low" in hist.columns:
            high = hist["High"]
            low = hist["Low"]
            tr = pd.concat([
                high - low,
                (high - close.shift(1)).abs(),
                (low - close.shift(1)).abs()
            ], axis=1).max(axis=1)
            atr14 = float(tr.rolling(14).mean().iloc[-1])
            atr_14_pct = round((atr14 / cur) * 100, 2) if cur > 0 else 2.0

        # SMA 50 Trend
        if len(close) >= 50:
            sma50 = float(close.rolling(50).mean().iloc[-1])
            sma50_trend = "BULLISH_ABOVE_50SMA" if cur >= sma50 else "BEARISH_BELOW_50SMA"

        # Volume Capitulation Test
        vol = hist["Volume"]
        recent_vol = float(vol.iloc[-5:].mean())
        avg_vol = float(vol.iloc[-30:].mean()) if len(vol) >= 30 else recent_vol
        vol_ratio = round(recent_vol / avg_vol, 2) if avg_vol > 0 else 1.0

        # 30-day drop
        p_30d = float(close.iloc[-20]) if len(close) >= 20 else cur
        pct_drop_30d = round(((cur - p_30d) / p_30d) * 100, 2)

    # Fundamental test
    fwd_pe = metrics.get("forward_pe")
    trail_pe = metrics.get("trailing_pe")
    de_ratio = metrics.get("debt_to_equity")
    op_margins = metrics.get("operating_margins")
    drawdown = metrics.get("drawdown_52w", 0.0)

    # Concept-Driven Strategy Verdict
    paradigm = opportunity.get("concept_paradigm", "")
    score = 7.5
    verdict = f"HIGH-CONVICTION {paradigm} SETUP" if paradigm else "ASYMMETRIC EDGE SETUP"
    risk_level = "MODERATE"

    if bb_bandwidth < 0.08:
        score += 1.0
        verdict = "EXTREME VOLATILITY COMPRESSION (BREAKOUT IMMINENT)"
    elif abs(z_score_20) >= 2.2:
        score += 1.0
        verdict = "STATISTICAL MULTI-SIGMA MEAN REVERSION"
    elif rsi_14 <= 25.0 and pct_b <= 0.15:
        score += 1.0
        verdict = "ASYMMETRIC MEAN-REVERSION OPPORTUNITY"
    elif rsi_14 >= 80.0:
        score = 8.5
        verdict = "EXTREME OVERBOUGHT / MEAN REVERSION SHORT SETUP"

    if de_ratio and de_ratio > 200.0:
        score -= 0.5
        risk_level = "ELEVATED SOLVENCY RISK"

    test_results = {
        "ticker": opportunity.get("ticker"),
        "rsi_14": round(rsi_14, 1),
        "pct_b": round(pct_b, 2),
        "bb_bandwidth": bb_bandwidth,
        "z_score_20": z_score_20,
        "atr_14_pct": atr_14_pct,
        "sma50_trend": sma50_trend,
        "vol_ratio_5d_vs_30d": vol_ratio,
        "pct_drop_30d": pct_drop_30d,
        "drawdown_52w": drawdown,
        "trailing_pe": trail_pe,
        "forward_pe": fwd_pe,
        "debt_to_equity": de_ratio,
        "operating_margin_pct": round(op_margins * 100, 2) if op_margins else None,
        "opportunity_score": min(max(round(score, 1), 1.0), 10.0),
        "verdict": verdict,
        "risk_level": risk_level,
        "asymmetric_upside_target": metrics.get("target_mean_price")
    }

    log(f"Test Verdict: {verdict} | Score: {test_results['opportunity_score']}/10 | Bandwidth: {bb_bandwidth} | Z-Score: {z_score_20}")
    return test_results


# ==============================================================================
# STAGE 5: WRITE ARTICLE (New Trading Concepts & Algorithmic Strategy Deep Dives)
# ==============================================================================

def write_investment_article(opportunity: dict, research: dict, test_results: dict) -> str:
    """Compose an 1,000-1,800 word Medium technical article teaching a new trading concept or innovative strategy idea."""
    today_str = datetime.now().strftime("%A, %d %B %Y")
    metrics = research.get("metrics", {})
    news_items = research.get("catalyst_news", [])

    concept_name = opportunity.get("trading_concept") or opportunity.get("headline", "Innovative Trading Concept")
    paradigm = opportunity.get("concept_paradigm") or opportunity.get("anomaly_type", "QUANTITATIVE_STRATEGY")

    news_text = "\n".join([
        f"- {n['title']} (Source: {n['source']}, {n['published']}): {n['summary']}"
        for n in news_items[:6]
    ]) or "Standard market disclosures and price fluctuations."

    system_prompt = """You are Rowan, an acclaimed quantitative trading strategist, algorithmic systems architect, and top Medium writer (featured in Towards Data Science, DataDrivenInvestor, and Generative AI).
You specialize in introducing NOVEL TRADING CONCEPTS, CUTTING-EDGE STRATEGY IDEAS, and MATHEMATICAL EDGES for developers, quants, and traders on Medium.
Your writing style is:
- Concept-First & Educational: You deconstruct complex quantitative, statistical, and behavioral market mechanics into gripping, intuitive explanations that Medium readers bookmark and study.
- Anti-Retail Hype: You relentlessly expose why naive retail trading indicators (static 14-period RSI, basic 50/200 SMA crosses, textbook chart patterns) decay into unprofitable noise.
- Mathematically Rigorous: You explain the formulas, statistical distributions, and quantitative intuition behind the edge.
- Code-Driven & Reproducible: Every article includes a complete, beautiful, copy-pasteable Python backtest script using real market data that readers can run in Google Colab."""

    prompt = f"""Today is {today_str}.

Write a high-conviction, publication-grade Medium technical article introducing this NEW TRADING CONCEPT / STRATEGY IDEA:

[THE TRADING CONCEPT / IDEA]:
Concept Name: {concept_name}
Paradigm: {paradigm}
Headline: {opportunity.get('headline')}
Core Thesis: {opportunity.get('core_concept_thesis') or opportunity.get('core_anomaly')}
Strategy Hypothesis: {opportunity.get('hypothesis')}

[EMPIRICAL CASE STUDY ASSET]:
Ticker: {opportunity.get('ticker')} ({metrics.get('company_name')})
Current Price: ${metrics.get('current_price')} {metrics.get('currency')}
52-Week Range: [${metrics.get('low_52w')} - ${metrics.get('high_52w')}]
Drawdown from High: {metrics.get('drawdown_52w')}%
Trailing P/E: {metrics.get('trailing_pe')} | Forward P/E: {metrics.get('forward_pe')}

[QUANTITATIVE TEST & METRICS ON CASE ASSET]:
14-Day RSI: {test_results.get('rsi_14')}
Bollinger Band %B: {test_results.get('pct_b')}
Bollinger Bandwidth (Compression): {test_results.get('bb_bandwidth')}
Rolling 20-Day Z-Score: {test_results.get('z_score_20')}
14-Day ATR Volatility: {test_results.get('atr_14_pct')}%
50-Day Trend State: {test_results.get('sma50_trend')}
Volume Absorption Ratio (5d vs 30d avg): {test_results.get('vol_ratio_5d_vs_30d')}x
Opportunity Score: {test_results.get('opportunity_score')}/10
Strategy Verdict: {test_results.get('verdict')}

[MARKET & CATALYST CONTEXT]:
{news_text}

MANDATORY EDITORIAL STRUCTURE FOR MEDIUM READERS:
1. WORD COUNT: Approximately 1,000 to 1,800 words. Rich, in-depth, and substantive.
2. TITLE & SUBTITLE:
   - Create an irresistible, concept-centric H1 title (e.g. "Beyond the 14-Day RSI: The Volatility Squeeze Strategy That Actually Works" or "The Cointegration Alpha: How to Trade Statistical Arbitrage in Python").
   - Follow with an intriguing H3 subtitle setting the hook for quants and active traders.
3. THE FLAW IN CONVENTIONAL WISDOM:
   - Open by addressing why 95% of retail traders lose using standard indicators. Explain the flaw in popular indicators when applied to this specific market phenomenon.
4. THE NEW TRADING CONCEPT UNPACKED:
   - Define the new concept or strategy clearly. Explain the underlying mathematical intuition (e.g. volatility cycles, stationary time series, regime switches, order flow absorption).
5. THE MATHEMATICAL / ALGORITHMIC MECHANISM:
   - Walk through the core mathematical formula or quantitative rules step-by-step so the reader understands the mechanics.
6. REAL-WORLD CASE STUDY & QUANTITATIVE AUDIT:
   - Apply this concept directly to {opportunity.get('ticker')} and recent market dynamics using the quantitative metrics above.
   - Show how the strategy signals compare to naive indicator readings.
7. COMPLETE RUNNABLE PYTHON / GOOGLE COLAB PROJECT:
   - Provide a full, clean, standalone Python script using yfinance, pandas, numpy, and matplotlib.
   - The script must:
     a) Download historical data for {opportunity.get('ticker')}.
     b) Vectorially compute the custom concept indicator / strategy rules.
     c) Generate Buy/Sell/Hold signals without lookahead bias.
     d) Compute an equity curve and benchmark comparison (Cumulative Return, Sharpe, Max Drawdown).
     e) Plot the indicator and trading performance clearly.
8. EXECUTION REALITIES & RISK ARCHITECTURE:
   - Detail position sizing rules (e.g. Volatility targeting, Half-Kelly criterion), stop invalidation points, and where this strategy regime fails.
9. THE 3 GOLDEN RULES:
   - Summarize 3 sharp, memorable takeaways the reader can immediately apply.
10. MEDIUM HASHTAGS:
    - End on the final line with 6-8 relevant tags: #Trading #AlgorithmicTrading #Python #QuantitativeFinance #StockMarket #Investing #DataScience

Format the entire output in clean, elegant GitHub-flavored Markdown ready to paste into Medium."""

    log("Composing full-length Medium trading concept article with Gemini...")
    article_md = call_gemini(prompt, system_instruction=system_prompt, min_words=600)
    return article_md


# ==============================================================================
# STAGE 6: GIVE IT TO YOU (Executive Review Package & Persistence)
# ==============================================================================

def generate_review_package(opportunity: dict, research: dict, test_results: dict, article_md: str) -> str:
    """Generate the 60-second Executive Review Queue document for the user."""
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    metrics = research.get("metrics", {})
    ticker = opportunity.get("ticker", "TICKER")
    concept_name = opportunity.get("trading_concept") or opportunity.get("headline", "Innovative Trading Concept")
    paradigm = opportunity.get("concept_paradigm", "QUANTITATIVE_STRATEGY")

    lines = article_md.split("\n")
    title = lines[0].replace("#", "").strip() if lines else concept_name
    subtitle = lines[2].replace("###", "").replace("*", "").strip() if len(lines) > 2 else ""
    word_count = len(article_md.split())
    read_time = max(1, round(word_count / 220))

    review_content = f"""# 📋 Rowan's Morning Review Queue: New Trading Concept & Strategy

> **Executive Status**: Ready for Review & Publishing  
> **Generated**: {today_str} | **Analyst**: Rowan (Autonomous Quantitative Trading Essayist)

---

## 🎯 Executive Pitch (60-Second Briefing)

* **Trading Concept / Strategy**: **{concept_name}**
* **Strategy Paradigm**: **`{paradigm}`**
* **Case Study Asset**: **{metrics.get('company_name', ticker)} ({ticker})**
* **Core Trading Edge**: {opportunity.get('core_concept_thesis') or opportunity.get('core_anomaly')}
* **Working Hypothesis**: {opportunity.get('hypothesis')}
* **Rowan's Quantitative Verdict**: **`{test_results.get('verdict')}`** (Opportunity Score: **{test_results.get('opportunity_score')}/10**)

---

## 📊 Quantitative Scorecard & Technical Audit

| Dimension | Metric | Assessment |
| :--- | :--- | :--- |
| **Test Asset Price** | ${metrics.get('current_price')} {metrics.get('currency')} | 52-Week Range: [${metrics.get('low_52w')} - ${metrics.get('high_52w')}] |
| **Bollinger Bandwidth** | **{test_results.get('bb_bandwidth')}** | {'Extreme Compression (Breakout Setup)' if test_results.get('bb_bandwidth', 0.1) < 0.08 else 'Normal Volatility'} |
| **Rolling 20-Day Z-Score** | **{test_results.get('z_score_20')}σ** | {'Multi-Sigma Statistical Divergence' if abs(test_results.get('z_score_20', 0)) >= 2.0 else 'Within Gaussian Norms'} |
| **14-Day RSI** | **{test_results.get('rsi_14')}** | {'Oversold (<30)' if test_results.get('rsi_14', 50) <= 30 else ('Overbought (>75)' if test_results.get('rsi_14', 50) >= 75 else 'Neutral Momentum')} |
| **ATR Volatility (14-Day)** | **{test_results.get('atr_14_pct')}%** | Baseline Asset Volatility |
| **50-Day Trend State** | **{test_results.get('sma50_trend')}** | Market Regime Filter |
| **Volume Absorption Ratio** | **{test_results.get('vol_ratio_5d_vs_30d')}x** | {'High Volume Activity' if test_results.get('vol_ratio_5d_vs_30d', 1) > 1.5 else 'Average Volume'} |
| **Strategic Edge Verdict** | **{test_results.get('verdict')}** | Score: {test_results.get('opportunity_score')}/10 |

---

## 📝 Generated Medium Article Deliverable

* **Proposed Title**: **{title}**
* **Subtitle**: *{subtitle}*
* **Word Count**: **{word_count} words** (~{read_time} min Medium read)
* **Embedded Project**: Full standalone Python backtest script with signal logic and performance metrics.
* **Full Draft Path**: [`latest_medium_draft.md`](latest_medium_draft.md)
* **Plain Text (Ready to Copy)**: [`latest_medium_draft.txt`](latest_medium_draft.txt)

---

## ✅ User Review & Publishing Actions

- [ ] **Review Article Draft**: Read [`latest_medium_draft.md`](latest_medium_draft.md)
- [ ] **Copy & Paste to Medium**: Copy text from [`latest_medium_draft.txt`](latest_medium_draft.txt)
- [ ] **Verify Python Project**: Run the embedded Python/Colab backtest script
- [ ] **Publish Status**: Ready to Publish

---
*Archived permanently to `drafts/` with rolling 4-week activity log in `writer_employee_activity.log`.*
"""
    with open(REVIEW_QUEUE_MD, "w", encoding="utf-8") as f:
        f.write(review_content)
    log(f"Executive Review Queue generated: {REVIEW_QUEUE_MD}")
    return review_content


def save_all_deliverables(opportunity: dict, research: dict, test_results: dict, article_md: str):
    """Save article, update latest pointers, and update topic history."""
    os.makedirs(DRAFTS_DIR, exist_ok=True)
    today_date = datetime.now().strftime("%Y-%m-%d")
    ticker = opportunity.get("ticker", "TICKER").replace(".", "_")

    raw_title = opportunity.get("headline", "market_anomaly")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", raw_title).strip("_").lower()[:40]
    filename = f"{today_date}_{ticker}_{slug}.md"
    archive_path = os.path.join(DRAFTS_DIR, filename)

    # 1. Save timestamped archive
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(article_md)
    log(f"Archived draft saved: {archive_path}")

    # 2. Update latest_medium_draft.md
    with open(LATEST_DRAFT_MD, "w", encoding="utf-8") as f:
        f.write(article_md)

    # 3. Update plain text copy
    with open(LATEST_DRAFT_TXT, "w", encoding="utf-8") as f:
        f.write(article_md)

    # 4. Generate Executive Review Queue
    generate_review_package(opportunity, research, test_results, article_md)

    # 5. Update topic history ledger
    history = load_topic_history()
    history.append({
        "date": today_date,
        "trading_concept": opportunity.get("trading_concept", opportunity.get("headline")),
        "concept_paradigm": opportunity.get("concept_paradigm", opportunity.get("anomaly_type")),
        "ticker": opportunity.get("ticker"),
        "title": opportunity.get("headline"),
        "verdict": test_results.get("verdict"),
        "file": filename
    })
    save_topic_history(history)
    log(f"Topic history updated ({len(history)} entries tracked).")


def run_cycle(manual_ticker: str = "", manual_concept: str = "", dry_run: bool = False):
    """Execute complete workflow: Scan → Formulate Trading Concept → Research → Test → Write → Give to You."""
    log("=========================================================================")
    log("Rowan is beginning the Autonomous Trading Concept & Writing cycle...")
    log("=========================================================================")

    # Step 1: Scan Market
    log("Stage 1/6: Scanning market (Quantitative watchlist + Market & Quant news vectors)...")
    quant_anomalies = scan_quantitative_watchlist()
    news_items = scan_news_anomalies()

    # Step 2: Formulate Concept & Opportunity
    log("Stage 2/6: Formulating innovative trading concept and selecting test asset...")
    history = load_topic_history()
    opportunity = find_opportunity_idea(quant_anomalies, news_items, history, manual_ticker=manual_ticker, manual_concept=manual_concept)
    log(f"Trading Concept: [{opportunity.get('trading_concept')}] ({opportunity.get('concept_paradigm')})")
    log(f"Case Study Asset: [{opportunity.get('ticker')}] {opportunity.get('headline')}")
    log(f"Core Concept Thesis: {opportunity.get('core_concept_thesis')}")
    log(f"Strategy Hypothesis: {opportunity.get('hypothesis')}")

    if dry_run:
        log("[Dry Run Complete] Trading concept formulated successfully.")
        return

    # Step 3: Research Stocks
    log("Stage 3/6: Conducting deep market research and fetching financial metrics...")
    research = research_stock_data(opportunity)

    # Step 4: Test the Idea
    log("Stage 4/6: Testing concept quantitatively (Volatility Bandwidth, Z-Score, ATR, RSI)...")
    test_results = test_the_idea(opportunity, research)

    # Step 5: Write Article
    log("Stage 5/6: Writing 1,000-1,800 word Medium trading concept article with runnable Python backtest...")
    article_md = write_investment_article(opportunity, research, test_results)

    # Step 6: Give it to You (Review Package)
    log("Stage 6/6: Packaging deliverables into Executive Review Queue (REVIEW_QUEUE.md)...")
    save_all_deliverables(opportunity, research, test_results, article_md)

    prune_rolling_log()

    word_count = len(article_md.split())
    log("=========================================================================")
    log(f"Cycle Complete! Article: {word_count} words | Verdict: {test_results.get('verdict')}")
    log(f"Executive Review Queue ready at: {REVIEW_QUEUE_MD}")
    log("=========================================================================")


def main():
    parser = argparse.ArgumentParser(description="Rowan: Autonomous Trading Concept Hunter & Medium Writer")
    parser.add_argument("--run-now", action="store_true", help="Trigger execution immediately")
    parser.add_argument("--concept", type=str, default="", help="Specify a custom trading concept or strategy idea")
    parser.add_argument("--ticker", type=str, default="", help="Provide a custom ticker to test the concept on")
    parser.add_argument("--dry-run", action="store_true", help="Scan and formulate concept without writing full draft")
    args = parser.parse_args()

    run_cycle(manual_ticker=args.ticker, manual_concept=args.concept, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
