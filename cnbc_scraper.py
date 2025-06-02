import feedparser

CNBC_RSS_URL = "https://www.cnbc.com/id/100003114/device/rss/rss.html"

def get_cnbc_titles(symbol):
    symbol = symbol.upper()
    headlines = []

    try:
        feed = feedparser.parse(CNBC_RSS_URL)

        if feed.bozo:
            print(f"⚠️ שגיאה ב־CNBC RSS: {feed.bozo_exception}")
            return []

        for entry in feed.entries[:20]:
            title = entry.get("title", "").strip()
            if symbol in title:
                headlines.append((title, "CNBC"))

    except Exception as e:
        print(f"⚠️ שגיאה ב־get_cnbc_titles({symbol}): {e}")

    return headlines
