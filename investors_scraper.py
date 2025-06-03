# investors_scraper.py
import feedparser
from logger_config import setup_logger # ייבוא פונקציית הלוגר

logger = setup_logger(__name__) # אתחול לוגר ספציפי למודול זה

def get_investors_news(symbol: str) -> list[tuple[str, str]]:
    """
    מקבל סימבול ומחזיר רשימת tuples של (כותרת, מקור) מ-Investors.com (IBD).
    מחזיר רשימה ריקה במקרה של שגיאה.
    """
    source_name = "Investors.com"
    headlines = []
    url = f"https://research.investors.com/rss.aspx?kw={symbol}"
    
    logger.info(f"Fetching news for {symbol} from {source_name}...")
    
    try:
        # הוספת timeout ל-feedparser (מועבר ל-urlopen הפנימי)
        feed = feedparser.parse(url, timeout=10) 

        if feed.bozo:
            # feed.bozo_exception מכיל את החריגה המקורית אם ישנה
            bozo_reason = feed.get("bozo_exception", "Unknown parsing error")
            logger.warning(f"Failed to parse RSS feed from {source_name} for {symbol}. Reason: {bozo_reason}")
            return []

        if not feed.entries:
            logger.info(f"No entries found in RSS feed from {source_name} for {symbol}.")
            return []

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            if title and len(title) >= 10: # בדיקת אורך מינימלי
                headlines.append((title, source_name))
            elif title:
                logger.debug(f"Skipping short title from {source_name} for {symbol}: '{title}'")
        
        logger.info(f"Found {len(headlines)} headlines for {symbol} from {source_name}.")

    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching news from {source_name} for {symbol}: {e}", exc_info=True)
        # exc_info=True יוסיף את ה-traceback המלא של השגיאה ללוג
    
    return headlines
