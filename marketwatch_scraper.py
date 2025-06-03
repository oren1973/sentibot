# marketwatch_scraper.py
import requests
from bs4 import BeautifulSoup
# from urllib.parse import quote # לא בשימוש כרגע
# from sentiment import clean_text # הנחה שזו פונקציה שלך. אם לא, צריך להגדיר אותה או להסיר.
from settings import setup_logger

logger = setup_logger(__name__)

# פונקציית clean_text לדוגמה, אם היא לא מיובאת ממקום אחר
# עליך להתאים אותה לצרכים שלך.
def clean_text(text: str) -> str:
    # הסרת רווחים עודפים בתחילת ובסוף הטקסט
    cleaned = text.strip()
    # אפשר להוסיף כאן עוד לוגיקת ניקוי, למשל:
    # import re
    # cleaned = re.sub(r'\s+', ' ', cleaned) # החלפת רצפי רווחים ברווח בודד
    return cleaned


def fetch_marketwatch_titles(symbol: str) -> list[tuple[str, str]]:
    """
    שולף כותרות מ-MarketWatch עבור סמל נתון.
    מחזיר רשימת tuples של (כותרת, מקור).
    """
    source_name = "MarketWatch"
    headlines_data = []
    base_url = f"https://www.marketwatch.com/investing/stock/{symbol.lower()}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    logger.info(f"Fetching news for {symbol} from {source_name} via scraping...")

    try:
        response = requests.get(base_url, headers=headers, timeout=15) # הגדלתי מעט את ה-timeout
        response.raise_for_status()  # יעלה חריגה עבור סטטוסים 4xx/5xx

        soup = BeautifulSoup(response.text, "html.parser")
        # שים לב: סלקטורים יכולים להישבר אם האתר משתנה.
        # כדאי לבדוק אותם מדי פעם.
        # שילבתי את שני הסלקטורים המקוריים. אפשר לשפר את זה אם יש דרך טובה יותר.
        selected_elements = soup.select("h3.article__headline a, h4.article__headline a, div.article__content > a > h3.article__title")
        # עוד אפשרות לסלקטור יותר כללי (אך עשוי לתפוס יותר מדי):
        # selected_elements = soup.find_all(['h3', 'h4'], class_=lambda x: x and 'headline' in x)
        
        titles_found = 0
        for h_element in selected_elements:
            title_text = h_element.get_text(strip=True)
            if title_text:
                cleaned_title = clean_text(title_text)
                if cleaned_title and len(cleaned_title) >= 15: # אורך מינימלי מעט יותר ארוך ל-scraping
                    headlines_data.append((cleaned_title, source_name))
                    titles_found += 1
                    if titles_found >= 10: # הגבלת מספר הכותרות
                        break 
                elif cleaned_title:
                     logger.debug(f"Skipping short title from {source_name} for {symbol}: '{cleaned_title}'")
            
        logger.info(f"Found {len(headlines_data)} headlines for {symbol} from {source_name}.")

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while fetching from {source_name} for {symbol}: {http_err} (URL: {base_url})")
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error occurred while fetching from {source_name} for {symbol}: {conn_err} (URL: {base_url})")
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error occurred while fetching from {source_name} for {symbol}: {timeout_err} (URL: {base_url})")
    except requests.exceptions.RequestException as req_err: # שגיאת requests כללית יותר
        logger.error(f"An error occurred during requests to {source_name} for {symbol}: {req_err} (URL: {base_url})", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred in {source_name} scraper for {symbol}: {e}", exc_info=True)
        
    return headlines_data[:10] # ודא שלא מחזירים יותר מ-10
