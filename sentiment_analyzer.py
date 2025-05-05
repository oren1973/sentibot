### sentiment_analyzer.py
import requests
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

RSS_FEED_TEMPLATE = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"

analyzer = SentimentIntensityAnalyzer()

def fetch_news_titles(symbol):
    url = RSS_FEED_TEMPLATE.format(symbol=symbol)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"⚠️ שגיאה בהורדת כותרות עבור {symbol}: {e}")
        return []

    import feedparser
    feed = feedparser.parse(response.text)
    return [entry.get("title", "") for entry in feed.entries if entry.get("title")]

def analyze_sentiment(symbol):
    titles = fetch_news_titles(symbol)
    scores = []

    for title in titles:
        score = analyzer.polarity_scores(title)["compound"]
        print(f"📰 '{title}' → {score:.4f}")
        scores.append(score)

    if scores:
        avg_score = sum(scores) / len(scores)
    else:
        avg_score = 0.0

    print(f"📊 ממוצע סנטימנט עבור {symbol}: {avg_score:.3f}")
    return avg_score


### requirements.txt
vaderSentiment
feedparser
requests
