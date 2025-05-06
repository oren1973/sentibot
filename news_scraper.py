# news_scraper.py – גרסה חדשה עם source + published_at
import feedparser
from datetime import datetime

JUNK_PHRASES = [
    "Entertainment",
    "New on Yahoo",
    "Mag 7 earnings show",
    "The Zacks Analyst Blog",
    "People Also Watch",
    "Compare To:"
]

def is_relevant(title):
    for junk in JUNK_PHRASES:
        if junk.lower() in title.lower():
            return False
    return True

def fetch_news_items(symbol, limit=10):
    rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    feed = feedparser.parse(rss_url)

    items = []
    for entry in feed.entries:
        title = entry.title.strip()
        if is_relevant(title):
            item = {
                "title": title,
                "source": "Yahoo Finance",
                "published_at": datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
            }
            items.append(item)
        if len(items) >= limit:
            break

    return items
