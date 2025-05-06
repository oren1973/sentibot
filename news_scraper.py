# news_scraper.py – שלב 2.3: הרחבת מקורות (Yahoo + MarketWatch + Reuters)

import feedparser

JUNK_PHRASES = [
    "Entertainment", "New on Yahoo", "The Zacks Analyst Blog",
    "People Also Watch", "Compare To:", "Video", "Press Release"
]

SOURCES = {
    "Yahoo": "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US",
    "MarketWatch": "https://www.marketwatch.com/rss/headlines.asp?channel=stocks",
    "Reuters": "http://feeds.reuters.com/reuters/businessNews"
}

def is_relevant(title):
    for junk in JUNK_PHRASES:
        if junk.lower() in title.lower():
            return False
    return True

def fetch_news_titles(symbol, limit=10):
    all_headlines = []

    for source_name, url_template in SOURCES.items():
        url = url_template.format(symbol=symbol)
        feed = feedparser.parse(url)

        for entry in feed.entries:
            title = entry.title.strip()
            if is_relevant(title):
                all_headlines.append(f"{title} [{source_name}]")
            if len(all_headlines) >= limit:
                break

        if len(all_headlines) >= limit:
            break

    return all_headlines
