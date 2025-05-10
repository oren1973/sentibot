import time
import os
from datetime import datetime
import pandas as pd
from sentiment_analyzer import analyze_sentiment
from yahoo_scraper import get_yahoo_news
from investors_scraper import get_investors_news
from reddit_scraper import get_reddit_posts
from recommender import make_recommendation
from alpaca_trade_api.rest import REST

SYMBOLS = [
    "AAPL", "TSLA", "NVDA", "MSFT", "META",
    "PFE", "XOM", "JPM", "DIS", "WMT"
]

source_weights = {
    "yahoo": 1.0,
    "investors": 1.2,
    "reddit": 0.8
}

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
alpaca = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, base_url=ALPACA_BASE_URL)

# ודא שהקובץ נשמר ליד הקבצים
log_file = os.path.join(os.path.dirname(__file__), "learning_log.csv")

print("🚀 Sentibot v1.5 – מופעל ✅")

all_logs = []

for symbol in SYMBOLS:
    print(f"🔍 מחשב סנטימנט עבור {symbol}...")
    timestamp = datetime.now().isoformat()

    yahoo_articles = get_yahoo_news(symbol)
    investors_articles = get_investors_news(symbol)
    reddit_posts = get_reddit_posts(symbol)

    sentiment_by_source = {}
    mentions = {
        "yahoo": len(yahoo_articles),
        "investors": len(investors_articles),
        "reddit": len(reddit_posts)
    }

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

    total_weight = sum(source_weights.values())
    weighted_sum = sum(
        sentiment_by_source[src] * source_weights[src] for src in source_weights
    )
    avg_sentiment = weighted_sum / total_weight

    result = make_recommendation(avg_sentiment)
    print(f"📊 {symbol}: סנטימנט משוקלל סופי: {avg_sentiment:.3f}")
    print(f"📈 {symbol}: החלטה: {result['decision'].upper()}")

    try:
        price = alpaca.get_latest_trade(symbol).price
    except Exception as e:
        print(f"⚠️ שגיאה בשליפת מחיר עבור {symbol}: {e}")
        price = None

    log_entry = {
        "symbol": symbol,
        "timestamp": timestamp,
        "sentiment_yahoo": sentiment_by_source["yahoo"],
        "sentiment_investors": sentiment_by_source["investors"],
        "sentiment_reddit": sentiment_by_source["reddit"],
        "avg_sentiment": avg_sentiment,
        "num_mentions_total": sum(mentions.values()),
        "num_mentions_yahoo": mentions["yahoo"],
        "num_mentions_investors": mentions["investors"],
        "num_mentions_reddit": mentions["reddit"],
        "reddit_vs_yahoo_gap": sentiment_by_source["reddit"] - sentiment_by_source["yahoo"],
        "alpaca_price_now": price,
        "decision": result["decision"]
    }

    all_logs.append(log_entry)
    time.sleep(1)

df = pd.DataFrame(all_logs)
if os.path.exists(log_file):
    df.to_csv(log_file, mode="a", header=False, index=False)
else:
    df.to_csv(log_file, index=False)

print("✅ הסתיים בהצלחה.")
print(f"📄 נוצר קובץ log: {log_file}")
print("📂 קבצים בתיקייה:", os.listdir(os.path.dirname(__file__)))
