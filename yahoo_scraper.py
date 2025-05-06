import feedparser
from sentiment import clean_text

def fetch_yahoo_titles(stock_symbol):
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={stock_symbol}&region=US&lang=en-US"
    try:
        feed = feedparser.parse(url)
        if feed.bozo:
            raise Exception("Parsing failed or feed invalid")
        titles = []
        for entry in feed.entries:
            title = clean_text(entry.title)
            if title:
                titles.append(title)
        return titles[:10]
    except Exception as e:
        print(f"⚠️ שגיאה בשליפת כותרות Yahoo עבור {stock_symbol}: {e}")
        return []
