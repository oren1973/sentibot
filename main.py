# main.py

from scanner import scan_market_headlines
from sentiment import analyze_sentiment
from trader import execute_trades

def main():
    print("✅ Sentibot starting...")

    # שלב 1: סריקה
    headlines = scan_market_headlines()
    print(f"DEBUG | headlines found: {len(headlines)}")

    # שלב 2: ניתוח רגשות
    sentiment_data = []
    for headline in headlines:
        sentiment = analyze_sentiment(headline)
        sentiment_data.append({
            "headline": headline,
            "sentiment": sentiment
        })

    # שלב 3: סימולציית מסחר
    execute_trades(sentiment_data)

if __name__ == "__main__":
    main()
