# recommender.py

def make_recommendation(avg_sentiment):
    """מקבל סנטימנט ממוצע ומחזיר המלצת מסחר פשוטה"""
    if avg_sentiment > 0.2:
        decision = "BUY"
    elif avg_sentiment < -0.2:
        decision = "SELL"
    else:
        decision = "HOLD"

    return {
        "decision": decision,
        "score": avg_sentiment
    }
