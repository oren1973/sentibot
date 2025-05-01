import requests
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from datetime import datetime

nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

NEWS_API_KEY = "49e6a262cba74b419c2dbea7c3376eb9"

def fetch_headlines():
    url = (
        f"https://newsapi.org/v2/top-headlines?"
        f"category=business&language=en&pageSize=10&apiKey={NEWS_API_KEY}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        return [("שגיאה בקבלת חדשות", 0.0)]

    articles = response.json().get("articles", [])
    return [
        (a["title"], sia.polarity_scores(a["title"])['compound'])
        for a in articles if "title" in a
    ]

def build_report():
    headlines = fetch_headlines()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report = f"🕒 Sentiment Report: {now}\n\n"
    for title, score in headlines:
        sentiment = "🟢" if score > 0.2 else "🔴" if score < -0.2 else "🟡"
        report += f"{sentiment} {title} (Score: {score:.2f})\n"
    return report
