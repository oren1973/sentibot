import os
import requests
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

nltk.download("vader_lexicon")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
if not FINNHUB_API_KEY:
    raise ValueError("Missing FINNHUB_API_KEY environment variable.")

# רשימת מניות לדוגמה (בשלב הבא נחליף ב-S&P 500 אמיתי)
tickers = ["TSLA", "NVDA", "AAPL", "MSFT", "GME", "META", "AMZN"]

analyzer = SentimentIntensityAnalyzer()

def get_news_sentiment(symbol):
    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2024-04-25&to=2024-05-01&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        return None

    news_items = response.json()
    scores = []
    for item in news_items:
        headline = item.get("headline", "")
        score = analyzer.polarity_scores(headline)["compound"]
        scores.append(score)

    if scores:
        return sum(scores) / len(scores)
    return 0

results = []
for symbol in tickers:
    sentiment = get_news_sentiment(symbol)
    if sentiment is not None:
        results.append({"symbol": symbol, "sentiment": sentiment})

df = pd.DataFrame(results)
df_sorted = df.sort_values(by="sentiment", ascending=False)

print("Top 5 Positive Sentiment Stocks:")
print(df_sorted.head(5))

print("\nTop 5 Negative Sentiment Stocks:")
print(df_sorted.tail(5)
