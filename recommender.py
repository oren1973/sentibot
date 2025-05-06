from sentiment_analyzer import analyze_sentiment

def make_recommendation(titles):
    """
    מקבל רשימת כותרות חדשות, מנתח סנטימנט, ומחזיר המלצה: BUY, HOLD או SELL
    """
    if not titles:
        return {"sentiment": 0.0, "decision": "HOLD"}

    sentiment_scores = [analyze_sentiment(title) for title in titles]
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

    if avg_sentiment > 0.2:
        decision = "BUY"
    elif avg_sentiment < -0.2:
        decision = "SELL"
    else:
        decision = "HOLD"

    return {"sentiment": round(avg_sentiment, 3), "decision": decision}
