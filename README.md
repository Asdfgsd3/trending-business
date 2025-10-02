# Trending Businesses Tracker

Backend: FastAPI (Python)
Frontend: Static HTML + JS

This app collects recent post titles from selected Reddit subreddits (via RSS) and business news RSS feeds, detects sudden increases in company mentions, and shows the current trending companies.

## Quickstart

1. Create and activate a virtualenv (recommended)
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the server:

```bash
uvicorn app.main:app --reload
```

4. Open the UI: http://localhost:8000/

## How it works

- Sources: Reddit subreddits via RSS (no API key) and a few news RSS feeds.
- Company matching: simple matching by company names, aliases, and tickers (with optional `$TICKER`).
- Trending detection: compares the recent mention count against an exponentially weighted baseline (EMA). Results refresh on a background schedule.

## Customize

- Edit `data/companies.csv` to add or adjust companies, tickers, and aliases.
- Change sources in `app/sources/reddit.py` and `app/sources/rss.py`.
- Tweak scoring and thresholds in `app/trending.py`.

## Endpoints

- `GET /api/health` — service health
- `GET /api/trending` — current trending scores

## Notes

- This project uses only public RSS endpoints to avoid API keys. You can integrate authenticated APIs later (e.g., PRAW for Reddit, NewsAPI, etc.).

