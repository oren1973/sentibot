# sentiment_analyzer.py
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
# שיניתי את שם המשתנה ב-settings.py ל-NEWS_SOURCES_CONFIG
from settings import setup_logger, NEWS_SOURCES_CONFIG 

# אתחול לוגר ספציפי למודול זה
logger = setup_logger(__name__) # השם יהיה "sentiment_analyzer"

# אתחול ה-analyzer פעם אחת כשהמודול נטען
try:
    analyzer = SentimentIntensityAnalyzer()
    logger.info("VADER SentimentIntensityAnalyzer initialized successfully.")
except Exception as e:
    logger.critical(f"Failed to initialize SentimentIntensityAnalyzer: {e}", exc_info=True)
    analyzer = None # הגדר כ-None אם האתחול נכשל

def analyze_sentiment(text: str, source_name: str = None) -> float | None:
    """
    מנתח את הסנטימנט של טקסט נתון, עם אפשרות לשקלול לפי משקל המקור.
    מחזיר ציון סנטימנט משוקלל (או רק מנורמל אם אין משקל) בין ערכים אפשריים, 
    או None אם ה-analyzer לא אותחל או הטקסט ריק.

    הערה: הטווח של הציון המוחזר תלוי במשקלים. אם כל המשקלים הם 1.0,
    הטווח יהיה בין 0 (שלילי לחלוטין) ל-1 (חיובי לחלוטין).
    אם יש משקלים גדולים מ-1, הציון יכול לחרוג מ-1.
    """
    if analyzer is None:
        logger.error("Sentiment analyzer is not initialized. Cannot analyze sentiment.")
        return None
    
    if not text or not isinstance(text, str):
        logger.warning("Received empty or invalid text for sentiment analysis. Returning None.")
        return None

    try:
        # קבלת ציון ה-compound מ-VADER (טווח: -1 עד +1)
        base_score = analyzer.polarity_scores(text)["compound"]
        logger.debug(f"Text: '{text[:70]}...', VADER compound score: {base_score:.4f}")

        # נרמול הציון לטווח 0 עד 1 (0 = הכי שלילי, 0.5 = ניטרלי, 1 = הכי חיובי)
        # זה שימושי אם רוצים שכל הציונים יהיו באותו סקאלה לפני שקלול.
        normalized_score = (base_score + 1) / 2
        logger.debug(f"Normalized score (0-1): {normalized_score:.4f}")

        # ברירת מחדל למשקל אם המקור לא ידוע או לא מוגדר לו משקל
        source_weight = 1.0 
        
        if source_name:
            source_config = NEWS_SOURCES_CONFIG.get(source_name)
            if source_config:
                source_weight = source_config.get("weight", 1.0)
                logger.debug(f"Source '{source_name}' found with weight: {source_weight}")
            else:
                logger.warning(f"Source '{source_name}' not found in NEWS_SOURCES_CONFIG. Using default weight 1.0.")
        else:
            logger.debug("No source name provided. Using default weight 1.0.")

        # שקלול הציון המנורמל עם משקל המקור
        # אם המשקל הוא 1.0, זה פשוט הציון המנורמל.
        # אם המשקל שונה, הוא יכול להגביר או להחליש את השפעת הסנטימנט מהמקור.
        adjusted_score = normalized_score * source_weight
        logger.debug(f"Adjusted score (after weight {source_weight}): {adjusted_score:.4f}")

        return round(adjusted_score, 4) # החזרת הציון עם 4 מקומות אחרי הנקודה לדיוק

    except Exception as e:
        logger.error(f"Error during sentiment analysis for text '{text[:70]}...': {e}", exc_info=True)
        return None # החזר None במקרה של שגיאה לא צפויה

if __name__ == "__main__":
    # --- בלוק לבדיקה מקומית ---
    import logging
    test_logger = setup_logger(__name__, level=logging.DEBUG)

    # ודא ש-NEWS_SOURCES_CONFIG מוגדר ב-settings.py
    # לדוגמה, אם ב-settings.py יש:
    # NEWS_SOURCES_CONFIG = {
    #     "Yahoo Finance": {"weight": 1.0},
    #     "CNBC": {"weight": 1.2},
    #     "HypotheticalSource": {"weight": 0.8}
    # }

    sample_texts = [
        ("This is a great and wonderful stock! I love it.", "CNBC"),
        ("This company is a complete disaster and will fail.", "Yahoo Finance"),
        ("The market is neutral today.", "HypotheticalSource"),
        ("Another piece of news with no specific source.", None),
        ("This is bad.", "UnknownSource") # מקור שלא מוגדר ב-NEWS_SOURCES_CONFIG
    ]

    if analyzer: # בדוק שה-analyzer אותחל
        for text_to_analyze, src_name in sample_texts:
            test_logger.info(f"--- Analyzing text for source: {src_name or 'N/A'} ---")
            test_logger.info(f"Original text: \"{text_to_analyze}\"")
            
            calculated_sentiment = analyze_sentiment(text_to_analyze, source_name=src_name)
            
            if calculated_sentiment is not None:
                test_logger.info(f"Calculated Sentiment Score: {calculated_sentiment}")
            else:
                test_logger.warning("Sentiment analysis returned None.")
            test_logger.info("--- Finished analyzing text ---")
    else:
        test_logger.critical("VADER Analyzer not initialized. Cannot run tests.")
