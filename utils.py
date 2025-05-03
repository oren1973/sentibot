# utils.py

from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

nltk.download("vader_lexicon")


def analyze_sentiment(headlines):
    sia = SentimentIntensityAnalyzer()
    sentiment_data = []

    for headline in headlines:
        if not isinstance(headline, str) or not headline.strip():
            continue  # דילוג על טקסטים ריקים או לא תקינים

        sentiment_score = sia.polarity_scores(headline.strip())["compound"]

        sentiment_data.append({
            "headline": headline.strip(),
            "sentiment": float(sentiment_score)  # מבטיח שיהיה float
        })

    return sentiment_data


def format_headlines(sentiment_data):
    if not sentiment_data or not isinstance(sentiment_data, list):
        return "⚠️ לא נמצאו כותרות תקינות לניתוח."

    lines = ["📰 ניתוח כותרות מהשוק:\n"]

    for item in sentiment_data:
        if not isinstance(item, dict):
            continue
        text = item.get("headline", "").strip()
        score = item.get("sentiment", 0.0)

        try:
            score_float = float(score)
        except (TypeError, ValueError):
            score_float = 0.0

        sentiment_type = "חיובי" if score_float > 0.05 else "שלילי" if score_float < -0.05 else "ניטרלי"
        lines.append(f"→ ({score_float:.2f}) {sentiment_type}  \n{text}")

    return "\n\n".join(lines)
