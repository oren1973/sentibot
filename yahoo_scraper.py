# yahoo_scraper.py
import feedparser
import socket
from settings import setup_logger, MIN_HEADLINE_LENGTH
import logging 
import urllib.request # נוסיף את זה לבדיקה ישירה יותר

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
    socket.setdefaulttimeout(20) # הגדלתי מעט את ה-timeout ל-20 שניות
    raw_feed_content_sample = "N/A" # אתחול למקרה שהשליפה הישירה נכשלת

    try:
        # --- ניסיון לשלוף תוכן גולמי קודם ---
        try:
            logger.debug(f"Directly fetching content from {rss_url} for {symbol} using urllib.request...")
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            request = urllib.request.Request(rss_url, headers={'User-Agent': user_agent})
            with urllib.request.urlopen(request, timeout=15) as response: # timeout גם כאן
                feed_content_bytes = response.read()
                # נסה לפענח כ-UTF-8, התעלם משגיאות אם יש תווים בעייתיים רק לצורך הדגימה
                raw_feed_content_sample = feed_content_bytes.decode('utf-8', errors='ignore')
                logger.info(f"Successfully fetched raw content from {rss_url} for {symbol}. Length: {len(feed_content_bytes)} bytes.")
                # הדפס רק אם יש תוכן, ולוגר ברמת DEBUG
                if raw_feed_content_sample:
                    logger.debug(f"Raw content sample for {symbol} (first 1000 chars):\n{raw_feed_content_sample[:1000]}")
                else:
                    logger.debug(f"Raw content fetched for {symbol} was empty.")
        except Exception as e_fetch:
            logger.error(f"Failed to fetch raw content directly for {symbol} from {rss_url}: {e_fetch}", exc_info=False)
            # המשך לנסות עם feedparser בכל מקרה, אולי הוא יצליח איפה ש-urllib נכשל
        # --- סוף ניסיון שליפת תוכן גולמי ---

        logger.debug(f"Attempting to parse feed for {symbol} from: {rss_url} using feedparser")
        # feedparser אמור להשתמש ב-socket timeout שהוגדר גלובלית
        feed = feedparser.parse(rss_url) 
        
        if hasattr(feed, 'status'): # feedparser לא תמיד מוסיף 'status' ישירות, זה תלוי ב-handler
            logger.info(f"Feed HTTP status (from feedparser if available) for {symbol} from {source_name}: {feed.status}")
        # אם אין status, ייתכן שהייתה שגיאה ברמת הרשת עוד לפני ש-feedparser קיבל תגובה.
        # במקרה כזה, ההודעות מ-urllib.request עשויות להיות יותר אינפורמטיביות.
            
        logger.info(f"Feed declared encoding (from feedparser) for {symbol} from {source_name}: {feed.get('encoding', 'N/A')}")
        logger.info(f"Feed declared version (from feedparser) for {symbol} from {source_name}: {feed.get('version', 'N/A')}")
        logger.info(f"Is feed.bozo (malformed) (from feedparser) for {symbol} from {source_name}: {feed.bozo}")
        
        if feed.bozo and hasattr(feed, 'bozo_exception'):
             logger.warning(f"Bozo exception details (from feedparser) for {symbol} from {source_name}: {feed.bozo_exception}")

        num_entries_found = 0
        if hasattr(feed, 'entries') and feed.entries is not None:
            num_entries_found = len(feed.entries)
        logger.info(f"Number of entries found by feedparser for {symbol} from {source_name}: {num_entries_found}")

        if feed.bozo: 
            bozo_reason_msg = feed.get("bozo_exception", "Unknown parsing error")
            logger.warning(f"Failed to parse RSS feed from {source_name} for '{symbol}' due to bozo flag (feedparser). Reason: {bozo_reason_msg} (URL: {rss_url})")
            return [] 

        if not feed.entries: 
            logger.info(f"No entries (headlines) found by feedparser in the parsed RSS feed from {source_name} for '{symbol}'. (URL: {rss_url})")
            # בדוק אם התוכן הגולמי גם נראה ריק מפריטים
            if num_entries_found == 0 and raw_feed_content_sample != "N/A":
                if "<item>" not in raw_feed_content_sample.lower() and "<entry>" not in raw_feed_content_sample.lower():
                     logger.warning(f"The raw feed content for {symbol} (fetched via urllib) also seems to lack <item> or <entry> tags, suggesting the feed might indeed be empty or in an unexpected format.")
                else: # התוכן הגולמי מכיל פריטים, אבל feedparser לא מצא אותם!
                     logger.error(f"CRITICAL: Raw feed content for {symbol} appears to have <item> or <entry> tags, but feedparser found 0 entries. This indicates a parsing issue with feedparser for this feed.")
            return []

        for entry_idx, entry in enumerate(feed.entries):
            title = entry.get("title", "").strip()
            logger.debug(f"  Processing entry {entry_idx + 1}/{num_entries_found} for {symbol} from {source_name}. Title: '{title[:100]}...'")
            if title and len(title) >= MIN_HEADLINE_LENGTH:
                headlines.append((title, source_name))
                logger.debug(f"    Added headline: '{title[:100]}...'")
            elif title: # אם הכותרת לא ריקה אבל קצרה מדי
                logger.debug(f"    Skipping short title: '{title}' (Length: {len(title)})")
            else: # אם אין כותרת כלל
                logger.debug(f"    Skipping empty title for entry {entry_idx + 1}.")
        
        logger.info(f"Successfully processed {len(headlines)} valid headlines for '{symbol}' from {source_name} after filtering (out of {num_entries_found} initial entries).")

    except socket.timeout:
        logger.error(f"Socket timeout ({socket.getdefaulttimeout()}s) occurred while fetching/processing news from {source_name} for '{symbol}'. URL: {rss_url}", exc_info=False)
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching/processing news from {source_name} for '{symbol}': {e} (URL: {rss_url})", exc_info=True)
    finally:
        socket.setdefaulttimeout(original_timeout) 
    
    return headlines

if __name__ == '__main__':
    # --- בלוק בדיקה מקומית (אופציונלי) ---
    test_logger = setup_logger("yahoo_scraper_test", level=logging.DEBUG)
    test_symbols_list = ["AAPL", "TSLA", "NONEXISTENT_SYMBOL"] # בדוק עם סמל תקין וסמל לא קיים
    test_rss_url_template = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}®ion=US&lang=en-US"
    
    for test_symbol in test_symbols_list:
        test_logger.info(f"--- Testing Yahoo Finance Scraper for symbol {test_symbol} ---")
        results = get_yahoo_news(test_symbol, test_rss_url_template)
        if results:
            test_logger.info(f"Found {len(results)} headlines for {test_symbol}:")
            for i, (title, source) in enumerate(results):
                test_logger.info(f"  {i+1}. [{source}] {title}")
        else:
            test_logger.info(f"No headlines found for {test_symbol} during test.")
        test_logger.info(f"--- Finished Yahoo Finance Scraper test for {test_symbol} ---")
