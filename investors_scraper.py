# investors_scraper.py
import feedparser
from settings import setup_logger, MIN_HEADLINE_LENGTH # ייבוא מהקובץ settings.py

# אתחול לוגר ספציפי למודול זה
# השם __name__ ייתן ללוגר את השם "investors_scraper"
logger = setup_logger(__name__) 

def get_investors_news(symbol: str, rss_url_template: str) -> list[tuple[str, str]]:
    """
    מקבל סימבול ותבנית URL ל-RSS, ומחזיר רשימת tuples של (כותרת, מקור) מ-Investors.com (IBD).
    מחזיר רשימה ריקה במקרה של שגיאה.
    """
    source_name = "Investors.com" # שם המקור כפי שיופיע בלוגים ובפלט
    headlines = []
    
    if not rss_url_template:
        logger.error(f"RSS URL template not provided for {source_name}. Cannot fetch news for {symbol}.")
        return []

    # החלפת ה-placeholder {symbol} בסימול האמיתי
    rss_url = rss_url_template.replace("{symbol}", symbol)
    
    logger.info(f"Fetching news for '{symbol}' from {source_name} using URL: {rss_url}")
    
    try:
        # הוספת timeout ל-feedparser (מועבר ל-urlopen הפנימי)
        feed = feedparser.parse(rss_url, timeout=10) 

        if feed.bozo:
            # feed.bozo_exception מכיל את החריגה המקורית אם ישנה
            bozo_reason = feed.get("bozo_exception", "Unknown parsing error")
            logger.warning(f"Failed to parse RSS feed from {source_name} for '{symbol}'. Reason: {bozo_reason} (URL: {rss_url})")
            return [] # החזר רשימה ריקה במקרה של שגיאת parsing

        if not feed.entries:
            logger.info(f"No entries found in RSS feed from {source_name} for '{symbol}'. (URL: {rss_url})")
            return []

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            if title and len(title) >= MIN_HEADLINE_LENGTH: # שימוש באורך מינימלי מההגדרות
                headlines.append((title, source_name))
            elif title:
                logger.debug(f"Skipping short title from {source_name} for '{symbol}': '{title}' (Length: {len(title)})")
        
        logger.info(f"Found {len(headlines)} headlines for '{symbol}' from {source_name}.")

    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching news from {source_name} for '{symbol}': {e} (URL: {rss_url})", exc_info=True)
        # exc_info=True יוסיף את ה-traceback המלא של השגיאה ללוג
    
    return headlines

if __name__ == "__main__":
    # --- בלוק לבדיקה מקומית של ה-scraper ---
    # ודא שקובץ settings.py קיים באותה תיקייה או בנתיב הייבוא של פייתון
    
    # הגדרת לוגר ברמת DEBUG לצורך הבדיקה המקומית
    # זה ידרוס את הגדרת ה-level מהאתחול הראשי של הלוגר אם הוא מוגדר ל-INFO
    test_logger = setup_logger(__name__, level=logging.DEBUG) 

    # קבלת תבנית ה-URL מ-settings.py (לצורך הדגמה, בפועל news_scraper.py יעשה זאת)
    # זה ידרוש ייבוא נוסף: from settings import NEWS_SOURCES_CONFIG
    # temp_rss_url_template = NEWS_SOURCES_CONFIG.get("Investors.com", {}).get("rss_url_template")

    # או פשוט השתמש ב-URL ישירות לבדיקה:
    temp_rss_url_template_for_test = "https://research.investors.com/rss.aspx?kw={symbol}"
    
    if temp_rss_url_template_for_test:
        test_symbols = ["AAPL", "TSLA", "NONEXISTENT"]
        for sym in test_symbols:
            test_logger.info(f"--- Testing {sym} for Investors.com ---")
            retrieved_headlines = get_investors_news(sym, temp_rss_url_template_for_test)
            if retrieved_headlines:
                test_logger.debug(f"Retrieved {len(retrieved_headlines)} headlines for {sym}:")
                for i, (h_title, h_source) in enumerate(retrieved_headlines):
                    test_logger.debug(f"  {i+1}. [{h_source}] {h_title}")
            else:
                test_logger.debug(f"No headlines retrieved for {sym}.")
            test_logger.info(f"--- Finished testing {sym} ---")
    else:
        test_logger.error("Could not get RSS URL template for Investors.com for testing.")
