# Trending Businesses Tracker
<img width="1470" height="956" alt="Screenshot 2025-11-17 at 11 52 30 PM" src="https://github.com/user-attachments/assets/e6a854a5-003c-45e0-9687-c976841570a6" />

<img width="1470" height="956" alt="Screenshot 2025-11-17 at 11 51 33 PM" src="https://github.com/user-attachments/assets/c740b3ca-d93b-4c2a-8c12-d38ef2ad00e3" />

Backend: FastAPI (Python)
Frontend: Static HTML + JS

This app collects recent post titles from selected Reddit subreddits (via RSS) and business news RSS feeds, detects sudden increases in company mentions, and shows the current trending companies.

## Website link via Vercel 
https://trending-business.vercel.app/

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

