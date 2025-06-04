# recommender.py
from settings import setup_logger, RECOMMENDER_THRESHOLD_BUY_ORIGINAL_SCALE, RECOMMENDER_THRESHOLD_SELL_ORIGINAL_SCALE

logger = setup_logger(__name__)

def make_recommendation(avg_sentiment_score: float) -> dict:
    decision = "HOLD" 

    # חשוב: ודא שה-avg_sentiment_score שמועבר לכאן הוא אכן בסקאלה המתאימה לספים!
    # הספים מיובאים כעת מ-settings.py.
    # אם avg_sentiment_score הוא ממוצע של ציונים משוקללים (שיכולים להיות > 1),
    # אז הספים המקוריים של 0.2 ו- -0.2 (שהם על סקאלת VADER compound) לא יתאימו.
    # יש להתאים את הספים ב-settings.py או את הנתונים המועברים לכאן.
    
    if avg_sentiment_score > RECOMMENDER_THRESHOLD_BUY_ORIGINAL_SCALE: # שימוש בסף מהגדרות
        decision = "BUY"
    elif avg_sentiment_score < RECOMMENDER_THRESHOLD_SELL_ORIGINAL_SCALE: # שימוש בסף מהגדרות
        decision = "SELL"

    logger.info(f"Recommendation based on avg_sentiment_score: {avg_sentiment_score:.4f} -> {decision}")
    
    return {
        "decision": decision,
        "score": avg_sentiment_score 
    }
