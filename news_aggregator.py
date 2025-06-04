# news_aggregator.py (לשעבר news_scraper.py)

# ייבוא פונקציות ה-scraper הספציפיות
from yahoo_scraper import get_yahoo_news
from investors_scraper import get_investors_news
from marketwatch_scraper import fetch_marketwatch_titles
from cnbc_scraper import get_cnbc_titles
# אם יש לך עוד scrapers שהוספת לרשימה, יבא אותם כאן

# ייבוא מהגדרות
from settings import setup_logger, NEWS_SOURCES_CONFIG, DEFAULT_MAX_HEADLINES_PER_SOURCE, MIN_HEADLINE_LENGTH

# אתחול לוגר ספציפי למודול זה
logger = setup_logger(__name__) # השם יהיה "news_aggregator"

# מילון שממפה את שמות פונקציות ה-scraper (כפי שהן מוגדרות ב-NEWS_SOURCES_CONFIG)
# לאובייקטי הפונקציות המיובאות בפועל.
# זה מאפשר קריאה דינמית לפונקציות.
AVAILABLE_SCRAPER_FUNCTIONS = {
    "get_yahoo_news": get_yahoo_news,
    "get_investors_news": get_investors_news,
    "fetch_marketwatch_titles": fetch_marketwatch_titles,
    "get_cnbc_titles": get_cnbc_titles,
    # הוסף כאן עוד מיפויים אם הוספת scrapers חדשים
}

def fetch_all_news(symbol: str, max_headlines_total: int = 50) -> list[tuple[str, str]]:
    """
    שולף כותרות חדשות מכל המקורות המוגדרים והמאופשרים עבור סמל נתון.
    מקבץ את כל הכותרות לרשימה אחת של (כותרת, שם_מקור), תוך מניעת כפילויות.
    max_headlines_total: מגבלה על סך כל הכותרות שיוחזרו מכל המקורות יחד.
    """
    all_collected_headlines = []
    # שימוש ב-set לאחסון כותרות שכבר נראו (ב-lowercase) למניעת כפילויות באופן לא רגיש לרישיות.
    # זה יעיל יותר מבדיקת 'in' ברשימה גדולה.
    seen_titles_lower = set() 

    logger.info(f"Starting news aggregation for symbol: '{symbol}'")

    # לולאה על המקורות המוגדרים ב-settings.py
    for source_key, source_config in NEWS_SOURCES_CONFIG.items():
        # בדוק אם המקור מאופשר
        if not source_config.get("enabled", False): # אם 'enabled' לא קיים, נניח False
            logger.info(f"Source '{source_key}' is disabled. Skipping.")
            continue

        # קבל את שם פונקציית ה-scraper מההגדרות
        scraper_function_name = source_config.get("scraper_function_name")
        if not scraper_function_name:
            logger.warning(f"No 'scraper_function_name' defined for source: '{source_key}'. Skipping.")
            continue

        # קבל את אובייקט הפונקציה מהמילון שלנו
        scraper_function = AVAILABLE_SCRAPER_FUNCTIONS.get(scraper_function_name)
        if not scraper_function:
            logger.error(f"Scraper function '{scraper_function_name}' for source '{source_key}' not found in AVAILABLE_SCRAPER_FUNCTIONS. Skipping.")
            continue

        logger.debug(f"Attempting to fetch news from '{source_key}' for '{symbol}' using function '{scraper_function_name}'...")
        
        # הכנת ארגומנטים לפונקציית ה-scraper
        # כל scraper מצפה ל-symbol, ואז לפרמטר ספציפי של URL/תבנית.
        # אחרים עשויים לצפות לפרמטרים נוספים.
        scraper_args = [symbol]
        if "rss_url_template" in source_config:
            scraper_args.append(source_config["rss_url_template"])
        elif "base_url_template" in source_config: # עבור MarketWatch
            scraper_args.append(source_config["base_url_template"])
        # אפשר להוסיף כאן עוד תנאים אם ל-scrapers אחרים יש פרמטרים ייחודיים מההגדרות

        try:
            # קריאה לפונקציית ה-scraper המתאימה עם הארגומנטים שהוכנו
            # כל פונקציית scraper אמורה להחזיר list[tuple[str, str]]
            source_specific_headlines = scraper_function(*scraper_args) 

            if not source_specific_headlines:
                logger.info(f"No headlines returned from '{source_key}' for '{symbol}'.")
                continue

            headlines_added_from_this_source = 0
            # הגבלת מספר הכותרות הנלקחות מכל מקור בודד
            for title, reported_source_name in source_specific_headlines[:DEFAULT_MAX_HEADLINES_PER_SOURCE]:
                # ודא שהכותרת עומדת באורך מינימלי ושלא ראינו אותה כבר (לא רגיש לרישיות)
                cleaned_title = title.strip() # ניקוי בסיסי נוסף אם צריך
                title_lower = cleaned_title.lower()

                if cleaned_title and len(cleaned_title) >= MIN_HEADLINE_LENGTH and title_lower not in seen_titles_lower:
                    # השתמש בשם המקור מההגדרות (source_key) כדי להבטיח עקביות,
                    # אלא אם כן יש סיבה טובה להשתמש ב-reported_source_name מה-scraper.
                    all_collected_headlines.append((cleaned_title, source_key))
                    seen_titles_lower.add(title_lower)
                    headlines_added_from_this_source += 1
                elif title_lower in seen_titles_lower:
                    logger.debug(f"Duplicate title (case-insensitive) skipped from '{source_key}': '{cleaned_title}'")
                elif cleaned_title: # אם הכותרת קצרה מדי
                     logger.debug(f"Short title skipped from '{source_key}': '{cleaned_title}' (Length: {len(cleaned_title)})")


            if headlines_added_from_this_source > 0:
                logger.info(f"Added {headlines_added_from_this_source} unique headlines from '{source_key}' for '{symbol}'.")
            else:
                logger.info(f"No new unique headlines added from '{source_key}' for '{symbol}'.")
        
        except TypeError as te: # יכול לקרות אם מספר/סוג הארגומנטים לפונקציה לא נכון
            logger.error(f"TypeError calling scraper function '{scraper_function_name}' for '{source_key}': {te}. Check arguments and function signature.", exc_info=True)
        except Exception as e:
            logger.error(f"Error processing source '{source_key}' for '{symbol}': {e}", exc_info=True)

        # בדיקה אם הגענו למגבלה הכוללת של הכותרות
        if len(all_collected_headlines) >= max_headlines_total:
            logger.info(f"Reached total headline limit of {max_headlines_total} for '{symbol}'. Stopping further fetching.")
            break # יציאה מהלולאה על המקורות

    if all_collected_headlines:
        logger.info(f"Total unique headlines aggregated for '{symbol}' across all sources: {len(all_collected_headlines)} (capped at {max_headlines_total}).")
        # הדפסה של כל הכותרות ל-DEBUG יכולה להיות מאוד ארוכה.
        # for h_idx, (h_title, h_source) in enumerate(all_collected_headlines):
        #     logger.debug(f"  Aggregated {h_idx+1}. [{h_source}] {h_title}")
    else:
        logger.info(f"No headlines aggregated for '{symbol}' across all sources.")

    return all_collected_headlines[:max_headlines_total] # ודא שלא מחזירים יותר מהמגבלה הכוללת


