from __future__ import annotations

import asyncio
from typing import List

import httpx

# Expanded Reddit sources for more data
SUBREDDITS = [
    # Finance & Trading
    "stocks", "investing", "wallstreetbets", "SecurityAnalysis", "ValueInvesting",
    "financialindependence", "StockMarket", "options", "pennystocks", "dividends",
    "SecurityAnalysis", "ValueInvesting", "Bogleheads", "financialindependence",
    
    # Technology
    "technology", "programming", "MachineLearning", "artificial", "singularity",
    "Futurology", "gadgets", "Apple", "teslamotors", "nvidia", "AMD", "intel",
    "microsoft", "google", "cybersecurity", "startups", "entrepreneur",
    
    # Business & Economy
    "business", "Economics", "entrepreneur", "smallbusiness", "news",
    "economy", "Economics", "Marketing", "sales", "Entrepreneurship",
    
    # Crypto & Fintech
    "CryptoCurrency", "Bitcoin", "ethereum", "CryptoMarkets", "CoinBase",
    "defi", "NFT", "blockchain",
    
    # Gaming & Entertainment
    "gaming", "Games", "PS5", "xbox", "nintendo", "pcgaming", "movies",
    "entertainment", "netflix", "DisneyPlus", "streaming",
    
    # Energy & Climate
    "energy", "renewableenergy", "solar", "ClimateChange", "environment",
    "electricvehicles", "TeslaMotors", "climatechange",
    
    # Healthcare & Biotech
    "medicine", "biotech", "HealthInsurance", "Healthcare"
]


async def fetch_subreddit_titles(client: httpx.AsyncClient, subreddit: str, limit: int = 50) -> List[str]:
    url = f"https://www.reddit.com/r/{subreddit}/.rss"
    resp = await client.get(url, headers={"User-Agent": "trending-business/0.1"}, timeout=20.0)
    resp.raise_for_status()
    text = resp.text
    # Naive title extraction to keep deps small; feedparser is used for news
    titles: List[str] = []
    start_tag = "<title>"
    end_tag = "</title>"
    start = 0
    while True:
        i = text.find(start_tag, start)
        if i == -1:
            break
        j = text.find(end_tag, i)
        if j == -1:
            break
        title = text[i + len(start_tag) : j].strip()
        # Skip the feed header title which usually comes first
        if title and not title.lower().startswith("r/"):
            titles.append(title)
        start = j + len(end_tag)
        if len(titles) >= limit:
            break
    return titles


async def fetch_recent_reddit_titles() -> List[str]:
    async with httpx.AsyncClient() as client:
        tasks = [fetch_subreddit_titles(client, s) for s in SUBREDDITS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        titles: List[str] = []
        for res in results:
            if isinstance(res, Exception):
                continue
            titles.extend(res)
        return titles


