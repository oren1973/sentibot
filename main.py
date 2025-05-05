# sentibot_v1_3: שדרוג מנוע הסנטימנט עם ניתוח חדשות אמיתיות

import requests
from news_scraper import fetch_news_titles
from sentiment import get_sentiment_score
import time

STOCKS = ["AAPL", "TSLA", "NVDA", "MSFT", "META"]
NEWS_LIMIT = 5  # כמות מקסימלית של כתבות לכל מניה

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0 Safari/537.36'
}

def fetch_news_titles(symbol):
    url = f"https://finance.yahoo.com/quote/{symbol}?p={symbol}"
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')

    news_items = soup.select('li.js-stream-content')[:NEWS_LIMIT]
    headlines = []

    for item in news_items:
        title = item.get_text(strip=True)
        if title:
            headlines.append(title)

    return headlines

def analyze_sentiment(symbol):
    print(f"\n🔍 מחשב סנטימנט עבור {symbol}...")
    headlines = fetch_news_titles(symbol)
    scores = []

    for h in headlines:
        score = get_sentiment_score(h)
        scores.append(score)
        print(f"📰 '{h}' → {score:.4f}")

    if scores:
        avg = sum(scores) / len(scores)
    else:
        avg = 0.0

    print(f"📊 ממוצע סנטימנט עבור {symbol}: {avg:.3f}")
    print(f"🧠 {symbol}: ציון סנטימנט: {avg:.3f}")

    if avg >= 0.25:
        decision = "BUY"
    elif avg <= -0.25:
        decision = "SELL"
    else:
        decision = "HOLD"

    print(f"📊 {symbol}: החלטה: {decision}")
    return symbol, avg, decision

def main():
    print("\n🚀 Sentibot v1.3 –", time.strftime("%Y-%m-%d %H:%M:%S"))
    for symbol in STOCKS:
        analyze_sentiment(symbol)

if __name__ == '__main__':
    main()
