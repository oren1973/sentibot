import feedparser

def get_investors_news(ticker):
    base_url = f"https://www.investors.com/feed/stock/{ticker.lower()}/"
    try:
        feed = feedparser.parse(base_url)
        headlines = [entry.title for entry in feed.entries]
        return headlines
    except Exception as e:
        print(f"❌ שגיאה בהבאת חדשות מ-Investors עבור {ticker}: {e}")
        return []
