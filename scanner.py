import feedparser

def scan_market_and_generate_report():
    rss_url = "https://www.marketwatch.com/rss/topstories"  # פיד RSS עדכני ואמין
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        print("⚠️ לא נמצאו כותרות בפיד MarketWatch.")
        return []

    headlines = []
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        if title:
            headlines.append(title)

    return headlines
