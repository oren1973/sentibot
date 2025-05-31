import feedparser
from config import NEWS_SOURCES
from urllib.parse import quote

def fetch_news_titles(symbol):
    headlines = []
    
    for source_name, source in NEWS_SOURCES.items():
        if not source["enabled"]:
            continue

        url_template = source["rss"]
        rss_url = url_template.format(symbol=quote(symbol))
        feed = feedparser.parse(rss_url)

        for entry in feed.entries:
            title = entry.title.strip()
            if title:
                headlines.append((title, source_name))

    return headlines
