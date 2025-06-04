# marketwatch_scraper.py
import requests
from bs4 import BeautifulSoup
from settings import setup_logger, MIN_HEADLINE_LENGTH # ייבוא מהקובץ settings.py

# אתחול לוגר ספציפי למודול זה
logger = setup_logger(__name__) # השם יהיה "marketwatch_scraper"

def _clean_text(text: str) -> str:
    """
    פונקציית עזר פנימית לניקוי טקסט כותרות.
    מסירה רווחים עודפים בתחילת ובסוף הטקסט.
    אפשר להוסיף כאן עוד לוגיקת ניקוי אם צריך.
    """
    if not text:
        return ""
    cleaned = text.strip()
    # דוגמה לניקוי נוסף: החלפת מספר רווחים רצופים ברווח בודד
    # import re
    # cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned

def fetch_marketwatch_titles(symbol: str, base_url_template: str) -> list[tuple[str, str]]:
    """
    שולף כותרות מ-MarketWatch עבור סמל נתון באמצעות web scraping.
    מקבל סימבול ותבנית URL בסיסי.
    מחזיר רשימת tuples של (כותרת, מקור).
    """
    source_name = "MarketWatch"
    headlines_data = []
    
    if not base_url_template:
        logger.error(f"Base URL template not provided for {source_name}. Cannot fetch news for {symbol}.")
        return []

    # MarketWatch מצפה לסימול באותיות קטנות ב-URL
    target_url = base_url_template.replace("{symbol_lower}", symbol.lower())
    
    # User-Agent חשוב כדי שהאתר לא יחסום אותנו כבוט גנרי
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    logger.info(f"Fetching news for '{symbol}' from {source_name} via scraping URL: {target_url}")

    try:
        response = requests.get(target_url, headers=headers, timeout=15) # Timeout של 15 שניות
        response.raise_for_status()  # יעלה חריגה עבור סטטוסים 4xx/5xx (כמו 404, 500)

        soup = BeautifulSoup(response.text, "html.parser")
        
        # --- בחירת אלמנטים עם כותרות ---
        # הסלקטורים האלה עלולים להישבר אם מבנה האתר ישתנה.
        # כדאי לבדוק אותם מדי פעם ולוודא שהם עדיין תופסים את הכותרות הנכונות.
        # אפשר להשתמש בכלי פיתוח של הדפדפן (Inspect Element) כדי למצוא סלקטורים מתאימים.
        # הסלקטורים מהקוד המקורי שלך: "h3.article__headline, h4.article__headline"
        # ננסה סלקטורים מעט יותר ספציפיים שעשויים להיות יותר יציבים:
        # 1. כותרות בתוך רשימת כתבות رئيسית (לרוב עם קישור)
        # 2. כותרות משנה בתוך גוף כתבה (פחות נפוץ לכותרות ראשיות)
        # חיפוש קישורים (<a>) שבתוכם יש כותרת (<h3> או <h4>) עם class שכולל 'headline' או 'title'
        potential_headlines_elements = soup.select('a h3[class*="headline"], a h4[class*="headline"], a h3[class*="title"], a h4[class*="title"]')
        
        if not potential_headlines_elements:
            # נסיון עם סלקטורים יותר רחבים אם הראשונים לא מצאו כלום
            logger.debug(f"Initial selectors found no elements for '{symbol}' on {source_name}. Trying broader selectors.")
            potential_headlines_elements = soup.find_all(['h3', 'h4'], class_=lambda c: c and ('headline' in c or 'title' in c))

        if not potential_headlines_elements:
            logger.info(f"No headline elements found on {source_name} page for '{symbol}'. (URL: {target_url})")
            return []
            
        logger.debug(f"Found {len(potential_headlines_elements)} potential headline elements for '{symbol}' on {source_name}.")

        titles_added_count = 0
        for element in potential_headlines_elements:
            raw_title_text = element.get_text(strip=False) # strip=False כדי שנוכל לנקות בעצמנו
            cleaned_title = _clean_text(raw_title_text)
            
            if cleaned_title and len(cleaned_title) >= MIN_HEADLINE_LENGTH:
                headlines_data.append((cleaned_title, source_name))
                titles_added_count += 1
                if titles_added_count >= 10: # הגבלת מספר הכותרות (כמו בקוד המקורי שלך)
                    logger.debug(f"Reached limit of {titles_added_count} headlines for '{symbol}' from {source_name}.")
                    break 
            elif cleaned_title:
                logger.debug(f"Skipping short/empty cleaned title from {source_name} for '{symbol}': '{cleaned_title}' (Original: '{raw_title_text[:50]}...')")
        
        logger.info(f"Successfully extracted {len(headlines_data)} headlines for '{symbol}' from {source_name}.")

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while fetching from {source_name} for '{symbol}': {http_err} (URL: {target_url})")
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error occurred while fetching from {source_name} for '{symbol}': {conn_err} (URL: {target_url})")
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error occurred while fetching from {source_name} for '{symbol}': {timeout_err} (URL: {target_url})")
    except requests.exceptions.RequestException as req_err: # שגיאת requests כללית יותר
        logger.error(f"An error occurred during requests to {source_name} for '{symbol}': {req_err} (URL: {target_url})", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred in {source_name} scraper for '{symbol}': {e} (URL: {target_url})", exc_info=True)
        
    return headlines_data # הפונקציה כבר דואגת להגבלה ל-10 כותרות מקסימום בלולאה

if __name__ == "__main__":
    # --- בלוק לבדיקה מקומית של ה-scraper ---
    import logging

    test_logger = setup_logger(__name__, level=logging.DEBUG)

    # קבלת תבנית ה-URL מ-settings.py
    # from settings import NEWS_SOURCES_CONFIG
    # temp_base_url_template = NEWS_SOURCES_CONFIG.get("MarketWatch", {}).get("base_url_template")
    
    # או פשוט השתמש ב-URL ישירות לבדיקה:
    temp_base_url_template_for_test = "https://www.marketwatch.com/investing/stock/{symbol_lower}"
    
    if temp_base_url_template_for_test:
        test_symbols = ["AAPL", "NVDA", "NONEXISTENT"]
        for sym in test_symbols:
            test_logger.info(f"--- Testing {sym} for MarketWatch ---")
            retrieved_headlines = fetch_marketwatch_titles(sym, temp_base_url_template_for_test)
            if retrieved_headlines:
                test_logger.debug(f"Retrieved {len(retrieved_headlines)} headlines for {sym}:")
                for i, (h_title, h_source) in enumerate(retrieved_headlines):
                    test_logger.debug(f"  {i+1}. [{h_source}] {h_title}")
            else:
                test_logger.debug(f"No headlines retrieved for {sym}.")
            test_logger.info(f"--- Finished testing {sym} ---")
    else:
        test_logger.error("Could not get base URL template for MarketWatch for testing.")
