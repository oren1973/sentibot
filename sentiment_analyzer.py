from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from config import NEWS_SOURCES

analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(text, source=None):
    base_score = analyzer.polarity_scores(text)["compound"]

    # נורמליזציה: ערך בין 0 ל-1
    normalized_score = (base_score + 1) / 2

    # קבלת משקל המקור, אם קיים
    weight = 1.0
    if source in NEWS_SOURCES:
        weight = NEWS_SOURCES[source].get("weight", 1.0)

    # שקלול ציון עם משקל המקור
    adjusted_score = normalized_score * weight

    return round(adjusted_score, 3)
