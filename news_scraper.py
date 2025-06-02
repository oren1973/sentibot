import feedparser
from config import NEWS_SOURCES

def fetch_news_titles(symbol):
    headlines = []
    seen_titles = set()

    for source_name, source_info in NEWS_SOURCES.items():
        if not source_info.get("enabled", False):
            continue

        rss_url = source_info.get("rss")
        if not rss_url:
            print(f"⚠️ מקור {source_name} אינו מכיל URL של RSS – מדלג.")
            continue

        try:
            rss_url = rss_url.replace("{symbol}", symbol)
            feed = feedparser.parse(rss_url)

            if feed.bozo:
                print(f"⚠️ שגיאה בהבאת מידע מ־{source_name} עבור {symbol}: {feed.bozo_exception}")
                continue

            for entry in feed.entries[:5]:
                title = entry.get("title", "").strip()
                if len(title) >= 10 and title not in seen_titles:
                    headlines.append((title, source_name))
                    seen_titles.add(title)

        except Exception as e:
            print(f"⚠️ חריגה בעת עיבוד מקור {source_name} עבור {symbol}: {e}")

    if headlines:
        print(f"\n🔎 {symbol} – Headlines:")
        for h in headlines:
            print(f"- {h[0]} [{h[1]}]")
    else:
        print(f"\n🔎 {symbol} – No headlines found.")

    return headlines
