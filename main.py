import os
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from news_scraper import fetch_news_titles

load_dotenv()

analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(symbol):
    print(f"\n🔍 מחשב סנטימנט עבור {symbol}...")

    headlines = fetch_news_titles(symbol)

    if not headlines:
        print("⚠️ לא נמצאו כותרות.")
        return

    scores = []
    for title in headlines:
        sentiment = analyzer.polarity_scores(title)["compound"]
        print(f"📰 '{title}' → {sentiment:.4f}")
        scores.append(sentiment)

    if scores:
        average_sentiment = sum(scores) / len(scores)
        print(f"📊 ממוצע סנטימנט עבור {symbol}: {average_sentiment:.3f}")
        print(f"🧠 {symbol}: ציון סנטימנט: {average_sentiment:.3f}")
        if average_sentiment >= 0.3:
            decision = "BUY"
        elif average_sentiment <= -0.3:
            decision = "SELL"
        else:
            decision = "HOLD"
        print(f"📊 {symbol}: החלטה: {decision}")
    else:
        print("⚠️ כל הכותרות נפסלו כספאם או לא רלוונטיות.")

def main():
    print("🚀 Sentibot v1.3.1 – מופעל ✅")
    tickers = ["AAPL", "TSLA", "NVDA", "MSFT", "META"]
    for symbol in tickers:
        analyze_sentiment(symbol)

if __name__ == "__main__":
    main()
