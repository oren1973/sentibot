import feedparser

RSS_FEEDS = [
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL,MSFT,GOOGL,AMZN,TSLA,META,NVDA,BRK-B,JPM,JNJ&region=US&lang=en-US"
]

def scan_market_headlines():
    headlines = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                if 'title' in entry:
                    headlines.append(entry.title)
        except Exception as e:
            print(f"⚠️ שגיאה בעת עיבוד הפיד: {e}")
    return headlines
