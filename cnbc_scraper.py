# cnbc_scraper.py
import feedparser
from logger_config import setup_logger

logger = setup_logger(__name__)

CNBC_RSS_URL = "https://www.cnbc.com/id/100003114/device/rss/rss.html"

# מיפוי סימבולים לשמות ומילות מפתח (נשאר כפי שהיה)
KEYWORDS = {
    "TSLA": ["Tesla", "Elon Musk", "TSLA"],
    # ... (שאר המילות מפתח שלך)
    "AAPL": ["Apple", "AAPL", "iPhone"],
    "MSFT": ["Microsoft", "MSFT", "Azure", "Windows"], # דוגמה להוספה
    "NVDA": ["Nvidia", "Jensen Huang", "NVDA", "GPU"],
    "META": ["Meta", "Facebook", "META", "Instagram", "WhatsApp"],
    "AMZN": ["Amazon", "AMZN", "AWS", "Bezos"],
    "GOOGL": ["Google", "Alphabet", "GOOGL", "GOOG", "Android", "Search"],
    # הוסף עוד מניות רלוונטיות מה-SYMBOLS שלך ב-main.py
}


def get_cnbc_titles(symbol: str) -> list[tuple[str, str]]:
    """
    שולף כותרות מ-CNBC עבור סמל נתון על בסיס מילות מפתח.
    מחזיר רשימת tuples של (כותרת, "CNBC").
    """
    source_name = "CNBC"
    symbol_upper = symbol.upper()
    # אם הסמל לא מוגדר ב-KEYWORDS, השתמש בסמל עצמו כמילת מפתח יחידה
    keywords_for_symbol = KEYWORDS.get(symbol_upper, [symbol_upper]) 
    headlines = []

    logger.info(f"Fetching news for {symbol_upper} from {source_name} using keywords: {keywords_for_symbol}...")

    try:
        feed = feedparser.parse(CNBC_RSS_URL, timeout=10)

        if feed.bozo:
            bozo_reason = feed.get("bozo_exception", "Unknown parsing error")
            logger.warning(f"Failed to parse RSS feed from {source_name}. Reason: {bozo_reason}")
            return []
        
        if not feed.entries:
            logger.info(f"No entries found in RSS feed from {source_name}.")
            return []

        # logger.debug(f"Scanning {len(feed.entries)} entries from {source_name} for {symbol_upper}...")
        
        titles_found_for_symbol = 0
        for entry in feed.entries[:50]:  # סריקה של עד 50 כותרות מהפיד הכללי
            title = entry.get("title", "").strip()
            if not title or len(title) < 10: # דלג על כותרות ריקות או קצרות מאוד
                continue

            # logger.debug(f"  Scanning title: '{title}'") # יכול להיות מאוד ורבלי

            # בדיקת התאמה לפי מילת מפתח (לא רגיש לרישיות)
            if any(kw.lower() in title.lower() for kw in keywords_for_symbol):
                headlines.append((title, source_name))
                titles_found_for_symbol += 1
                # אפשר להוסיף כאן הגבלה על מספר הכותרות פר סמל אם רוצים
                # if titles_found_for_symbol >= 5: # למשל, עד 5 כותרות רלוונטיות פר סמל
                #     break 
        
        logger.info(f"Found {len(headlines)} relevant headlines for {symbol_upper} from {source_name} (out of {len(feed.entries)} scanned).")

    except Exception as e:
        logger.error(f"An unexpected error occurred in {source_name} scraper for {symbol_upper}: {e}", exc_info=True)

    return headlines # החזר את כל הכותרות הרלוונטיות שנמצאו (עד למגבלת הסריקה הכללית)
