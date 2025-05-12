# recommender.py – גרסת בדיקה להרצה יזומה

def make_recommendation(avg_sentiment):
    """
    גרסה ניסיונית: כל סנטימנט חיובי קטן יוביל ל־BUY,
    כל שלילי קטן יוביל ל־SELL – כדי לוודא שהמסחר פועל.
    """
    if avg_sentiment > 0.01:
        decision = "buy"
    elif avg_sentiment < -0.01:
        decision = "sell"
    else:
        decision = "hold"

    return {
        "decision": decision,
        "score": avg_sentiment
    }
