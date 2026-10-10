#!/usr/bin/env python3
"""
AI Employee: Ava - Autonomous Market Monitoring Agent
------------------------------------------------------
Role: Autonomous financial analyst employee.
Task: Automatically monitors CSL.AX (CSL Limited on the ASX) every 30 minutes,
      recording real-time prices, market movements, and analytical logs into
      the local workspace without requiring manual human prompts.
"""

import os
import sys
import time
import json
import csv
import signal
import atexit
import argparse
import socket
from datetime import datetime, timezone
import urllib.request
import urllib.error

# Ensure network calls never hang indefinitely
socket.setdefaulttimeout(15)

# Disable QuickEdit mode on Windows to prevent mouse clicks from freezing the terminal
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        hStdin = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(hStdin, ctypes.byref(mode)):
            ENABLE_QUICK_EDIT_MODE = 0x0040
            kernel32.SetConsoleMode(hStdin, mode.value & ~ENABLE_QUICK_EDIT_MODE)
    except Exception:
        pass

# Configuration
SYMBOL = "CSL.AX"
COMPANY_NAME = "CSL Limited"
CHECK_INTERVAL_SECONDS = 1800  # 30 minutes
API_URL = f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?interval=1m&range=1d"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Base directory is always the script's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE_PATH = os.path.join(BASE_DIR, "CSL_AX_prices.csv")
LOG_FILE_PATH = os.path.join(BASE_DIR, "employee_activity.log")
SIMPLE_LOG_PATH = os.path.join(BASE_DIR, "csl_price_log.txt")
PID_FILE_PATH = os.path.join(BASE_DIR, "employee.pid")


