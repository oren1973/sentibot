import feedparser
import re
from sentiment import analyze_sentiment

def clean_text(text):
    if not text:
        return ""
    # הסרת HTML ותווים מיותרים
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fetch_investors_news(symbol):
    url = f"https://www.investors.com/category/etfs-and-funds/{symbol.lower()}/feed/"
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries:
            title = clean_text(entry.get('title', ''))
            if title and symbol.upper() in title.upper():
                score = analyze_sentiment(title)
                articles.append((title, score))
        return articles
    except Exception as e:
        print(f"שגיאה בשליפת חדשות מ-Investors.com עבור {symbol}: {e}")
        return []

# דוגמה לבדיקה ידנית
if __name__ == "__main__":
    symbol = "AAPL"
    news = fetch_investors_news(symbol)
    for title, score in news:
        print(f"📰 {title} → {score:.4f}")
