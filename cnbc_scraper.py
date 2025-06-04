# cnbc_scraper.py
import feedparser
from settings import setup_logger, MIN_HEADLINE_LENGTH # ייבוא מהקובץ settings.py

# אתחול לוגר ספציפי למודול זה
logger = setup_logger(__name__) # השם יהיה "cnbc_scraper"

# מיפוי סימבולים למילות מפתח
# מומלץ לרכז את זה ב-settings.py אם המיפוי גדל מאוד או משותף למודולים נוספים.
# כרגע, נשאיר אותו כאן לנוחות. ודא שהוא כולל את כל הסמלים הרלוונטיים מה-SYMBOLS שלך.
KEYWORDS_BY_SYMBOL = {
    "TSLA": ["Tesla", "Elon Musk", "TSLA"],
    "NVDA": ["Nvidia", "Jensen Huang", "NVDA", "GPU"],
    "AAPL": ["Apple", "AAPL", "iPhone", "MacBook", "iPad", "Tim Cook"],
    "MSFT": ["Microsoft", "MSFT", "Azure", "Windows", "Satya Nadella", "OpenAI"],
    "META": ["Meta", "Facebook", "META", "Instagram", "WhatsApp", "Zuckerberg"],
    "AMZN": ["Amazon", "AMZN", "AWS", "Bezos", "Prime"],
    "GOOGL": ["Google", "Alphabet", "GOOGL", "GOOG", "Android", "Search", "Sundar Pichai", "Waymo"],
    "GOOG": ["Google", "Alphabet", "GOOG", "Android", "Search", "Sundar Pichai", "Waymo"], # גם ל-GOOG
    "PFE": ["Pfizer", "PFE", "BioNTech"],
    "XOM": ["Exxon", "ExxonMobil", "XOM", "oil", "gas"],
    "JPM": ["JPMorgan", "JPM", "Jamie Dimon", "Chase"],
    "DIS": ["Disney", "DIS", "Disney+", "ESPN", "parks"],
    "WMT": ["Walmart", "WMT", "retail"],
    # הוסף עוד מניות רלוונטיות מה-SYMBOLS שלך ב-main.py והמילים המשויכות אליהן
}


def get_cnbc_titles(symbol: str, cnbc_general_rss_url: str, max_feed_items_to_scan: int = 50) -> list[tuple[str, str]]:
    """
    שולף כותרות מ-CNBC עבור סמל נתון על בסיס מילות מפתח מפיד RSS כללי.
    מקבל סימבול, URL לפיד ה-RSS הכללי של CNBC, ומספר מקסימלי של פריטים לסרוק מהפיד.
    מחזיר רשימת tuples של (כותרת, "CNBC").
    """
    source_name = "CNBC"
    symbol_upper = symbol.upper() # עבודה עם סמלים באותיות גדולות לטובת מילון ה-KEYWORDS
    
    # קבלת מילות המפתח עבור הסמל. אם הסמל לא מוגדר במילון, השתמש בסמל עצמו כמילת מפתח.
    keywords_for_symbol = KEYWORDS_BY_SYMBOL.get(symbol_upper, [symbol_upper]) 
    
    headlines = []

    if not cnbc_general_rss_url:
        logger.error(f"CNBC general RSS URL not provided. Cannot fetch news for {symbol_upper}.")
        return []

    logger.info(f"Fetching news for '{symbol_upper}' from {source_name} using keywords: {keywords_for_symbol} (Scanning up to {max_feed_items_to_scan} feed items from {cnbc_general_rss_url})")

    try:
        feed = feedparser.parse(cnbc_general_rss_url, timeout=10)

        if feed.bozo:
            bozo_reason = feed.get("bozo_exception", "Unknown parsing error")
            logger.warning(f"Failed to parse RSS feed from {source_name}. Reason: {bozo_reason} (URL: {cnbc_general_rss_url})")
            return []
        
        if not feed.entries:
            logger.info(f"No entries found in general RSS feed from {source_name}. (URL: {cnbc_general_rss_url})")
            return []

        logger.debug(f"Scanning {len(feed.entries)} total entries from {source_name} for '{symbol_upper}' (limit scan to {max_feed_items_to_scan})...")
        
        relevant_headlines_count = 0
        # סריקה של עד max_feed_items_to_scan כותרות מהפיד הכללי
        for entry in feed.entries[:max_feed_items_to_scan]:  
            title = entry.get("title", "").strip()
            
            if not title or len(title) < MIN_HEADLINE_LENGTH: 
                # logger.debug(f"  Skipping short/empty title: '{title}'") # יכול להיות מאוד ורבלי
                continue

            # logger.debug(f"  Scanning title: '{title}' for keywords: {keywords_for_symbol}")

            # בדיקת התאמה לפי מילת מפתח (לא רגיש לרישיות)
            if any(keyword.lower() in title.lower() for keyword in keywords_for_symbol):
                headlines.append((title, source_name))
                relevant_headlines_count += 1
                logger.debug(f"    Found relevant title for '{symbol_upper}': '{title}'")
                # אפשר להוסיף כאן הגבלה על מספר הכותרות *הרלוונטיות* פר סמל אם רוצים
                # לדוגמה, אם רוצים לא יותר מ-5 כותרות רלוונטיות לכל סמל:
                # if relevant_headlines_count >= 5:
                #     logger.info(f"Reached limit of 5 relevant headlines for '{symbol_upper}'. Stopping search for this symbol.")
                #     break 
        
        logger.info(f"Found {len(headlines)} relevant headlines for '{symbol_upper}' from {source_name} (scanned up to {max_feed_items_to_scan} feed items).")

    except Exception as e:
        logger.error(f"An unexpected error occurred in {source_name} scraper for '{symbol_upper}': {e} (URL: {cnbc_general_rss_url})", exc_info=True)

    return headlines

if __name__ == "__main__":
    # --- בלוק לבדיקה מקומית של ה-scraper ---
    import logging
    # from settings import NEWS_SOURCES_CONFIG # אם רוצים לקרוא את ה-URL מההגדרות

    test_logger = setup_logger(__name__, level=logging.DEBUG)

    # temp_cnbc_rss_url = NEWS_SOURCES_CONFIG.get("CNBC", {}).get("rss_url_template")
    temp_cnbc_rss_url_for_test = "https://www.cnbc.com/id/100003114/device/rss/rss.html"

    if temp_cnbc_rss_url_for_test:
        test_symbols = ["AAPL", "TSLA", "MSFT", "NONEXISTENT"] # בדוק סמל שכן מוגדר ב-KEYWORDS וגם אחד שלא
        for sym in test_symbols:
            test_logger.info(f"--- Testing {sym} for CNBC ---")
            # אפשר לשלוט על מספר הפריטים לסריקה בפיד הכללי לצורך הבדיקה
            retrieved_headlines = get_cnbc_titles(sym, temp_cnbc_rss_url_for_test, max_feed_items_to_scan=30)
            if retrieved_headlines:
                test_logger.debug(f"Retrieved {len(retrieved_headlines)} headlines for {sym}:")
                for i, (h_title, h_source) in enumerate(retrieved_headlines):
                    test_logger.debug(f"  {i+1}. [{h_source}] {h_title}")
            else:
                test_logger.debug(f"No headlines retrieved for {sym}.")
            test_logger.info(f"--- Finished testing {sym} ---")
    else:
        test_logger.error("Could not get CNBC RSS URL for testing.")
