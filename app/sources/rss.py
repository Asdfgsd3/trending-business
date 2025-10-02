from __future__ import annotations

from typing import List

import feedparser

NEWS_FEEDS = [
    # Financial News
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",  # WSJ Markets
    "https://www.cnbc.com/id/10001147/device/rss/rss.html",  # CNBC Top News
    "https://www.cnbc.com/id/15839135/device/rss/rss.html",  # CNBC Technology
    "https://www.cnbc.com/id/10000664/device/rss/rss.html",  # CNBC Business
    "https://feeds.bloomberg.com/markets/news.rss",  # Bloomberg Markets
    "https://feeds.reuters.com/reuters/businessNews",  # Reuters Business
    "https://feeds.marketwatch.com/marketwatch/topstories/",  # MarketWatch
    "https://finance.yahoo.com/news/rssindex",  # Yahoo Finance
    
    # Technology News
    "https://www.theverge.com/rss/index.xml",  # The Verge
    "https://techcrunch.com/feed/",  # TechCrunch
    "https://feeds.arstechnica.com/arstechnica/index/",  # Ars Technica
    "https://www.wired.com/feed/rss",  # Wired
    "https://feeds.feedburner.com/venturebeat/SZYF",  # VentureBeat
    "https://rss.cnn.com/rss/cnn_tech.rss",  # CNN Tech
    "https://feeds.feedburner.com/Mashable",  # Mashable
    
    # Business & Economy
    "https://feeds.fortune.com/fortune/headlines",  # Fortune
    "https://feeds.feedburner.com/entrepreneur/latest",  # Entrepreneur
    "https://feeds.inc.com/home/updates.rss",  # Inc.com
    "https://feeds.feedburner.com/fastcompany/headlines",  # Fast Company
    "https://feeds.hbr.org/harvardbusiness",  # Harvard Business Review
    
    # General News with Business Content
    "https://rss.cnn.com/rss/cnn_topstories.rss",  # CNN Top Stories
    "https://feeds.nbcnews.com/nbcnews/public/news",  # NBC News
    "https://feeds.npr.org/1001/rss.xml",  # NPR News
    "https://feeds.bbci.co.uk/news/business/rss.xml",  # BBC Business
    
    # Industry Specific
    "https://feeds.feedburner.com/zerohedge/feed",  # Zero Hedge (Finance)
    "https://feeds.feedburner.com/seekingalpha/feed",  # Seeking Alpha
    "https://feeds.feedburner.com/fool/free",  # Motley Fool
]


async def fetch_recent_news_titles() -> List[str]:
    titles: List[str] = []
    for url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:50]:
                title = getattr(entry, "title", "").strip()
                if title:
                    titles.append(title)
        except Exception:  # noqa: BLE001
            continue
    return titles


