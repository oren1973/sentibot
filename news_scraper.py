# news_scraper.py – גרסה מעודכנת לשימוש בשמות חברות
import feedparser
from config import NEWS_SOURCES
from urllib.parse import quote
from symbol_names import SYMBOL_TO_NAME

def fetch_news_titles(symbol):
    headlines = []

    # נשתמש בשם החברה לצורך החיפוש, אם קיים
    search_term = SYMBOL_TO_NAME.get(symbol, symbol)
    search_term_encoded = quote(search_term)

    for source_name, source in NEWS_SOURCES.items():
        if not source.get("enabled", True):
            continue

        url_template = source.get("rss")
        if not url_template:
            continue

        # נחליף {symbol} בשם החברה (מוצפן ב-URL)
        rss_url = url_template.format(symbol=search_term_encoded)
        feed = feedparser.parse(rss_url)

        for entry in feed.entries:
            title = entry.title.strip()
            if title:
                headlines.append((title, source_name))

    return headlines
