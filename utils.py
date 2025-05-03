# utils.py

from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

nltk.download("vader_lexicon")

def analyze_sentiment(headlines):
    sia = SentimentIntensityAnalyzer()
    sentiment_data = []

    for headline in headlines:
        if not isinstance(headline, str) or not headline.strip():
            continue  # מדלג על שורות ריקות או לא טקסטואליות
        sentiment_score = sia.polarity_scores(headline)["compound"]
        sentiment_data.append({
            "headline": headline.strip(),
            "sentiment": sentiment_score
        })

    return sentiment_data

def format_headlines(sentiment_data):
    if not sentiment_data:
        return "⚠️ לא נמצאו כותרות תקינות לניתוח."

    lines = ["📰 ניתוח כותרות מהשוק:\n"]
    for item in sentiment_data:
        if isinstance(item, dict):
            text = item.get("headline", "").strip()
            score = item.get("sentiment", 0.0)
            sentiment_type = "חיובי" if score > 0.05 else "שלילי" if score < -0.05 else "ניטרלי"
            lines.append(f"→ ({score:.2f}) {sentiment_type}  \n{text}")
    return "\n\n".join(lines)
