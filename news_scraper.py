# news_scraper.py – גרסה מעודכנת לשלב 2

import feedparser
from config import NEWS_SOURCES
from urllib.parse import quote

def fetch_news_titles(symbol):
    headlines = []
    
    for source_name, source in NEWS_SOURCES.items():
        # דילוג על מקורות לא פעילים
        if not source.get("enabled", True):
            continue

        source_type = source.get("type")
        url = source.get("url")

        # מקור מסוג "news_article": RSS קבוע לכל השוק, נסנן לפי הופעת הסימבול בכותרת
        if source_type == "news_article" and url:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title.strip()
                if title and symbol.upper() in title.upper():
                    headlines.append((title, source_name))

        # תמיכה עתידית בסוגים אחרים (כמו "symbol_rss")
        # elif source_type == "symbol_rss" and url:
        #     formatted_url = url.format(symbol=quote(symbol))
        #     feed = feedparser.parse(formatted_url)
        #     for entry in feed.entries:
        #         title = entry.title.strip()
        #         if title:
        #             headlines.append((title, source_name))

        # מקורות מסוג Reddit יטופלו בקובץ reddit_scraper.py

    return headlines
