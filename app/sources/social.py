from __future__ import annotations

import asyncio
from typing import List

import httpx

# Additional social media and financial sources (RSS-based to avoid API keys)
SOCIAL_FEEDS = [
    # Financial Twitter alternatives and RSS feeds
    "https://feeds.feedburner.com/InvestorPlace",  # InvestorPlace
    "https://feeds.feedburner.com/benzinga",  # Benzinga
    "https://feeds.feedburner.com/InvestingChannel",  # Investing Channel
    "https://feeds.feedburner.com/SeekingAlpha",  # Seeking Alpha
    "https://feeds.feedburner.com/StockNews",  # Stock News
    
    # Reddit alternative sources via RSS
    "https://www.reddit.com/r/SecurityAnalysis/hot/.rss",
    "https://www.reddit.com/r/ValueInvesting/hot/.rss", 
    "https://www.reddit.com/r/financialindependence/hot/.rss",
    "https://www.reddit.com/r/SecurityAnalysis/new/.rss",
    "https://www.reddit.com/r/investing/hot/.rss",
    
    # Hacker News (lots of tech company discussion)
    "https://feeds.feedburner.com/ycombinator",  # Hacker News
    
    # Google News searches for specific terms
    "https://news.google.com/rss/search?q=stocks&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=earnings&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=tech+stocks&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=cryptocurrency&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=IPO&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=merger+acquisition&hl=en-US&gl=US&ceid=US:en",
]


async def fetch_social_feed_titles(client: httpx.AsyncClient, url: str) -> List[str]:
    """Fetch titles from RSS feeds"""
    try:
        resp = await client.get(url, headers={"User-Agent": "trending-business/0.1"}, timeout=15.0)
        resp.raise_for_status()
        text = resp.text
        
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
            
            # Clean up common RSS artifacts
            if title and not any(skip in title.lower() for skip in [
                "rss", "feed", "google news", "reddit:", "comments"
            ]):
                # Remove HTML entities
                title = title.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                title = title.replace("&quot;", '"').replace("&#39;", "'")
                titles.append(title)
            
            start = j + len(end_tag)
            if len(titles) >= 30:  # Limit per feed
                break
                
        return titles
    except Exception:
        return []


async def fetch_recent_social_titles() -> List[str]:
    """Fetch titles from all social and financial feeds"""
    async with httpx.AsyncClient() as client:
        tasks = [fetch_social_feed_titles(client, url) for url in SOCIAL_FEEDS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        titles: List[str] = []
        for res in results:
            if isinstance(res, Exception):
                continue
            titles.extend(res)
        
        return titles
