import feedparser
from config import NEWS_SOURCES

def fetch_news_titles(symbol):
    headlines = []

    for source_name, source in NEWS_SOURCES.items():
        if not source.get("enabled", True):
            continue

        url_template = source.get("rss")
        if not url_template:
            print(f"⚠️ No RSS URL for {source_name}")
            continue

        try:
            rss_url = url_template.format(symbol=symbol)
            print(f"📡 Fetching from {source_name}: {rss_url}")

            feed = feedparser.parse(rss_url)

            if not feed.entries:
                print(f"  ⚠️ No entries for {symbol} from {source_name}")
                continue

            for entry in feed.entries:
                title = entry.get("title", "").strip()
                if title:
                    headlines.append((title, source_name))
                    print(f"    ✅ {title}")
                else:
                    print(f"    ⚠️ Empty title from {source_name}")

        except Exception as e:
            print(f"❌ Error fetching from {source_name}: {e}")

    return headlines
