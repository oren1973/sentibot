import feedparser

def get_yahoo_news(symbol):
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    feed = feedparser.parse(url)
    titles = [entry["title"] for entry in feed["entries"]]
    return titles