def log_message(message: str, level: str = "INFO", console_output: bool = True):
    """Write formatted log entry to employee_activity.log and console."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_entry = f"[{now_str}] [Ava - AI Employee] [{level}] {message}"
    
    if console_output and sys.stdout is not None:
        try:
            # Clear line first in case countdown was active
            sys.stdout.write("\r" + " " * 90 + "\r")
            print(formatted_entry, flush=True)
        except Exception:
            pass
        
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(formatted_entry + "\n")
    except Exception as e:
        if sys.stderr is not None:
            print(f"Failed to write to log file: {e}", file=sys.stderr)


def init_csv():
    """Ensure CSV file exists with proper headers."""
    if not os.path.exists(CSV_FILE_PATH):
        try:
            with open(CSV_FILE_PATH, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp_Local",
                    "Timestamp_UTC",
                    "Symbol",
                    "Company",
                    "Price_AUD",
                    "Previous_Close_AUD",
                    "Change_AUD",
                    "Change_Percent",
                    "Day_Low_AUD",
                    "Day_High_AUD",
                    "Volume",
                    "Market_State",
                    "Ava_Assessment"
                ])
            log_message(f"Initialized new tracking ledger: {os.path.basename(CSV_FILE_PATH)}")
        except Exception as e:
            log_message(f"Could not initialize CSV: {e}", level="ERROR")


def fetch_csl_data(retries: int = 3, retry_delay: int = 15) -> dict:
    """Fetch real-time stock data from market API with retry support."""
    req = urllib.request.Request(API_URL, headers={"User-Agent": USER_AGENT})
    
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    result = data.get("chart", {}).get("result")
                    if result and len(result) > 0:
                        return result[0].get("meta", {})
                    else:
                        raise ValueError("Empty or malformed market payload received.")
                else:
                    raise urllib.error.HTTPError(
                        response.url, response.status, f"HTTP status {response.status}", response.headers, None
                    )
        except Exception as err:
            log_message(
                f"Attempt {attempt}/{retries} to fetch {SYMBOL} data failed: {err}",
                level="WARNING"
            )
            if attempt < retries:
                time.sleep(retry_delay)
            else:
                raise err
    return {}


def determine_market_status(meta: dict) -> str:
    """Determine whether ASX regular market is currently open."""
    try:
        now_ts = int(time.time())
        current_period = meta.get("currentTradingPeriod", {}).get("regular", {})
        start_ts = current_period.get("start")
        end_ts = current_period.get("end")
        if start_ts and end_ts:
            if start_ts <= now_ts <= end_ts:
                return "OPEN"
            elif now_ts < start_ts:
                return "PRE-MARKET"
            else:
                return "CLOSED"
    except Exception:
        pass
    return "UNKNOWN"


def record_price():
    """Perform one complete check and record cycle."""
    log_message(f"Checking live {SYMBOL} ({COMPANY_NAME}) stock price from ASX market...")
    try:
        meta = fetch_csl_data()
        
        price = meta.get("regularMarketPrice")
        if price is None:
            price = meta.get("fulldayPrice")
            
        if price is None:
            log_message(f"Market data received but price was unavailable for {SYMBOL}.", level="WARNING")
            return False

        prev_close = meta.get("previousClose") or meta.get("chartPreviousClose") or price
        day_high = meta.get("regularMarketDayHigh", 0.0)
        day_low = meta.get("regularMarketDayLow", 0.0)
        volume = meta.get("regularMarketVolume", 0)
        currency = meta.get("currency", "AUD")
        
        change = round(price - prev_close, 3)
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0
        
        market_state = determine_market_status(meta)
        
        # Formulate assessment commentary
        if change > 0:
            assessment = f"Gaining (+${change:.2f} / +{change_pct:.2f}%) vs previous close"
        elif change < 0:
            assessment = f"Easing (-${abs(change):.2f} / {change_pct:.2f}%) vs previous close"
        else:
            assessment = "Flat (unchanged vs previous close)"
            
        now_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
        
        # Append to CSV
        with open(CSV_FILE_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                now_local,
                now_utc,
                SYMBOL,
                COMPANY_NAME,
                f"{price:.2f}",
                f"{prev_close:.2f}",
                f"{change:+.2f}",
                f"{change_pct:+.2f}%",
                f"{day_low:.2f}" if day_low else "N/A",
                f"{day_high:.2f}" if day_high else "N/A",
                f"{volume:,}" if volume else "N/A",
                market_state,
                assessment
            ])
            
        # Append to simple text log
        with open(SIMPLE_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{now_local}] {SYMBOL}: ${price:.2f} {currency} | Change: {change:+.2f} ({change_pct:+.2f}%) | Day Range: [${day_low:.2f} - ${day_high:.2f}] | Vol: {volume:,} | Market: {market_state}\n")

        # Append to activity log
        log_message(
            f"Logged {SYMBOL} price: ${price:.2f} {currency} ({assessment}). "
            f"Range: [${day_low:.2f} - ${day_high:.2f}] | Vol: {volume:,} | Market: {market_state}"
        )
        return True
    except Exception as e:
        log_message(f"Error during price monitoring cycle: {e}", level="ERROR")
        return False


def save_pid():
    """Record current process ID for lifecycle management."""
    try:
        with open(PID_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        log_message(f"Could not write PID file: {e}", level="WARNING")


def remove_pid():
    """Remove PID file on shutdown."""
    if os.path.exists(PID_FILE_PATH):
        try:
            os.remove(PID_FILE_PATH)
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Ava - Autonomous CSL.AX Stock Monitoring AI Employee")
    parser.add_argument("--once", action="store_true", help="Run one check and exit immediately.")
    parser.add_argument("--interval", type=int, default=CHECK_INTERVAL_SECONDS, help="Check interval in seconds (default: 1800).")
    args = parser.parse_args()

    init_csv()

    if args.once:
        log_message("Starting single price verification cycle...")
        success = record_price()
        if success:
            log_message("Single verification cycle finished successfully.")
            sys.exit(0)
        else:
            log_message("Single verification cycle encountered an error.", level="ERROR")
            sys.exit(1)

    # Long-running autonomous daemon mode
    save_pid()
    atexit.register(remove_pid)

    def handle_signal(sig, frame):
        log_message(f"Received termination signal ({sig}). Ava is clocking out safely...")
        remove_pid()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_signal)

    log_message("=" * 60)
    log_message("Ava (AI Employee) is now ON DUTY.")
    log_message(f"Monitoring Target: {COMPANY_NAME} ({SYMBOL})")
    log_message(f"Check Frequency: Every {args.interval // 60} minutes ({args.interval}s)")
    log_message(f"Ledger File: {CSV_FILE_PATH}")
    log_message(f"Activity Log: {LOG_FILE_PATH}")
    log_message("=" * 60)

    while True:
        record_price()
        
        target_timestamp = time.time() + args.interval
        next_dt = datetime.fromtimestamp(target_timestamp).strftime("%H:%M:%S")
        log_message(f"Standing by. Next check scheduled for {next_dt} (in {args.interval // 60}m)...")
        
        # Resilient wall-clock wait with live status countdown
        while time.time() < target_timestamp:
            remaining = int(target_timestamp - time.time())
            mins, secs = divmod(remaining, 60)
            if sys.stdout is not None:
                try:
                    sys.stdout.write(f"\r[Ava Status] Active | Next check in {mins:02d}m {secs:02d}s (at {next_dt}) ... ")
                    sys.stdout.flush()
                except Exception:
                    pass
            time.sleep(1)
            
        if sys.stdout is not None:
            try:
                sys.stdout.write("\r" + " " * 80 + "\r")
                sys.stdout.flush()
            except Exception:
                pass


if __name__ == "__main__":
    main()
