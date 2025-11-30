import asyncio
import sys
import json
import os
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Ensure project root on sys.path when executed as a script
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.sources.reddit import fetch_recent_reddit_titles  # noqa: E402
from app.sources.rss import fetch_recent_news_titles  # noqa: E402
from app.sources.social import fetch_recent_social_titles  # noqa: E402
from app.trending import TrendingDetector, load_companies  # noqa: E402


APP_ROOT = THIS_DIR
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
BASELINE_PATH = os.path.join(DATA_DIR, "baseline.json")
COMPANIES_CSV = os.path.join(DATA_DIR, "companies.csv")
HISTORY_PATH = os.path.join(DATA_DIR, "history.json")


app = FastAPI(title="Trending Businesses Tracker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


static_dir = os.path.join(PROJECT_ROOT, "static")
if os.path.isdir(static_dir):
    # Serve static assets under /static and explicitly serve index at /
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


detector: TrendingDetector | None = None
latest_scores: List[Dict] = []
all_trending_scores: List[Dict] = []  # Cache for all results
historical_data: List[Dict] = []


async def refresh_trending() -> None:
    global latest_scores, all_trending_scores, historical_data
    assert detector is not None

    reddit_titles = await fetch_recent_reddit_titles()
    news_titles = await fetch_recent_news_titles()
    social_titles = await fetch_recent_social_titles()
    titles = reddit_titles + news_titles + social_titles

    timestamp = datetime.now(tz=timezone.utc).isoformat()
    
    # Get all scores first
    # We need to modify score_titles slightly or just use the logic here if we want *all* of them
    # The current score_titles returns top 20. Let's do the scoring manually here to get ALL, 
    # then slice for latest_scores.
    
    # Aggregate counts over titles
    agg_counts: Dict[str, Tuple[int, str | None]] = {}
    for title in titles:
        counts = detector._count_mentions(title)
        for name, (c, alias_used) in counts.items():
            prev = agg_counts.get(name)
            if prev:
                agg_counts[name] = (prev[0] + c, prev[1] or alias_used)
            else:
                agg_counts[name] = (c, alias_used)

    # Compute lift over baseline and update EMA for ALL companies
    all_results: List[Dict] = []
    for company, _ in detector.company_patterns:
        recent = float(agg_counts.get(company.name, (0, None))[0])
        alias_used = agg_counts.get(company.name, (0, None))[1]
        baseline = float(detector.baseline.get(company.name, 0.0))
        
        # Trend score: lift = (recent + 1) / (baseline + 1)
        lift = (recent + 1.0) / (baseline + 1.0)

        # Update EMA baseline toward recent
        new_baseline = (1 - detector.alpha) * baseline + detector.alpha * recent
        detector.baseline[company.name] = new_baseline

        # Add to results if it has any activity or significant lift
        if recent > 0 or lift > 1.2:
            all_results.append(
                {
                    "name": company.name,
                    "ticker": company.ticker,
                    "recent_count": recent,
                    "baseline": baseline,
                    "lift": lift,
                    "timestamp": timestamp,
                    "alias_used": None,
                }
            )
            if alias_used:
                all_results[-1]["alias_used"] = detector._clean_alias(alias_used)

    # Sort by lift then by recent counts
    all_results.sort(key=lambda r: (r["lift"], r["recent_count"]), reverse=True)
    
    # Update globals
    all_trending_scores = all_results
    latest_scores = all_results[:20]

    # Add to historical data (using top 20 for history to keep it small)
    historical_entry = {
        "timestamp": timestamp,
        "companies": {score["name"]: {"lift": score["lift"], "recent_count": score["recent_count"]} for score in latest_scores}
    }
    historical_data.append(historical_entry)
    
    # Keep only last 100 data points to avoid unbounded growth
    if len(historical_data) > 100:
        historical_data.pop(0)

    # Persist baseline and history after each run
    with open(BASELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(detector.serialize_state(), f, ensure_ascii=False, indent=2)
    
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(historical_data, f, ensure_ascii=False, indent=2)


async def scheduler_loop(interval_seconds: int) -> None:
    # Run once at startup, then loop
    while True:
        try:
            await refresh_trending()
        except Exception as exc:  # noqa: BLE001
            # Keep the loop alive
            print(f"[scheduler] Error: {exc}")
        await asyncio.sleep(interval_seconds)


@app.on_event("startup")
async def on_startup() -> None:
    global detector, historical_data

    os.makedirs(DATA_DIR, exist_ok=True)

    companies = load_companies(COMPANIES_CSV)

    baseline: Dict[str, Dict] | None = None
    if os.path.exists(BASELINE_PATH):
        try:
            with open(BASELINE_PATH, "r", encoding="utf-8") as f:
                baseline = json.load(f)
        except Exception:  # noqa: BLE001
            baseline = None

    # Load existing historical data
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                historical_data = json.load(f)
        except Exception:  # noqa: BLE001
            historical_data = []

    detector = TrendingDetector(companies=companies, baseline_state=baseline)

    # Start background scheduler (default every 2 minutes for more data; configurable)
    interval_seconds = int(os.getenv("REFRESH_SECONDS", "120"))
    asyncio.create_task(scheduler_loop(interval_seconds=interval_seconds))


@app.get("/api/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/api/trending")
async def get_trending() -> JSONResponse:
    return JSONResponse(latest_scores)


@app.get("/api/trending/all")
async def get_all_trending() -> JSONResponse:
    # Return all trending companies for sectors view
    # Served from cache
    return JSONResponse(all_trending_scores)


@app.get("/")
async def index() -> FileResponse:
    index_path = os.path.join(static_dir, "index.html")
    return FileResponse(index_path)


@app.get("/api/top_ticker")
async def get_top_ticker() -> JSONResponse:
    # latest_scores is sorted by lift then recent_count desc
    for row in latest_scores:
        if row.get("ticker"):
            return JSONResponse(row)
    return JSONResponse({"detail": "no ticker found"}, status_code=404)


@app.get("/api/chart_data")
async def get_chart_data() -> JSONResponse:
    return JSONResponse(historical_data)


@app.get("/chart")
async def chart_page() -> FileResponse:
    chart_path = os.path.join(static_dir, "chart.html")
    return FileResponse(chart_path)


@app.get("/sectors")
async def sectors_page() -> FileResponse:
    sectors_path = os.path.join(static_dir, "sectors.html")
    return FileResponse(sectors_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


