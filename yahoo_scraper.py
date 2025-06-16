# yahoo_scraper.py
import feedparser
import socket
from settings import setup_logger, MIN_HEADLINE_LENGTH
import logging # הוספתי ייבוא של logging כדי להשתמש ב- logging.DEBUG

# שנה את רמת הלוגר כאן ל-DEBUG באופן זמני לבדיקה
# logger = setup_logger(__name__) # ברירת המחדל המקורית שלך היא INFO
logger = setup_logger(__name__, level=logging.DEBUG) # הפעל DEBUG באופן זמני עבור הלוגר של הקובץ הזה

def get_yahoo_news(symbol: str, rss_url_template: str) -> list[tuple[str, str]]:
    source_name = "Yahoo Finance"
    headlines = []

    if not rss_url_template:
        logger.error(f"RSS URL template not provided for {source_name}. Cannot fetch news for {symbol}.")
        return []

    rss_url = rss_url_template.replace("{symbol}", symbol)
    logger.info(f"Fetching news for '{symbol}' from {source_name} using URL: {rss_url}")
    
    original_timeout = socket.getdefaulttimeout()
    # הגדר timeout ספציפי לפעולה זו, 15 שניות זה סביר.
    # אם תיתקל ב-timeouts, אפשר לשקול להגדיל מעט.
    socket.setdefaulttimeout(15) 
    try:
        logger.debug(f"Attempting to parse feed for {symbol} from: {rss_url}")
        feed = feedparser.parse(rss_url) 
        
        # לוגינג מפורט על האובייקט feed
        # הערה: הדפסת האובייקט feed כולו עלולה להיות ארוכה מאוד.
        # שקול להסיר/להעיר את השורה הבאה אם הלוגים עמוסים מדי.
        # logger.debug(f"Full feed object for {symbol} from {source_name}: {feed}") 
        
        if hasattr(feed, 'status'):
            logger.info(f"Feed HTTP status for {symbol} from {source_name}: {feed.status}")
        else:
            logger.info(f"Feed HTTP status attribute not found for {symbol} from {source_name}.")
            
        logger.info(f"Feed declared encoding for {symbol} from {source_name}: {feed.get('encoding', 'N/A')}")
        logger.info(f"Feed declared version for {symbol} from {source_name}: {feed.get('version', 'N/A')}")
        logger.info(f"Is feed.bozo (malformed) for {symbol} from {source_name}: {feed.bozo}")
        
        if feed.bozo and hasattr(feed, 'bozo_exception'):
             logger.warning(f"Bozo exception details for {symbol} from {source_name}: {feed.bozo_exception}")

        # בדוק את מספר ה-entries *לפני* הבדיקה אם הוא ריק
        num_entries_found = 0
        if hasattr(feed, 'entries') and feed.entries is not None:
            num_entries_found = len(feed.entries)
        logger.info(f"Number of entries found by feedparser for {symbol} from {source_name}: {num_entries_found}")

        if feed.bozo: # אם הפיד לא תקין
            bozo_reason_msg = feed.get("bozo_exception", "Unknown parsing error")
            logger.warning(f"Failed to parse RSS feed from {source_name} for '{symbol}' due to bozo flag. Reason: {bozo_reason_msg} (URL: {rss_url})")
            return [] # צא אם הפיד לא תקין

        if not feed.entries: # אם הפיד תקין (לא bozo) אבל אין בו entries
            logger.info(f"No entries (headlines) found in the parsed RSS feed from {source_name} for '{symbol}'. (URL: {rss_url})")
            return []

        # אם הגענו לכאן, יש entries
        for entry_idx, entry in enumerate(feed.entries):
            title = entry.get("title", "").strip()
            logger.debug(f"  Processing entry {entry_idx + 1}/{num_entries_found} for {symbol} from {source_name}. Title: '{title[:100]}...'")
            if title and len(title) >= MIN_HEADLINE_LENGTH:
                headlines.append((title, source_name))
                logger.debug(f"    Added headline: '{title[:100]}...'")
            elif title:
                logger.debug(f"    Skipping short title: '{title}' (Length: {len(title)})")
            else:
                logger.debug(f"    Skipping empty title for entry {entry_idx + 1}.")
        
        logger.info(f"Successfully processed {len(headlines)} valid headlines for '{symbol}' from {source_name} after filtering (out of {num_entries_found} initial entries).")

    except socket.timeout:
        logger.error(f"Socket timeout (15s) occurred while fetching news from {source_name} for '{symbol}'. URL: {rss_url}", exc_info=False)
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching/processing news from {source_name} for '{symbol}': {e} (URL: {rss_url})", exc_info=True)
    finally:
        socket.setdefaulttimeout(original_timeout) # החזר את ה-timeout המקורי
    
    return headlines

if __name__ == '__main__':
    # --- בלוק בדיקה מקומית (אופציונלי) ---
    # כדי להריץ את זה, תצטרך להגדיר את settings.py ברמה הנכונה או לספק MIN_HEADLINE_LENGTH
    # ולוודא ש-setup_logger זמין.
    # from settings import MIN_HEADLINE_LENGTH # אם אתה מריץ את זה ישירות, שים לב לנתיבי ייבוא
    
    test_logger = setup_logger("yahoo_scraper_test", level=logging.DEBUG)
    test_symbol = "AAPL" # שנה לסמל לבדיקה
    test_rss_url_template = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}®ion=US&lang=en-US"
    
    test_logger.info(f"--- Testing Yahoo Finance Scraper for symbol {test_symbol} ---")
    results = get_yahoo_news(test_symbol, test_rss_url_template)
    if results:
        test_logger.info(f"Found {len(results)} headlines for {test_symbol}:")
        for i, (title, source) in enumerate(results):
            test_logger.info(f"  {i+1}. [{source}] {title}")
    else:
        test_logger.info(f"No headlines found for {test_symbol} during test.")
    test_logger.info(f"--- Finished Yahoo Finance Scraper test for {test_symbol} ---")
