# news_scraper.py
# import feedparser # לא ישירות בשימוש כאן, אלא ב-scrapers הספציפיים
from settings import NEWS_SOURCES # ← ודא שהוא מעודכן
from cnbc_scraper import get_cnbc_titles # נשאר כפי שהיה
# יבוא של ה-scrapers החדשים/המשופרים
from yahoo_scraper import get_yahoo_news
from investors_scraper import get_investors_news
from marketwatch_scraper import fetch_marketwatch_titles
# אם יש לך עוד, יבא אותם

from settings import setup_logger

logger = setup_logger(__name__)

# מפה של שמות מקורות לפונקציות ה-scraper שלהם
# זה יכול להיות מוגדר גם ב-settings.py
SCRAPER_FUNCTIONS = {
    "Yahoo Finance": get_yahoo_news,
    "Investors.com": get_investors_news,
    "MarketWatch": fetch_marketwatch_titles,
    "CNBC": get_cnbc_titles, # CNBC מטופל באופן מיוחד למטה
    # הוסף עוד מקורות ופונקציות כאן
}


def fetch_all_news_titles(symbol: str, max_headlines_per_source: int = 10) -> list[tuple[str, str]]:
    """
    שולף כותרות חדשות מכל המקורות המוגדרים עבור סמל נתון.
    מקבץ את כל הכותרות לרשימה אחת של (כותרת, שם_מקור).
    """
    all_headlines = []
    seen_titles = set() # למניעת כפילויות בין כל המקורות

    logger.info(f"Starting news fetch for symbol: {symbol}")

    for source_name, source_info in NEWS_SOURCES.items():
        if not source_info.get("enabled", True): # ברירת מחדל ל-enabled אם לא צוין
            logger.info(f"Source '{source_name}' is disabled. Skipping.")
            continue

        scraper_function = SCRAPER_FUNCTIONS.get(source_name)
        
        if not scraper_function:
            logger.warning(f"No scraper function defined for source: '{source_name}'. Skipping.")
            continue

        logger.debug(f"Fetching news from '{source_name}' for {symbol}...")
        try:
            # קריאה לפונקציית ה-scraper המתאימה
            # הפונקציות אמורות להחזיר list[tuple[str, str]]
            source_headlines = scraper_function(symbol) 

            processed_count = 0
            for title, src_name_from_scraper in source_headlines:
                # ודא ששם המקור מה-scraper תואם, או השתמש ב-source_name מהלולאה
                # למקרה ש-scraper לא מחזיר שם מקור, או שרוצים לדרוס
                actual_source_name = src_name_from_scraper if src_name_from_scraper else source_name

                # בודק אורך מינימלי (אפשר להסיר אם כל scraper כבר עושה זאת)
                # וכמובן בדיקת כפילויות
                if title and len(title) >= 10 and title.lower() not in seen_titles:
                    all_headlines.append((title, actual_source_name))
                    seen_titles.add(title.lower()) # שמירת כותרות ב-lowercase למניעת כפילויות רישיות
                    processed_count += 1
                    if processed_count >= max_headlines_per_source:
                        logger.debug(f"Reached max headlines ({max_headlines_per_source}) for {actual_source_name}.")
                        break 
            
            logger.info(f"Fetched {processed_count} unique headlines from '{source_name}' for {symbol}.")

        except Exception as e:
            logger.error(f"Error processing source '{source_name}' for {symbol}: {e}", exc_info=True)

    if all_headlines:
        logger.info(f"Total unique headlines found for {symbol} across all sources: {len(all_headlines)}")
        # ההדפסה של כל הכותרות יכולה להיות מאוד ורבלית, אולי רק ל-DEBUG
        # for h_title, h_source in all_headlines:
        #     logger.debug(f"- [{h_source}] {h_title}")
    else:
        logger.info(f"No headlines found for {symbol} across all sources.")

    return all_headlines
