# main.py
import time
from sentiment_analyzer import analyze_sentiment
from yahoo_scraper import get_yahoo_news
from investors_scraper import get_investors_news
from reddit_scraper import get_reddit_posts
from recommender import make_recommendation

SYMBOLS = [
    "AAPL", "TSLA", "NVDA", "MSFT", "META",
    "PFE", "XOM", "JPM", "DIS", "WMT"
]

print("🚀 Sentibot v1.5 – מופעל ✅")

for symbol in SYMBOLS:
    print(f"🔍 מחשב סנטימנט עבור {symbol}...")

    # קבלת תוכן ממקורות שונים
    yahoo_articles = get_yahoo_news(symbol)
    investors_articles = get_investors_news(symbol)
    reddit_posts = get_reddit_posts(symbol)

    all_articles = yahoo_articles + investors_articles + reddit_posts

    if not all_articles:
        print(f"⚠️ לא נמצאו כתבות או פוסטים עבור {symbol}")
        continue

    # ניתוח סנטימנט
    sentiments = []
    for text in all_articles:
        score = analyze_sentiment(text)
        sentiments.append(score)
        print(f"📰 '{text[:80]}...' → {score:.4f}")

    avg_sentiment = sum(sentiments) / len(sentiments)
    result = make_recommendation(avg_sentiment)

    print(f"📊 {symbol}: סנטימנט משוקלל: {avg_sentiment:.3f}")
    print(f"📊 {symbol}: החלטה: {result['decision'].upper()}")

    time.sleep(1)

print("✅ הסתיים בהצלחה.")
