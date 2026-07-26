#!/usr/bin/env python3
"""
stock_alert.py

Monitors GEVO's stock price and sends a Discord alert when the current
price has dropped 1% or more from the previous trading day's closing
price. Meant to run as a single, stateless process on a schedule (e.g. a
GitHub Actions cron job every 30 minutes during market hours) - it does
not track state between runs.

Setup:
    1. Install dependencies:   pip install -r requirements.txt
    2. Create a Discord webhook (Server Settings -> Integrations ->
       Webhooks) and copy its URL.
    3. Set the DISCORD_WEBHOOK_URL environment variable. For local
       testing, copy .env.example to .env, fill in the real URL, then
       load it before running, e.g.:
         export $(grep -v '^#' .env | xargs)
         python stock_alert.py
       Never commit a real .env file - it's excluded via .gitignore.
    4. In GitHub Actions, set DISCORD_WEBHOOK_URL as a repository secret
       and pass it to the job via `env:`, e.g.:
         env:
           DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}

Environment variables:
    DISCORD_WEBHOOK_URL   Required. Discord webhook URL to post alerts to.
"""

import os
import sys
from datetime import datetime, timezone

import requests
import yfinance as yf

TICKER = "GEVO"
DROP_THRESHOLD_PERCENT = 5.0


def log(message: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] {message}", flush=True)


def get_price_data(ticker_symbol: str):
    """Return (current_price, previous_close) for ticker_symbol, or (None, None) on failure."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        fast_info = ticker.fast_info

        current_price = fast_info.get("lastPrice") or fast_info.get("last_price")
        previous_close = fast_info.get("previousClose") or fast_info.get("previous_close")

        if current_price is None or previous_close is None:
            log(
                f"ERROR: yfinance returned incomplete data for {ticker_symbol} "
                f"(current={current_price}, previous_close={previous_close})"
            )
            return None, None

        if previous_close <= 0:
            log(f"ERROR: invalid previous close ({previous_close}) for {ticker_symbol}")
            return None, None

        return float(current_price), float(previous_close)

    except Exception as exc:
        log(f"ERROR: failed to fetch data for {ticker_symbol}: {exc}")
        return None, None


def send_discord_alert(webhook_url: str, message: str) -> bool:
    try:
        response = requests.post(webhook_url, json={"content": message}, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        log(f"ERROR: failed to send Discord alert: {exc}")
        return False


def main() -> int:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        log("ERROR: DISCORD_WEBHOOK_URL environment variable is not set. Skipping run.")
        return 1

    current_price, previous_close = get_price_data(TICKER)
    if current_price is None or previous_close is None:
        log(f"{TICKER}: no valid price data this run, skipping.")
        return 0

    percent_change = ((current_price - previous_close) / previous_close) * 100

    log(
        f"{TICKER}: previous close=${previous_close:.2f}, current=${current_price:.2f}, "
        f"change={percent_change:+.2f}%"
    )

    if percent_change <= -DROP_THRESHOLD_PERCENT:
        message = (
            f"GEVO Alert: Down {abs(percent_change):.1f}% today "
            f"(${previous_close:.2f} to ${current_price:.2f})"
        )
        if send_discord_alert(webhook_url, message):
            log(f"Alert sent: {message}")
        else:
            log(f"Alert threshold met but failed to notify Discord: {message}")
    else:
        log(f"{TICKER}: no alert, drop threshold ({DROP_THRESHOLD_PERCENT}%) not met.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
