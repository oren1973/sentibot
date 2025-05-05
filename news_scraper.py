# news_scraper.py – גרסה עם סינון כותרות לא רלוונטיות (junk filtering)

import feedparser

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

def fetch_news_titles(symbol, limit=10):
    rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    feed = feedparser.parse(rss_url)

    headlines = []
    for entry in feed.entries:
        title = entry.title.strip()
        if is_relevant(title):
            headlines.append(title)
        if len(headlines) >= limit:
            break

    return headlines
