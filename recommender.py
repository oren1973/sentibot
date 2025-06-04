# recommender.py
from settings import setup_logger, RECOMMENDER_THRESHOLD_BUY, RECOMMENDER_THRESHOLD_SELL

logger = setup_logger(__name__)

def make_recommendation(avg_sentiment_score: float) -> dict:
    decision = "HOLD" 

    # הספים מיובאים כעת מ-settings.py (RECOMMENDER_THRESHOLD_BUY, RECOMMENDER_THRESHOLD_SELL)
    # ודא שהם מותאמים לסקאלה של avg_sentiment_score המשוקלל.
    
    if avg_sentiment_score > RECOMMENDER_THRESHOLD_BUY:
        decision = "BUY"
    elif avg_sentiment_score < RECOMMENDER_THRESHOLD_SELL: # שים לב, אם SELL הוא למשל 0.35, אז ציון נמוך מזה הוא מכירה
        decision = "SELL" # או HOLD אם הציון בין SELL ל-BUY

    # אם רוצים אזור ניטרלי מוגדר יותר:
    # if avg_sentiment_score > RECOMMENDER_THRESHOLD_BUY:
    #     decision = "BUY"
    # elif avg_sentiment_score < RECOMMENDER_THRESHOLD_SELL:
    #     decision = "SELL"
    # else: # (avg_sentiment_score is between SELL and BUY thresholds)
    #     decision = "HOLD"

    logger.info(f"Recommendation based on avg_sentiment_score: {avg_sentiment_score:.4f} -> {decision}")
    
    return {
        "decision": decision,
        "score": avg_sentiment_score 
    }
