# recommender.py
from settings import setup_logger 
# אפשר יהיה לייבא ספים מ-settings.py בעתיד:
# from settings import SENTIMENT_THRESHOLD_BUY, SENTIMENT_THRESHOLD_SELL

# אתחול לוגר ספציפי למודול זה
logger = setup_logger(__name__) # השם יהיה "recommender"

# --- ספי החלטה ---
# כרגע מקודדים כאן. מומלץ להעביר אותם ל-settings.py כדי שיהיו קונפיגורביליים.
# לדוגמה, ב-settings.py:
# SENTIMENT_THRESHOLD_BUY = 0.65 # אם הציון המנורמל והמשוקלל הוא בין 0 ל-1+
# SENTIMENT_THRESHOLD_SELL = 0.35 # אם הציון המנורמל והמשוקלל הוא בין 0 ל-1+
# NEUTRAL_ZONE_LOWER = 0.45
# NEUTRAL_ZONE_UPPER = 0.55

# בהנחה שה-avg_sentiment שמתקבל הוא *לאחר* נרמול ושקלול, ויכול להיות בטווח רחב יותר
# אם avg_sentiment הוא מהקוד הקודם שלך (0 עד 1 כפול משקל), נצטרך להתאים את הספים.
# נניח כרגע שה-avg_sentiment שמגיע לפה הוא הציון הסופי מה-sentiment_analyzer
# והוא יכול להיות למשל בין 0 ל-1.2 אם משקל מקסימלי הוא 1.2.
# הספים המקוריים שלך היו 0.2 ו- -0.2 על ה-compound score (-1 עד +1).
# אם נניח שהציון המגיע לכאן הוא בטווח 0 עד (1*max_weight), נצטרך לחשוב על הספים מחדש.

# נשתמש כרגע בספים שדורשים התאמה לטווח הציון החדש מ-sentiment_analyzer.
# אם הציון מנורמל ל-0..1 (לפני שקלול), אז:
# BUY > 0.7  (מקביל ל-compound > 0.4)
# SELL < 0.3 (מקביל ל-compound < -0.4)
# HOLD בין 0.3 ל-0.7
# אם יש שקלול, זה מסבך. נחזור לספים המקוריים שלך ונניח שה-avg_sentiment שמתקבל
# הותאם איכשהו בחזרה לטווח דומה ל-compound המקורי, או שהספים האלה הם על סקאלה שונה.
# **זו נקודה חשובה לדיון והתאמה!**

# נחזור כרגע לספים מהקוד המקורי שלך, ונניח שה-avg_sentiment שמגיע לכאן
# הוא ממוצע של ציוני VADER compound המקוריים (לפני נרמול ושקלול).
# אם הוא *לא*, הספים האלה לא יהיו נכונים.
THRESHOLD_BUY_ORIGINAL_SCALE = 0.2  # על סקאלת VADER compound (-1 עד +1)
THRESHOLD_SELL_ORIGINAL_SCALE = -0.2 # על סקאלת VADER compound (-1 עד +1)


def make_recommendation(avg_sentiment_score: float) -> dict:
    """
    מקבל סנטימנט ממוצע (נניח שהוא על סקאלת VADER compound המקורית, -1 עד +1)
    ומחזיר המלצת מסחר פשוטה.
    """
    decision = "HOLD" # ברירת מחדל

    # חשוב: ודא שה-avg_sentiment_score שמועבר לכאן הוא אכן בסקאלה המתאימה לספים!
    # אם הוא ממוצע של הציונים המשוקללים (שיכולים להיות > 1 או שונים מטווח -1..1),
    # הספים האלה לא יעבדו נכון.

    if avg_sentiment_score > THRESHOLD_BUY_ORIGINAL_SCALE:
        decision = "BUY"
    elif avg_sentiment_score < THRESHOLD_SELL_ORIGINAL_SCALE:
        decision = "SELL"
    # else: decision נשאר "HOLD"

    logger.info(f"Recommendation based on avg_sentiment_score: {avg_sentiment_score:.4f} -> {decision}")
    
    return {
        "decision": decision,
        "score": avg_sentiment_score # החזר את הציון המקורי שהתקבל
    }

if __name__ == "__main__":
    # --- בלוק לבדיקה מקומית ---
    import logging
    test_logger = setup_logger(__name__, level=logging.DEBUG)

    test_scores = [0.8, 0.25, 0.1, 0.0, -0.15, -0.3, -0.7]
    # אלו ציונים שמדמים את סקאלת ה-compound של VADER (-1 עד +1)

    for score in test_scores:
        test_logger.info(f"--- Testing recommendation for score: {score} ---")
        recommendation = make_recommendation(score)
        test_logger.info(f"Input score: {score}, Decision: {recommendation['decision']}")
        # ודא שהציון המוחזר הוא אותו ציון שהוכנס
        assert recommendation['score'] == score, "Returned score does not match input score" 
    test_logger.info("--- Finished all recommendation tests ---")
