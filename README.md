# GEVO Stock Alert Bot

Monitors GEVO's stock price during market hours and posts a Discord alert
when the price has dropped 5% or more from the previous trading day's
closing price.

## How it works

- `stock_alert.py` uses the [`yfinance`](https://pypi.org/project/yfinance/)
  library to pull GEVO's current price and the previous close.
- It calculates the percent change between the two.
- If the drop is 5% or more, it posts a message to a Discord channel via
  webhook, formatted like:

  ```
  GEVO Alert: Down 12.0% today ($1.85 to $1.62)
  ```

- Every run — whether or not the threshold is met — logs a timestamped
  line to stdout, so results are visible in the GitHub Actions run
  history even when nothing happens.
- If `yfinance` fails to return usable data, the script logs the error
  and exits cleanly instead of crashing.
- The script is stateless: it doesn't track anything between runs, so
  each scheduled run is a fresh, independent check.

## Automated schedule

`.github/workflows/gevo-stock-alert.yml` runs the script automatically
every 30 minutes during US market hours (13:00–21:30 UTC, Monday–Friday)
via GitHub Actions, and can also be triggered manually from the Actions
tab (`workflow_dispatch`).

## Secrets handling

The Discord webhook URL is never hardcoded. It's read from the
`DISCORD_WEBHOOK_URL` environment variable:

- **Locally:** copy `.env.example` to `.env`, fill in your real webhook
  URL, then load it before running:
  ```bash
  export $(grep -v '^#' .env | xargs)
  python stock_alert.py
  ```
  `.env` is excluded via `.gitignore` and is never committed.
- **In GitHub Actions:** set `DISCORD_WEBHOOK_URL` as a repository secret
  (Settings → Secrets and variables → Actions), which the workflow
  passes into the job via `env:`.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a Discord webhook (Server Settings → Integrations → Webhooks)
   and copy its URL.
3. Set `DISCORD_WEBHOOK_URL` as described above (locally via `.env`, or
   as a GitHub Actions repository secret for the scheduled workflow).
4. Run it directly with `python stock_alert.py`, or let the GitHub
   Actions workflow run it on schedule.

## Files

| File | Purpose |
|---|---|
| `stock_alert.py` | Main script: fetches price data, checks the threshold, sends alerts |
| `requirements.txt` | Python dependencies (`yfinance`, `requests`) |
| `.env.example` | Template for local `DISCORD_WEBHOOK_URL` setup |
| `.gitignore` | Excludes `.env` and other local secrets from version control |
| `.github/workflows/gevo-stock-alert.yml` | Scheduled GitHub Actions workflow |
