import feedparser

def get_investors_news(symbol):
    """
    מקבל סימבול (למשל AAPL) ומחזיר רשימת כותרות חדשות מ-Investors.com (IBD)
    """
    url = f"https://research.investors.com/rss.aspx?kw={symbol}"
    feed = feedparser.parse(url)
    titles = [entry["title"] for entry in feed["entries"]]
    return titles
