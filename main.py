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

source_weights = {
    "yahoo": 1.0,
    "investors": 1.2,
    "reddit": 0.8
}

print("🚀 Sentibot v1.5 – מופעל ✅")

for symbol in SYMBOLS:
    print(f"🔍 מחשב סנטימנט עבור {symbol}...")

    # קבלת תוכן ממקורות שונים
    yahoo_articles = get_yahoo_news(symbol)
    investors_articles = get_investors_news(symbol)
    reddit_posts = get_reddit_posts(symbol)

    sentiment_by_source = {}

    for source_name, texts in {
        "yahoo": yahoo_articles,
        "investors": investors_articles,
        "reddit": reddit_posts
    }.items():
        if texts:
            sentiments = [analyze_sentiment(text) for text in texts]
            avg = sum(sentiments) / len(sentiments)
            sentiment_by_source[source_name] = avg
            print(f"📊 {symbol}: ממוצע {source_name}: {avg:.3f}")
        else:
            sentiment_by_source[source_name] = 0.0
            print(f"⚠️ {symbol}: אין נתונים מ־{source_name}")

    # ממוצע סנטימנט משוקלל
    total_weight = sum(source_weights.values())
    weighted_sum = sum(
        sentiment_by_source[src] * source_weights[src] for src in source_weights
    )
    avg_sentiment = weighted_sum / total_weight

    result = make_recommendation(avg_sentiment)

    print(f"📊 {symbol}: סנטימנט משוקלל סופי: {avg_sentiment:.3f}")
    print(f"📈 {symbol}: החלטה: {result['decision'].upper()}")

    time.sleep(1)

print("✅ הסתיים בהצלחה.")
