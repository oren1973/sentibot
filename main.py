import time
from sentiment_analyzer import analyze_sentiment
from yahoo_scraper import get_yahoo_news
from investors_scraper import get_investors_news
from recommender import make_recommendation

SYMBOLS = [
    "AAPL", "TSLA", "NVDA", "MSFT", "META",
    "PFE", "XOM", "JPM", "DIS", "WMT"
]

print("🚀 Sentibot v1.4.1 – מופעל ✅")

for symbol in SYMBOLS:
    print(f"🔍 מחשב סנטימנט עבור {symbol}...")

    # קבלת חדשות משני המקורות
    yahoo_articles = get_yahoo_news(symbol)
    investors_articles = get_investors_news(symbol)

    # שילוב כל הכתבות
    all_articles = yahoo_articles + investors_articles

    if not all_articles:
        print(f"⚠️ לא נמצאו כתבות עבור {symbol}")
        continue

    # ניתוח סנטימנט לכל כתבה
    sentiments = []
    for article in all_articles:
        sentiment = analyze_sentiment(article)
        sentiments.append(sentiment)
        print(f"📰 '{article}' → {sentiment:.4f}")

    # חישוב ממוצע סנטימנט
    avg_sentiment = sum(sentiments) / len(sentiments)
    decision = make_recommendation(all_articles)

    print(f"📊 {symbol}: סנטימנט משוקלל: {avg_sentiment:.3f}")
    print(f"📊 {symbol}: החלטה: {decision.upper()}")

    time.sleep(1)  # השהייה קטנה בין מניות

print("✅ הסתיים בהצלחה.")