if __name__ == "__main__":
    # --- בלוק לבדיקה מקומית של ה-aggregator ---
    import logging

    # הגדרת לוגר ברמת DEBUG לבדיקה. זה ידרוס את ברירת המחדל (INFO) אם היא מוגדרת כך.
    test_logger = setup_logger(__name__, level=logging.DEBUG)

    test_symbols_agg = ["AAPL", "TSLA"] # סמלים לבדיקה
    
    # ודא שכל פונקציות ה-scraper מיובאות כראוי וש-settings.py מעודכן
    # (במיוחד NEWS_SOURCES_CONFIG ו-AVAILABLE_SCRAPER_FUNCTIONS כאן למעלה)

    for sym_to_test in test_symbols_agg:
        test_logger.info(f"--- Testing news aggregator for symbol: {sym_to_test} ---")
        
        # קריאה לפונקציה הראשית עם מגבלה כוללת נמוכה יותר לבדיקה
        aggregated_headlines_list = fetch_all_news(sym_to_test, max_headlines_total=20)
        
        if aggregated_headlines_list:
            test_logger.info(f"Aggregated {len(aggregated_headlines_list)} headlines for {sym_to_test}:")
            for index, (headline_text, source_name_text) in enumerate(aggregated_headlines_list):
                test_logger.info(f"  {index+1}. [{source_name_text}] {headline_text}")
        else:
            test_logger.info(f"No headlines were aggregated for {sym_to_test}.")
        test_logger.info(f"--- Finished news aggregator test for {sym_to_test} ---")
