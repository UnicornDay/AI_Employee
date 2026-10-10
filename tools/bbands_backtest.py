# -*- coding: utf-8 -*-
"""Ponytail Bollinger Bands Backtest Script

20-day Bollinger Bands strategy (2 standard deviations, long-only, buy when price crosses below lower band, sell when price crosses above upper band) on historical asset prices using yfinance.
"""

import argparse
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf


def run_backtest(
    ticker: str = "AAPL",
    period: str = "5y",
    initial_cash: float = 10_000.0,
    window: int = 20,
    num_std_dev: float = 2.0,
    save_chart: str = None,
    show_plot: bool = True,
):
    print(f"Downloading data for {ticker} (period: {period})...")
    df = yf.download(ticker, period=period, auto_adjust=True)
    if df.empty:
        print(f"Error: No data found for ticker '{ticker}' with period '{period}'.", file=sys.stderr)
        sys.exit(1)

    close = df["Close"].squeeze()
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    # Calculate Bollinger Bands (20-day period, 2 standard deviations)
    sma = close.rolling(window=window).mean()
    std_dev = close.rolling(window=window).std()

    upper_band = sma + (std_dev * num_std_dev)
    lower_band = sma - (std_dev * num_std_dev)

    # Generate signals based on Bollinger Bands
    signal = pd.Series(index=close.index, dtype=str)
    # Buy when price crosses below the lower band (oversold)
    signal[close < lower_band] = "BUY"
    # Sell when price crosses above the upper band (overbought)
    signal[close > upper_band] = "SELL"
    signal = signal.fillna("HOLD")

    position = (
        signal
        .map({"BUY": 1, "SELL": 0})
        .ffill()
        .fillna(0)
        .shift(1)
        .fillna(0)
    )

    pos_change = position.diff().fillna(position)

    ret = close.pct_change().fillna(0)
    equity = initial_cash * (1 + position * ret).cumprod()
    bh_equity = initial_cash * (1 + ret).cumprod()

    tx_log = pd.DataFrame(
        {
            "Date": close.index,
            "Action": np.where(pos_change > 0, "BUY", np.where(pos_change < 0, "SELL", "")),
            "Price": close.values,
            "SMA": sma.values,
            "Upper Band": upper_band.values,
            "Lower Band": lower_band.values,
            "Position": position.values,
            "Portfolio Value": equity.values,
        }
    )
    # Filter out 'HOLD' actions for display and ensure we only have actual trades
    tx_log = tx_log[tx_log["Action"] != ""].reset_index(drop=True)

    trades = len(tx_log)
    total_return = equity.iloc[-1] / initial_cash - 1
    bh_return = bh_equity.iloc[-1] / initial_cash - 1
    max_dd = (equity / equity.cummax() - 1).min()

    # Calculate Sharpe Ratio
    daily_returns = equity.pct_change().dropna()
    risk_free_rate_annual = 0.02
    risk_free_rate_daily = (1 + risk_free_rate_annual) ** (1 / 252) - 1
    excess_returns = daily_returns - risk_free_rate_daily
    strategy_volatility = excess_returns.std()
    if strategy_volatility > 0 and not np.isnan(strategy_volatility):
        sharpe_ratio = (excess_returns.mean() / strategy_volatility) * np.sqrt(252)
    else:
        sharpe_ratio = 0.0

    print(f"\n==================== Bollinger Bands Backtest Summary: {ticker} ====================")
    print(f"Period: {close.index[0].date()} -> {close.index[-1].date()}")
    print(f"Trades: {trades}")
    print(f"Strategy return: {total_return:.2%}")
    print(f"Buy & hold return: {bh_return:.2%}")
    print(f"Max drawdown: {max_dd:.2%}")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"Final equity: ${equity.iloc[-1]:,.2f}")

    print("\nTransaction log:")
    if tx_log.empty:
        print("No trades triggered during this period.")
    else:
        print(tx_log.to_string(index=False))

    # Plotting
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(close.index, close, color="#333", linewidth=1, label=f"{ticker} Close")
    ax.plot(close.index, sma, color="blue", linewidth=1, label=f"SMA {window}")
    ax.plot(close.index, upper_band, color="green", linestyle="--", linewidth=1, label=f"Upper Band ({num_std_dev} StdDev)")
    ax.plot(close.index, lower_band, color="red", linestyle="--", linewidth=1, label=f"Lower Band ({num_std_dev} StdDev)")
    buys = tx_log[tx_log["Action"] == "BUY"]
    sells = tx_log[tx_log["Action"] == "SELL"]
    ax.scatter(
        buys["Date"],
        buys["Price"],
        marker="^",
        s=90,
        color="#2ecc71",
        label="Buy",
        zorder=3,
    )
    ax.scatter(
        sells["Date"],
        sells["Price"],
        marker="v",
        s=90,
        color="#e74c3c",
        label="Sell",
        zorder=3,
    )
    ax.set_title(f"{ticker} Bollinger Bands ({window}-day, {num_std_dev} StdDev) Backtest")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price ($)")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save_chart:
        fig.savefig(save_chart, dpi=300)
        print(f"\nChart saved to: {save_chart}")

    if show_plot:
        plt.show()

    return trades, equity.iloc[-1]


def main():
    parser = argparse.ArgumentParser(description="Ponytail Bollinger Bands Backtest")
    parser.add_argument("pos_ticker", nargs="?", default=None, help="Stock ticker symbol (e.g. AAPL)")
    parser.add_argument("pos_period", nargs="?", default=None, help="Historical period (e.g. 5y, 1y, 6mo)")
    parser.add_argument("--ticker", "-t", default=None, help="Stock ticker symbol")
    parser.add_argument("--period", "-p", default=None, help="Historical period (e.g. 5y, 1y, 6mo)")
    parser.add_argument("--cash", type=float, default=10_000.0, help="Initial cash balance (default: 10000)")
    parser.add_argument("--window", "-w", type=int, default=20, help="SMA window (default: 20)")
    parser.add_argument("--std", type=float, default=2.0, help="Standard deviation multiplier (default: 2)")
    parser.add_argument("--save-chart", "-s", default=None, help="File path to save the chart image")
    parser.add_argument("--no-show", action="store_true", help="Do not display interactive plot window")

    args = parser.parse_args()

    ticker = (args.ticker or args.pos_ticker or "AAPL").upper()
    period = args.period or args.pos_period or "5y"

    trades, final_equity = run_backtest(
        ticker=ticker,
        period=period,
        initial_cash=args.cash,
        window=args.window,
        num_std_dev=args.std,
        save_chart=args.save_chart,
        show_plot=not args.no_show,
    )

    assert trades >= 0 and final_equity > 0


if __name__ == "__main__":
    main()
