# 📄 utils.py
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

nltk.download("vader_lexicon")

def analyze_sentiment(headlines):
    sia = SentimentIntensityAnalyzer()
    sentiment_data = []

    for headline in headlines:
        if not isinstance(headline, str) or not headline.strip():
            continue
        score = sia.polarity_scores(headline.strip())["compound"]
        sentiment_data.append({
            "headline": headline.strip(),
            "sentiment": float(score)
        })

    return sentiment_data


def format_headlines(data):
    lines = ["📊 ניתוח סנטימנט יומי:\n"]
    for item in data:
        text = item.get("headline", "")
        score = float(item.get("sentiment", 0.0))
        category = "חיובי" if score > 0.05 else "שלילי" if score < -0.05 else "ניטרלי"
        lines.append(f"→ ({score:.2f}) {category} \n{text}")
    return "\n\n".join(lines)
