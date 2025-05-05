# news_scraper.py
import feedparser

def fetch_news_titles(symbol, limit=5):
    rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    feed = feedparser.parse(rss_url)

    headlines = []
    for entry in feed.entries[:limit]:
        headlines.append(entry.title)

    return headlines
